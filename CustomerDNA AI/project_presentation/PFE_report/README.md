# AdOptimizer CDP - Report Workspace

This workspace is designed for chapter-by-chapter report production.

It must be treated as a **standalone report folder**.

That means:

- it should be possible to open only this folder in TeXstudio,
- compile the report from this folder alone,
- store all report-specific assets inside this folder,
- and avoid dependency on the presentation folder.

## Folder logic

- `00_master/`
  - report-wide rules, structure, project summaries, and writing workflow
- `01_front_matter/`
  - non-chapter pages such as abstract, acknowledgements, acronyms, and other opening matter
- `02_...` to `11_...`
  - one folder per report chapter
- `12_references/`
  - bibliography strategy and reference assets
- `13_appendices/`
  - appendices, deployment commands, supplementary tables, and technical annexes
- `90_assets/`
  - reusable figures, tables, and Draw.io diagrams
- `91_evidence/`
  - screenshots, logs, and validation notes used as proof
- `99_submission_package/`
  - final cleaned export-ready package

## Recommended authoring rule

Each chapter folder should eventually contain:

- a chapter outline,
- the working draft,
- chapter-specific evidence notes,
- figure planning notes,
- and any localized chapter references.

## Isolation rule

This folder should contain everything needed for report authoring and compilation.

The broader `project_requirements/` folder remains a reference source for report-building support, but the report workspace itself should remain coherent and readable on its own.

## TeXstudio rule

The final LaTeX project should be compiled by opening only `PFE_report/` in TeXstudio.
