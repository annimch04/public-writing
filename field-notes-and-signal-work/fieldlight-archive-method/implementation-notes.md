# Implementation Notes — The Toolchain Used for Version 1.0

Prepared: 2026-08-13  
Status: review draft

The Fieldlight Archive Method is tool-agnostic, but Version 1.0 came from a concrete working environment. This record names the tools and what they did so that the method can be reproduced, substituted, or audited.

## Working environment

- macOS laptop as the primary custody and processing environment;
- Apple Photos and an iPhone photo library for source discovery and album-level grouping;
- local folders for preservation masters, working derivatives, catalog records, analysis, and outputs;
- Codex as the AI-assisted file, image, spreadsheet, and analysis collaborator;
- Git for version history and public-package review;
- Markdown and CSV for durable, inspectable records;
- XLSX for the human-facing master catalog and filtering layer.

## Tool-to-function map

| Function | Tool used in this implementation | Replaceable with |
|---|---|---|
| Photo-source discovery | Apple Photos albums, date browsing, and visual search | Any photo manager that can preserve original files and metadata |
| Preservation export | Photos “Export Unmodified Originals” | Device or application export that retains originals, filenames, and metadata |
| Filesystem source transfer | macOS `ditto` for metadata-aware copying | A verified copy tool appropriate to the source filesystem |
| Still-image derivatives | macOS `sips` for full-resolution JPEG conversion | ImageMagick, libvips, Preview export, or another documented converter |
| Integrity manifests | SHA-256 command-line hashing | Any maintained SHA-256 implementation with a verifiable manifest format |
| File discovery and comparison | shell tools, `find`, `rg`, Git, file metadata, and targeted format extraction | Equivalent filesystem, search, and version-control tools |
| Document inspection | format-aware extraction and rendering for Word, PDF, PowerPoint, Pages, RTF, and Scrivener material | Any tools that preserve source files and create reviewable derivatives |
| Image review | contact sheets, full-resolution source views, and AI-assisted visual description | Human review, computer vision, or another multimodal model with declared confidence |
| Catalog | CSV registers plus a formatted XLSX workbook | SQLite, Airtable, a collections system, or another exportable structured database |
| Narrative records | Markdown | Plain text, HTML, or another nonproprietary text format |
| Change history | Git commits for catalog, method, and analysis layers | Another versioned document system with author and timestamp history |
| AI collaboration | Codex operating on user-authorized local and accessible cloud material | Another AI system capable of file inspection, structured output, and explicit uncertainty |

## How the human–AI work was divided

### Creator work

The creator:

- defined the archive's purpose and named the project;
- retrieved and handled the physical materials;
- assigned notebook identifiers and wrote them into the sources;
- photographed covers, boundary pages, and selected internal material;
- identified inserted leaves, personal relationships, dates, works, and digital counterparts;
- supplied context that the artifacts could not establish;
- chose which domains to accession next;
- corrected groupings and challenged analytical scope and conclusions;
- retained authority over privacy, interpretation, and public release.

### AI-assisted work

The AI collaborator:

- helped define and extend the identifier system;
- inspected available files, source packages, public repositories, and exported images;
- generated manifests, registers, contact sheets, working derivatives, and catalog updates;
- performed candidate OCR, description, duplicate comparison, version comparison, and cross-source retrieval;
- drafted orientation maps, evidence ledgers, bounded analyses, correction records, and method documentation;
- maintained links among source IDs, representations, claims, and outputs;
- surfaced candidate patterns and research questions;
- ran consistency, privacy, link, formula, rendering, and save-state checks.

### Shared decisions

The process was iterative. The creator's context and corrections changed source identity, grouping, analytical priority, and the meaning of records. AI proposals were not treated as final merely because they were written into a draft. Material corrections were moved into durable records when they affected the archive's structure or claims.

## A reproducible command-line pattern

Exact commands depend on paths and operating system. The general preservation sequence was:

```text
1. Export or copy originals into a dated accession directory.
2. Enumerate the resulting files by type and size.
3. Generate a sorted SHA-256 manifest over preservation files.
4. Verify every manifest entry.
5. Create working derivatives in a separate directory.
6. Generate and verify a second derivative manifest when useful.
7. Record counts, transfer method, omissions, and verification result in the accession note.
8. Add source and representation records to the catalog.
```

Commands and scripts should never target a broad home directory, cloud root, or workspace root destructively. Explicit accession paths and read-only verification should precede any cleanup or replacement.

## AI review modes used

The implementation used several different AI review modes. They should not be conflated:

- **enumeration** — identify files, formats, counts, or metadata;
- **candidate classification** — propose source grouping, card identity, document role, or material type;
- **direct comparison** — compare two visible or extracted representations;
- **orientation** — create a restrained navigation map;
- **connection proposal** — identify a possible cross-source relation;
- **bounded analysis** — test a declared question against a selected packet;
- **quality assurance** — check links, formulas, counts, privacy terms, and saved outputs.

Candidate classification and connection proposal require human or source-based verification before they support consequential interpretation.

## Formats and durability

The working system intentionally uses overlapping forms:

- **original proprietary or device formats** preserve source fidelity;
- **JPEG, plain text, and rendered pages** make review accessible;
- **CSV** keeps registers portable and machine-readable;
- **XLSX** supports human filtering, navigation, visual status, and mixed-domain catalog use;
- **Markdown** preserves methods and analysis in diffable text;
- **Git** records revisions to the non-master layers.

No one format is asked to do every job.

## Known technical limitations

- Cloud photo populations can change during discovery and export.
- Visual search is neither exhaustive nor stable enough to define an accession without review.
- File timestamps may describe surviving copies, not original composition.
- OCR and image recognition degrade with handwriting, oblique captures, glare, overlaps, and partial objects.
- Proprietary project formats can contain internal metadata and duplicate or generated records whose meaning requires format-specific inspection.
- Spreadsheet rendering and formula evaluation must be checked in the saved file, not only in memory.
- AI can produce coherent but unsupported groupings and explanations; correction logs and bounded claims are structural safeguards, not optional commentary.

## What was deliberately not automated

- writing identifiers into physical sources;
- determining private personal meaning from artifact appearance alone;
- deciding that a public derivative was safe to release;
- deleting duplicates or masters;
- rewriting creator testimony;
- resolving authorship solely from file location;
- treating a symbolic pattern as external validation.

The method uses automation for scale and traceability while preserving human authority where context, consequence, and consent matter.

