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
        "input_pdfs",
        nargs="+",
        help="One or more input PDF paths.",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Optional output PDF path or directory.",
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

    input_paths = [Path(path).expanduser().resolve() for path in args.input_pdfs]
    for input_path in input_paths:
        if not input_path.exists():
            raise SystemExit(f"Input file does not exist: {input_path}")
        if input_path.suffix.lower() != ".pdf":
            raise SystemExit(f"Input file must be a PDF: {input_path}")

    output_dir = None
    if args.output:
        output_path_value = Path(args.output).expanduser().resolve()
        if len(input_paths) > 1:
            if output_path_value.exists():
                if not output_path_value.is_dir():
                    raise SystemExit(
                        "--output must be a directory when multiple inputs are provided"
                    )
                output_dir = output_path_value
            else:
                if output_path_value.suffix.lower() == ".pdf":
                    raise SystemExit(
                        "--output must be a directory when multiple inputs are provided"
                    )
                output_dir = output_path_value
                output_dir.mkdir(parents=True, exist_ok=True)
        else:
            if output_path_value.exists() and output_path_value.is_dir():
                output_dir = output_path_value

    for input_path in input_paths:
        if args.inplace:
            output_path = input_path
        elif output_dir:
            output_path = output_dir / input_path.name
        elif args.output and len(input_paths) == 1:
            output_path = Path(args.output).expanduser().resolve()
        else:
            output_path = input_path.with_name(f"{input_path.stem}_compressed.pdf")

        print(
            f"Compressing {input_path.name} -> {output_path.name} | "
            f"dpi={args.dpi} quality={args.quality}"
        )
        compress_pdf(input_path, output_path, args.dpi, args.quality)

    if len(input_paths) == 1:
        print(f"Wrote {output_path}")
    else:
        print(f"Processed {len(input_paths)} file(s)")


if __name__ == "__main__":
    main()
