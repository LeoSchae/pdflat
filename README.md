# PDFlat (flatten and compress pdfs)

A simple python script that reads a PDF and turns it into a PDF containing only a single image per page.
All vector text is lost. It is intended as a simple compression tool for PDF scans or bad vector PDFs (as some handwritten vector PDFs tend to be huge for reasons beyond me).

## Usage

```bash
python3 pdflat.py --dpi 300 --quality 90 /path/to/input.pdf

python3 pdflat.py --dpi 300 --quality 90 --width a4 --height a4 /dir/*.pdf

python3 pdflat.py --dpi 300 --quality 90 --output outdir a.pdf b.pdf
```

One can also use the `--inplace` flag to overwrite PDFs in place.

The program works with Bash wildcards, for example: `python3 pdflat.py --dpi 300 --quality 90 docs/*.pdf`.

## Examples

Rasterize a file and save it to the output (input and output path can be the same):
```bash
python3 pdflat.py --dpi 300 --quality 90 --output out.pdf input.pdf
```

Rasterize two files at the same time. Saved to `[name]_compressed.pdf` in the same folder as the original:
```bash
python3 pdflat.py --dpi 300 --quality 90 a.pdf b.pdf
```

Rasterize all PDFs in the folder and save them in the output folder:
```bash
python3 pdflat.py --dpi 300 --quality 90 --output out/ in/*.pdf
```

Rasterize a file and ensure all pages are the same width as A4 paper (preserving the original aspect ratio). Override the input PDFs in place:
```bash
python3 pdflat.py --dpi 300 --quality 90 --width a4 --inplace input.pdf
```

Ensure all pages are exactly A4 paper size and override the input PDFs in place:
```bash
python3 pdflat.py --dpi 300 --quality 90 --width a4 --height a4 --inplace in/*.pdf
```


## Notes

- `--dpi` controls rasterization resolution.
- `--quality` controls JPEG quality (0-100, higher = better quality, larger files).
- `--width` and `--height` set the output canvas size. Options are:
    - Standard paper sizes: `a1-a10`, `letter`, `legal` (for landscape add `~` as a suffix, e.g. `a4~`).
    - Custom length with unit (e.g. `210mm`, `8.5in`, `595px`).
- `--output` sets the output PDF path (or a directory when multiple inputs are provided).
- `--inplace` overwrites the input PDF
    - Cannot be used in combination with `--output`
