# Presentation Assets

## Core files
- `napcore-helpdesk-presentation-pandoc.md`: slide source for Pandoc.
- `napcore-helpdesk-speaker-notes.md`: speaker notes aligned to slide flow.
- `napcore-helpdesk-executive-summary.md`: one-page executive brief.
- `napcore-helpdesk-presentation-summary.md`: extended slide narrative.

## Build outputs
Generated files are written to `dist/` at repository root.

## Make targets
From repository root:

- `make slides-pdf`
- `make slides-pptx`

## Requirements
- `pandoc` for both PDF and PPTX outputs.
- For PDF: one of `xelatex`, `lualatex`, or `pdflatex`.

## Manual command
- `bash scripts/render-slides.sh pdf docs/presentation/napcore-helpdesk-presentation-pandoc.md dist/napcore-helpdesk-presentation.pdf`
- `bash scripts/render-slides.sh pptx docs/presentation/napcore-helpdesk-presentation-pandoc.md dist/napcore-helpdesk-presentation.pptx`
