from io import BytesIO
from statistics import mean

import cv2
import numpy as np
import pytesseract
from PIL import Image, ImageOps, UnidentifiedImageError
from pytesseract import Output

from app.services.parsers.base import BaseParser, ParsedDocument


class ImageParser(BaseParser):
    """Extract image text using Tesseract with multiple OCR passes."""

    UPSCALE_FACTOR = 3
    PAGE_OCR_CONFIG = "--oem 3 --psm 11"
    ROW_OCR_CONFIG = "--oem 3 --psm 7 -c preserve_interword_spaces=1"

    def parse(
        self,
        content: bytes,
        filename: str,
        content_type: str | None = None,
    ) -> ParsedDocument:
        try:
            with Image.open(BytesIO(content)) as source:
                image = ImageOps.exif_transpose(source).convert("RGB")
                image.load()
                original_width, original_height = image.size

        except (UnidentifiedImageError, OSError) as exc:
            raise ValueError(f"Could not read image '{filename}'") from exc

        # Grayscale + 3x enlargement was the best baseline in testing.
        gray = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2GRAY)
        processed = cv2.resize(
            gray,
            None,
            fx=self.UPSCALE_FACTOR,
            fy=self.UPSCALE_FACTOR,
            interpolation=cv2.INTER_CUBIC,
        )

        # Primary full-page OCR pass.
        page_data = pytesseract.image_to_data(
            processed,
            config=self.PAGE_OCR_CONFIG,
            output_type=Output.DICT,
        )
        extracted_text = pytesseract.image_to_string(
            processed,
            config=self.PAGE_OCR_CONFIG,
        ).strip()

        words = self._extract_words(page_data)
        ocr_rows = self._consolidate_words_into_rows(words)
        consolidated_text = "\n".join(ocr_rows)

        # Run a targeted OCR pass on likely item-description rows.
        # This supplements the full-page result without replacing it.
        item_row_results = self._extract_item_rows(processed, words)

        if not extracted_text:
            raise ValueError(f"No text could be extracted from image '{filename}'")

        confidences = [word["confidence"] for word in words if word["confidence"] >= 0]

        return ParsedDocument(
            content=consolidated_text or extracted_text,
            metadata={
                "filename": filename,
                "content_type": content_type,
                "image_format": image.format if hasattr(image, "format") else None,
                "width": original_width,
                "height": original_height,
                "ocr": True,
                "ocr_engine": "tesseract",
                "ocr_config": self.PAGE_OCR_CONFIG,
                "ocr_preprocessing": "grayscale",
                "ocr_scale": self.UPSCALE_FACTOR,
                "ocr_word_count": len(words),
                "ocr_mean_confidence": (
                    round(mean(confidences), 2) if confidences else None
                ),
                "ocr_words": words,
                "ocr_rows": ocr_rows,
                "ocr_item_row_candidates": item_row_results,
            },
        )

    @staticmethod
    def _consolidate_words_into_rows(
        words: list[dict],
        y_tolerance: int = 18,
    ) -> list[str]:
        """Group OCR words into visual rows and order them left to right."""
        if not words:
            return []

        sorted_words = sorted(
            words,
            key=lambda word: word["top"] + word["height"] / 2,
        )

        rows = []

        for word in sorted_words:
            center_y = word["top"] + word["height"] / 2

            # Match the closest existing row within the tolerance.
            matching_row = None
            smallest_distance = float("inf")

            for row in rows:
                distance = abs(center_y - row["center_y"])

                if distance <= y_tolerance and distance < smallest_distance:
                    matching_row = row
                    smallest_distance = distance

            if matching_row is None:
                rows.append(
                    {
                        "center_y": center_y,
                        "words": [word],
                    }
                )
            else:
                matching_row["words"].append(word)
                matching_row["center_y"] = sum(
                    item["top"] + item["height"] / 2 for item in matching_row["words"]
                ) / len(matching_row["words"])

        # Sort rows vertically, then words horizontally.
        rows.sort(key=lambda row: row["center_y"])

        consolidated_rows = []

        for row in rows:
            ordered_words = sorted(
                row["words"],
                key=lambda word: word["left"],
            )
            line = " ".join(word["text"] for word in ordered_words).strip()

            if line:
                consolidated_rows.append(line)

        return consolidated_rows

    @staticmethod
    def _extract_words(data: dict) -> list[dict]:
        """Extract word text, confidence, and bounding boxes."""
        words = []

        for index, raw_text in enumerate(data["text"]):
            text = raw_text.strip()
            if not text:
                continue

            try:
                confidence = float(data["conf"][index])
            except TypeError, ValueError:
                confidence = -1.0

            words.append(
                {
                    "text": text,
                    "confidence": round(confidence, 2),
                    "left": int(data["left"][index]),
                    "top": int(data["top"][index]),
                    "width": int(data["width"][index]),
                    "height": int(data["height"][index]),
                    "block_num": int(data["block_num"][index]),
                    "par_num": int(data["par_num"][index]),
                    "line_num": int(data["line_num"][index]),
                }
            )

        return words

    def _extract_item_rows(
        self,
        image: np.ndarray,
        words: list[dict],
    ) -> list[dict]:
        """Re-OCR likely item-description lines as individual rows."""
        if not words:
            return []

        image_height, image_width = image.shape[:2]

        # Group OCR words by their Tesseract line identifiers.
        lines: dict[tuple[int, int, int], list[dict]] = {}
        for word in words:
            key = (
                word["block_num"],
                word["par_num"],
                word["line_num"],
            )
            lines.setdefault(key, []).append(word)

        results = []

        for line_words in lines.values():
            line_text = " ".join(word["text"] for word in line_words)
            normalized = line_text.lower()

            # Restrict this pass to likely dish-description rows.
            if not any(
                marker in normalized for marker in ("paneer", "tortas", "torta")
            ):
                continue

            left = min(word["left"] for word in line_words)
            top = min(word["top"] for word in line_words)
            right = max(word["left"] + word["width"] for word in line_words)
            bottom = max(word["top"] + word["height"] for word in line_words)

            # Add padding so ascenders, descenders, and nearby digits
            # are not clipped.
            pad_x = 12
            pad_y = 10
            x1 = max(0, left - pad_x)
            y1 = max(0, top - pad_y)
            x2 = min(image_width, right + pad_x)
            y2 = min(image_height, bottom + pad_y)

            crop = image[y1:y2, x1:x2]
            if crop.size == 0:
                continue

            row_text = pytesseract.image_to_string(
                crop,
                config=self.ROW_OCR_CONFIG,
            ).strip()

            row_data = pytesseract.image_to_data(
                crop,
                config=self.ROW_OCR_CONFIG,
                output_type=Output.DICT,
            )
            row_words = self._extract_words(row_data)
            row_confidences = [
                word["confidence"] for word in row_words if word["confidence"] >= 0
            ]

            results.append(
                {
                    "original_line": line_text,
                    "row_ocr_text": row_text,
                    "mean_confidence": (
                        round(mean(row_confidences), 2) if row_confidences else None
                    ),
                    "crop": {
                        "left": x1,
                        "top": y1,
                        "width": x2 - x1,
                        "height": y2 - y1,
                    },
                }
            )

        return results
