# PDFlat (flatten and compress pdfs)

A simple python script that reads a pdf and turns it into a pdf containing only a single image per page.
All vector text is lost. It is intendes as a simple compression tool for pdf scans or bad vector pdfs (as some handwritten vector pdfs tend to be huge for reasons beyond me).

## Usage

```bash
python3 pdflat.py --dpi 300 --quality 90 /path/to/input.pdf

python3 pdflat.py --dpi 300 --quality 90 --output /path/to/out.pdf /path/to/input.pdf

python3 pdflat.py --dpi 300 --quality 90 --inplace /path/to/input.pdf

python3 pdflat.py --dpi 300 --quality 90 /path/to/a.pdf /path/to/b.pdf

python3 pdflat.py --dpi 300 --quality 90 --output /path/to/outdir /path/to/a.pdf /path/to/b.pdf
```

One can also use the `--inplace` flag to override pdfs inplace.

The program works with bash wildcards, for example: `python3 pdflat.py --dpi 300 --quality 90 docs/*.pdf`.

## Notes

- `--dpi` controls rasterization resolution.
- `--quality` controls JPEG quality (0-100, higher = better quality, larger files).
- `--output` sets the output PDF path (or a directory when multiple inputs are provided).
- `--inplace` overwrites the input PDF (can not be used in combination with `--output`)
