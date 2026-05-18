#!/usr/bin/env python3
import argparse
import io
from pathlib import Path
import re

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
        "--width",
        help="Optional output width (e.g. a4, a4~, 21cm, 8.27in, 1200px).",
    )
    parser.add_argument(
        "--height",
        help="Optional output height (e.g. a4, a4~, 29.7cm, 11.69in, 1600px).",
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


PAPER_SIZES_MM = {
    "a0": (841, 1189),
    "a0~": (1189, 841),
    "a1": (594, 841),
    "a1~": (841, 594),
    "a2": (420, 594),
    "a2~": (594, 420),
    "a3": (297, 420),
    "a3~": (420, 297),
    "a4": (210, 297),
    "a4~": (297, 210),
    "a5": (148, 210),
    "a5~": (210, 148),
    "a6": (105, 148),
    "a6~": (148, 105),
    "a7": (74, 105),
    "a7~": (105, 74),
    "a8": (52, 74),
    "a8~": (74, 52),
    "a9": (37, 52),
    "a9~": (52, 37),
    "a10": (26, 37),
    "a10~": (37, 26),
    "letter": (215.9, 279.4),
    "letter~": (279.4, 215.9),
    "legal": (215.9, 355.6),
    "legal~": (355.6, 215.9),
    "tabloid": (279.4, 431.8),
    "tabloid~": (431.8, 279.4),
}

def mm_to_points(value_mm: float) -> float:
    return value_mm * 72.0 / 25.4


def parse_length(value: str, dpi: int, dimension: str) -> float:
    """ Return length in points for the given dimension (width or height) """
    if not value:
        raise ValueError("Length value is required")
    if not dimension in ("width", "height"):
        raise ValueError("Dimension must be 'width' or 'height'")

    normalized = value.strip().lower()
    if normalized in PAPER_SIZES_MM:
        width_mm, height_mm = PAPER_SIZES_MM[normalized]
        return mm_to_points(width_mm if dimension == "width" else height_mm)

    match = re.fullmatch(r"(\d+(?:\.\d+)?)(cm|in|px)", normalized)
    if not match:
        raise ValueError(
            "Invalid length. Use a0-a9, letter, or values like 21cm, 8.27in, 1200px."
        )

    number = float(match.group(1))
    unit = match.group(2)
    if number <= 0:
        raise ValueError("Length must be a positive number")

    if unit == "cm":
        return mm_to_points(number * 10.0)
    if unit == "in":
        return number * 72.0
    if unit == "px":
        if dpi <= 0:
            raise ValueError("--dpi must be a positive integer")
        return number * 72.0 / dpi

    raise ValueError("Unsupported length unit")


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


def compress_pdf(
    input_path: Path,
    output_path: Path,
    dpi: int,
    quality: int,
    target_width: float | None,
    target_height: float | None,
) -> None:
    if quality < 0 or quality > 100:
        raise ValueError("--quality must be between 0 and 100")
    if dpi <= 0:
        raise ValueError("--dpi must be a positive integer")

    with fitz.open(input_path) as source:
        output = fitz.open()
        for page in source:
            rect = page.rect
            page_width = rect.width
            page_height = rect.height

            if target_width and target_height:
                output_width = target_width
                output_height = target_height
                scale = min(output_width / page_width, output_height / page_height)
            elif target_width:
                scale = target_width / page_width
                output_width = target_width
                output_height = page_height * scale
            elif target_height:
                scale = target_height / page_height
                output_height = target_height
                output_width = page_width * scale
            else:
                scale = 1.0
                output_width = page_width
                output_height = page_height

            zoom = (dpi * scale) / 72.0
            matrix = fitz.Matrix(zoom, zoom)
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
            out_page = output.new_page(width=output_width, height=output_height)

            image_width = page_width * scale
            image_height = page_height * scale
            x0 = max(0.0, (output_width - image_width) / 2.0)
            y0 = max(0.0, (output_height - image_height) / 2.0)
            image_rect = fitz.Rect(x0, y0, x0 + image_width, y0 + image_height)
            out_page.insert_image(image_rect, stream=buffer.getvalue())

        output.save(output_path, deflate=True, garbage=4)
        output.close()


def main() -> None:
    args = parse_args()
    if args.output and args.inplace:
        raise SystemExit("Use either --output or --inplace, not both")
    if args.width or args.height:
        if args.width is None and args.height is None:
            raise SystemExit("--width or --height must be provided")

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

    target_width = None
    target_height = None
    try:
        if args.width:
            target_width = parse_length(args.width, args.dpi, "width")
        if args.height:
            target_height = parse_length(args.height, args.dpi, "height")
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    size_label = []
    if args.width:
        size_label.append(f"width={args.width}")
    if args.height:
        size_label.append(f"height={args.height}")
    size_label_text = " ".join(size_label) if size_label else "original size"
    print(f"Options: dpi={args.dpi} quality={args.quality} {size_label_text}")

    for input_path in input_paths:
        if args.inplace:
            output_path = input_path
        elif output_dir:
            output_path = output_dir / input_path.name
        elif args.output and len(input_paths) == 1:
            output_path = Path(args.output).expanduser().resolve()
        else:
            output_path = input_path.with_name(f"{input_path.stem}_compressed.pdf")

        print(f"Compressing {input_path.name} -> {output_path.name}")
        compress_pdf(
            input_path,
            output_path,
            dpi=args.dpi,
            quality=args.quality,
            target_width=target_width,
            target_height=target_height,
        )

    if len(input_paths) == 1:
        print(f"Wrote {output_path}")
    else:
        print(f"Processed {len(input_paths)} file(s)")


if __name__ == "__main__":
    main()
