# PDF JPEG Compressor

This repo provides a simple PDF compressor that rasterizes each page and embeds it as a single JPEG image.

## Usage

```bash
python3 pdflat.py --dpi 300 --quality 90 /path/to/input.pdf

python3 pdflat.py --dpi 300 --quality 90 --output /path/to/out.pdf /path/to/input.pdf

python3 pdflat.py --dpi 300 --quality 90 --inplace /path/to/input.pdf

python3 pdflat.py --dpi 300 --quality 90 --glob "docs/*.pdf"

python3 pdflat.py --dpi 300 --quality 90 --glob "docs/*.pdf" --output /path/to/outdir
```

## Notes

- `--dpi` controls rasterization resolution.
- `--quality` controls JPEG quality (0-100, higher = better quality, larger files).
- `--output` sets the output PDF path (or folder when using `--glob`).
- `--inplace` overwrites the input PDF.
- `--glob` processes all matching PDFs (with `--output`, writes into that directory using original filenames).
