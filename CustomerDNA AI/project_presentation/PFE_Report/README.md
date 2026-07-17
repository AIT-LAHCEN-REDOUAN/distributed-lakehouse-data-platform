# Master's PFE LaTeX Template

This folder contains a clean LaTeX template for a Master's PFE report:

- Main file: `main.tex`
- Style goal: academic, clean, and Overleaf-friendly
- Cover page: based on the old mini-project cover-page structure only

## What this template already handles well

- Safe margins for academic reports
- Better protection against page overflow
- Safe handling for:
  - large figures
  - long tables
  - code listings
  - URLs
  - chapter headers and page numbering
- Diagram support with:
  - `tikz`
  - `pgfplots`
  - standard figure/caption/label workflow

## Overleaf structure assumed by `main.tex`

The template is written for this project tree:

- `PFE_Report/main.tex`
- `PFE_resources/Figures/...`
- `PFE_resources/Figures/Logos/...`

Current logo references expected by the template:

- `../PFE_resources/Figures/Logos/Logo Universite.png`
- `../PFE_resources/Figures/Logos/image.png`

If you rename logo files in Overleaf, update only these commands in `main.tex`:

- `\LeftLogoFile`
- `\RightLogoFile`

Also replace the metadata placeholders in `main.tex`:

- `\UniversityName`
- `\SchoolName`
- `\DepartmentName`
- `\ProgramName`
- `\ReportType`
- `\ReportTitle`
- `\ReportSubtitle`
- `\StudentName`
- `\SupervisorName`
- `\CoSupervisorName`
- `\AcademicYear`
- `\DefenseDate`

## Recommended Overleaf compiler

Use `pdfLaTeX`.

This template intentionally uses `listings` instead of `minted` so you do not need shell-escape.

## Quick note on overflow prevention

If a page still overflows in a specific chapter:

- reduce a figure from `1.0\textwidth` to `0.9\textwidth`
- use `adjustbox` for wide tables
- use `longtable` for multi-page tables
- insert `\FloatBarrier` after figure-heavy sections
