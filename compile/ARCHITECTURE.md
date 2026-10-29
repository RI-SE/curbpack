# Compile

Compile owns reporting from existing Check results. The new PDF component follows the `compile/` ownership in [system architecture](../docs/arch/ARCHITECTURE.md). Existing JSON report assembly and validation currently remain in `review/compile.py`; their migration is separate work. Final-review decisions and signing remain in `review/`.

## PDF component

`pdf.compile_pdf(report_path, out)` reads a saved review-report JSON through the existing `review.compile.load_report` validator and writes a new monochrome A4 PDF. It returns the output path. `cli.main` supplies the command-line interface; root `compile-pdf.py` is a thin entry point.

The PDF is a presentation of the existing [output contract](../docs/reference/outputs.md#review-report). It introduces no persistent JSON fields. It groups embedded Claims by embedded Requirement, preserving the recorded outcomes and arguments. It does not run Checks, load current evidence or repository files, fetch sources, contact a model, record a decision, or sign anything.

Recorded signature metadata is displayed with the object, identity, stated time, version digest, and explicit verification-not-performed explanation. Recorded appendix reasons remain unchanged. A JSON signature does not cover the PDF bytes.

ReportLab provides layout and bundled Vera TrueType fonts, including Swedish characters. All source strings are escaped before paragraph layout. Long passages and arguments wrap across pages. No colour, interactive controls, file-opening actions, or network-loaded fonts are required.

The parent output directory must exist. Rendering completes in a temporary sibling file before the destination is created exclusively. Existing outputs (including symlinks) are refused; failures clean up the temporary file. Input report bytes and existing PDFs remain unchanged. Filesystems that cannot create the exclusive hard link return an error without replacing an output.

## Verification

`tests/test_compile_pdf.py` exercises the real command, uses pypdf to read the generated PDF, and checks historical content, Unicode, multipage output, explicit statuses, recorded decision/signature presentation, invalid input, and preservation of existing files. Visual acceptance additionally inspects actual pages for wrapping, pagination, grayscale layout and absence of controls.
