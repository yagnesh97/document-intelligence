from itertools import pairwise

import pymupdf

from app.services.parsers.pdf.base import (
    PdfAnalysis,
    PdfPageAnalysis,
    PdfType,
)


class PdfAnalyzer:
    """
    Analyze PDF pages and determine which pages require OCR.
    """

    MIN_NATIVE_TEXT_LENGTH = 80
    HIGH_IMAGE_COVERAGE = 0.50

    @classmethod
    def analyze(cls, content: bytes) -> PdfAnalysis:
        document = pymupdf.open(
            stream=content,
            filetype="pdf",
        )

        try:
            pages = [
                cls._analyze_page(
                    page=page,
                    page_number=page_number,
                )
                for page_number, page in enumerate(
                    document,
                    start=1,
                )
            ]

            pdf_type = cls._detect_pdf_type(pages)

            return PdfAnalysis(
                pdf_type=pdf_type,
                pages=pages,
                metadata={
                    "page_count": len(pages),
                    "ocr_page_count": sum(page.requires_ocr for page in pages),
                },
            )
        finally:
            document.close()

    @classmethod
    def _analyze_page(
        cls,
        page: pymupdf.Page,
        page_number: int,
    ) -> PdfPageAnalysis:
        text = page.get_text("text").strip()
        image_infos = page.get_image_info()

        image_count = len(image_infos)
        image_coverage = cls._calculate_image_coverage(
            page=page,
            image_infos=image_infos,
        )

        has_text = bool(text)

        requires_ocr = cls._requires_ocr(
            has_text=has_text,
            text_length=len(text),
            image_count=image_count,
            image_coverage=image_coverage,
        )

        return PdfPageAnalysis(
            page_number=page_number,
            has_text=has_text,
            text_length=len(text),
            image_count=image_count,
            image_coverage=image_coverage,
            requires_ocr=requires_ocr,
        )

    @classmethod
    def _requires_ocr(
        cls,
        has_text: bool,
        text_length: int,
        image_count: int,
        image_coverage: float,
    ) -> bool:
        if image_count == 0:
            return False

        if not has_text:
            return True

        return (
            text_length < cls.MIN_NATIVE_TEXT_LENGTH
            and image_coverage >= cls.HIGH_IMAGE_COVERAGE
        )

    @staticmethod
    def _calculate_image_coverage(
        page: pymupdf.Page,
        image_infos: list[dict],
    ) -> float:
        """Calculate the proportion of the page covered by images."""

        page_area = page.rect.get_area()

        if page_area <= 0 or not image_infos:
            return 0.0

        image_rects: list[pymupdf.Rect] = []

        for image_info in image_infos:
            bbox = image_info.get("bbox")

            if not bbox:
                continue

            image_rect = pymupdf.Rect(bbox)

            if not image_rect.intersects(page.rect):
                continue

            image_rect &= page.rect

            if image_rect.is_empty:
                continue

            image_rects.append(image_rect)

        if not image_rects:
            return 0.0

        covered_area = PdfAnalyzer._calculate_union_area(
            image_rects,
        )

        return min(covered_area / page_area, 1.0)

    @staticmethod
    def _calculate_union_area(
        rectangles: list[pymupdf.Rect],
    ) -> float:
        """Calculate rectangle union area without double-counting."""

        if not rectangles:
            return 0.0

        x_coordinates = sorted(
            {
                coordinate
                for rectangle in rectangles
                for coordinate in (
                    rectangle.x0,
                    rectangle.x1,
                )
            }
        )

        total_area = 0.0

        for x_start, x_end in pairwise(x_coordinates):
            if x_end <= x_start:
                continue

            active_intervals: list[tuple[float, float]] = []

            for rectangle in rectangles:
                if rectangle.x0 < x_end and rectangle.x1 > x_start:
                    active_intervals.append((rectangle.y0, rectangle.y1))

            if not active_intervals:
                continue

            active_intervals.sort()

            merged_height = 0.0
            current_start, current_end = active_intervals[0]

            for start, end in active_intervals[1:]:
                if start <= current_end:
                    current_end = max(current_end, end)
                else:
                    merged_height += current_end - current_start
                    current_start, current_end = start, end

            merged_height += current_end - current_start
            total_area += (x_end - x_start) * merged_height

        return total_area

    @staticmethod
    def _detect_pdf_type(
        pages: list[PdfPageAnalysis],
    ) -> PdfType:
        if not pages:
            return PdfType.EMPTY

        ocr_pages = sum(page.requires_ocr for page in pages)

        if ocr_pages == len(pages):
            return PdfType.IMAGE

        if ocr_pages > 0:
            return PdfType.HYBRID

        if any(page.has_text for page in pages):
            return PdfType.TEXT

        return PdfType.EMPTY
