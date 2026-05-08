#!/usr/bin/env python3
import argparse
import io
from pathlib import Path

import fitz
from PIL import Image


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Rasterize each PDF page and recompress as JPEG images.",
    )
    parser.add_argument(
        "-d",
        "--dpi",
        type=int,
        default=300,
        help="Rasterization resolution in DPI (default: 300).",
    )
    parser.add_argument(
        "-q",
        "--quality",
        type=int,
        default=90,
        help="JPEG quality (0-100, higher is better).",
    )
    parser.add_argument(
        "--glob",
        help="Glob pattern to match PDFs (e.g., 'docs/*.pdf').",
    )
    parser.add_argument("input_pdf", nargs="?", help="Path to the input PDF.")
    parser.add_argument(
        "-o",
        "--output",
        help="Optional output PDF path (default: <input>_compressed.pdf).",
    )
    parser.add_argument(
        "--inplace",
        action="store_true",
        help="Overwrite the input PDF in place.",
    )
    return parser.parse_args()


def pixmap_to_rgb(pix: fitz.Pixmap) -> Image.Image:
    if pix.n == 1:
        image = Image.frombytes("L", (pix.width, pix.height), pix.samples)
        return image.convert("RGB")
    if pix.n == 3:
        return Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    if pix.n == 4:
        image = Image.frombytes("CMYK", (pix.width, pix.height), pix.samples)
        return image.convert("RGB")
    image = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    return image


def compress_pdf(input_path: Path, output_path: Path, dpi: int, quality: int) -> None:
    if quality < 0 or quality > 100:
        raise ValueError("--quality must be between 0 and 100")
    if dpi <= 0:
        raise ValueError("--dpi must be a positive integer")

    zoom = dpi / 72.0
    matrix = fitz.Matrix(zoom, zoom)

    with fitz.open(input_path) as source:
        output = fitz.open()
        for page in source:
            pix = page.get_pixmap(matrix=matrix, alpha=False)
            image = pixmap_to_rgb(pix)
            buffer = io.BytesIO()
            image.save(
                buffer,
                format="JPEG",
                quality=quality,
                optimize=True,
                progressive=True,
            )
            buffer.seek(0)
            rect = page.rect
            out_page = output.new_page(width=rect.width, height=rect.height)
            out_page.insert_image(rect, stream=buffer.getvalue())

        output.save(output_path, deflate=True, garbage=4)
        output.close()


def main() -> None:
    args = parse_args()
    if args.output and args.inplace:
        raise SystemExit("Use either --output or --inplace, not both")

    if args.glob and args.input_pdf:
        raise SystemExit("Use either --glob or an input PDF, not both")
    if not args.glob and not args.input_pdf:
        raise SystemExit("Provide an input PDF or use --glob")

    if args.glob:
        pattern = args.glob
        matches = sorted(Path().glob(pattern))
        pdfs = [path for path in matches if path.suffix.lower() == ".pdf"]
        if not pdfs:
            raise SystemExit(f"No PDF files matched glob: {pattern}")
        output_dir = None
        if args.output:
            output_dir = Path(args.output).expanduser().resolve()
            if output_dir.exists() and output_dir.is_file():
                raise SystemExit("--output must be a directory when used with --glob")
            output_dir.mkdir(parents=True, exist_ok=True)
        for input_path in pdfs:
            input_path = input_path.expanduser().resolve()
            if args.inplace:
                output_path = input_path
            elif output_dir:
                output_path = output_dir / input_path.name
            else:
                output_path = input_path.with_name(
                    f"{input_path.stem}_compressed.pdf"
                )
            print(
                f"Compressing {input_path.name} -> {output_path.name} | "
                f"dpi={args.dpi} quality={args.quality}"
            )
            compress_pdf(input_path, output_path, args.dpi, args.quality)
        print(f"Processed {len(pdfs)} file(s)")
        return

    input_path = Path(args.input_pdf).expanduser().resolve()
    if not input_path.exists():
        raise SystemExit(f"Input file does not exist: {input_path}")
    if input_path.suffix.lower() != ".pdf":
        raise SystemExit("Input file must be a PDF")

    if args.inplace:
        output_path = input_path
    elif args.output:
        output_path = Path(args.output).expanduser().resolve()
    else:
        output_path = input_path.with_name(f"{input_path.stem}_compressed.pdf")

    print(
        f"Compressing {input_path.name} -> {output_path.name} | "
        f"dpi={args.dpi} quality={args.quality}"
    )
    compress_pdf(input_path, output_path, args.dpi, args.quality)
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
