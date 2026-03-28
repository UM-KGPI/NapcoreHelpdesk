#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 3 ]]; then
  echo "Usage: bash scripts/render-slides.sh <pdf|pptx> <input-md> <output-file>" >&2
  exit 1
fi

format="$1"
input_md="$2"
output_file="$3"

if [[ "$format" != "pdf" && "$format" != "pptx" ]]; then
  echo "Error: format must be 'pdf' or 'pptx'." >&2
  exit 1
fi

if [[ ! -f "$input_md" ]]; then
  echo "Error: input file not found: $input_md" >&2
  exit 1
fi

if ! command -v pandoc >/dev/null 2>&1; then
  echo "Error: pandoc command not found." >&2
  echo "Install pandoc and ensure it is available on PATH." >&2
  exit 1
fi

output_dir="$(dirname "$output_file")"
mkdir -p "$output_dir"

if [[ "$format" == "pdf" ]]; then
  # Use a broadly available fallback chain for PDF engines.
  pdf_engine=""
  if command -v xelatex >/dev/null 2>&1; then
    pdf_engine="xelatex"
  elif command -v lualatex >/dev/null 2>&1; then
    pdf_engine="lualatex"
  elif command -v pdflatex >/dev/null 2>&1; then
    pdf_engine="pdflatex"
  else
    echo "Error: no LaTeX PDF engine found (xelatex/lualatex/pdflatex)." >&2
    echo "Install a TeX distribution (for example MacTeX) to build PDF slides." >&2
    exit 1
  fi

  echo "Rendering PDF slides with $pdf_engine"
  pandoc "$input_md" -t beamer --pdf-engine="$pdf_engine" -o "$output_file"
else
  echo "Rendering PPTX slides"
  pandoc "$input_md" -t pptx -o "$output_file"
fi

echo "Created $output_file"
