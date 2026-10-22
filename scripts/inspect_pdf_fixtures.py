from pathlib import Path

import pymupdf

from app.services.parsers.pdf.analyzer import PdfAnalyzer

ROOT_DIR = Path(__file__).resolve().parents[1]
FIXTURE_DIR = ROOT_DIR / "tests" / "fixtures" / "pdf" / "sample-files"


def inspect_pdf(path: Path) -> None:
    relative_path = path.relative_to(FIXTURE_DIR)

    try:
        document = pymupdf.open(path)

        if document.is_encrypted:
            print(f"{relative_path} | ENCRYPTED")
            document.close()
            return

        page_count = len(document)

        text_pages = 0
        image_pages = 0
        total_images = 0

        for page in document:
            text = page.get_text("text").strip()
            images = page.get_image_info()

            if text:
                text_pages += 1

            if images:
                image_pages += 1

            total_images += len(images)

        document.close()

        analysis = PdfAnalyzer.analyze(path.read_bytes())

        print(
            f"{relative_path}"
            f" | pages={page_count}"
            f" | text_pages={text_pages}"
            f" | image_pages={image_pages}"
            f" | images={total_images}"
            f" | detected={analysis.pdf_type.value}"
            f" | ocr_pages={analysis.metadata['ocr_page_count']}"
        )

    except Exception as exc:  # noqa: BLE001
        print(f"{relative_path} | ERROR={type(exc).__name__}: {exc}")


def main() -> None:
    pdf_files = sorted(FIXTURE_DIR.rglob("*.pdf"))

    print(f"Fixture directory: {FIXTURE_DIR}")
    print(f"PDF files found: {len(pdf_files)}")
    print()

    for pdf_file in pdf_files:
        inspect_pdf(pdf_file)


if __name__ == "__main__":
    main()
