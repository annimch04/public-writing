# Fieldlight Archive Method — Operational Protocol

Version: 1.0  
Prepared: 2026-08-13  
Status: review draft

This protocol translates [The Fieldlight Archive Method](../fieldlight-archive-method.md) into a working record system. It is deliberately tool-agnostic. A file manager, spreadsheet, text editor, checksum utility, OCR system, version-control system, and AI assistant are sufficient.

## 1. Start with an archive code

Choose a short uppercase code and keep it stable. The examples below use `ARC`.

Do not encode privacy, interpretation, ownership, or a mutable category inside the identifier. Store those properties in metadata fields so they can change without renaming the source.

## 2. Minimal directory model

```text
archive/
├── 00_catalog/
│   ├── source-register.csv
│   ├── representation-register.csv
│   ├── connection-ledger.csv
│   └── correction-log.csv
├── 01_originals/
│   └── YYYY-MM-DD_accession-label/
├── 02_working/
│   └── YYYY-MM-DD_accession-label/
├── 03_extractions/
├── 04_analysis/
├── 05_outputs/
└── 99_admin/
    ├── accessions/
    ├── manifests/
    ├── method/
    └── templates/
```

The numbers describe layers, not importance. Originals stay distinct from working files; extraction stays distinct from interpretation; public outputs stay distinct from both.

## 3. Identifier model

Activate only the prefixes the archive needs.

| Pattern | Unit |
|---|---|
| `ARC-ACC-YYYYMMDD-###` | One acquisition or import boundary |
| `ARC-NB-####` | Bound notebook |
| `ARC-NB-####-LL-###` | Loose leaf stored with a notebook |
| `ARC-LL-####` | Standalone loose leaf |
| `ARC-CAP-#####` | Documentation capture of another source |
| parent-scoped `-REP-###` | Independently cited representation or version of a source/work |
| `ARC-CHT-####` | Chat conversation or coherent export unit |
| `ARC-ACD-####` | Academic work or coherent research unit |
| `ARC-DRN-####` | Drone flight or shoot |
| `ARC-PHS-####` | Photographic series or event |
| `ARC-FIC-####` | Fiction work |
| `ARC-PUB-####` | Public work, series, representation, or project record |
| `ARC-CON-####` | Connection claim |
| `ARC-COR-####` | Material correction, split, merge, or retraction record |
| `ARC-RQ-####` | Formally registered research question |

Rules:

1. Numbers are archive-wide within a prefix.
2. Never recycle an identifier.
3. Never renumber earlier records to make a sequence look cleaner.
4. A source split keeps the earlier ID with the first defensible unit and appends a new ID for the separated unit.
5. A file is not automatically a source. Use a representation relationship unless independent source status is justified.

## 4. Source register

One row represents one source or coherent work-level entity.

Required fields:

| Field | Meaning |
|---|---|
| `source_id` | Stable identifier |
| `accession_id` | Acquisition boundary that brought it into custody |
| `source_type` | Notebook, session, chat, work, series, project, and so on |
| `parent_id` | Parent source, series, or container if applicable |
| `label` | Short human-readable name |
| `description` | Bounded description, not full interpretation |
| `date_value` | Date or range as known |
| `date_basis` | Artifact inscription, metadata, creator account, file history, inference |
| `privacy` | Public, Private, or Restricted |
| `rights_authorship` | Known creator, collaborator, third-party, mixed, unresolved |
| `inventory_status` | Current source-level processing state |
| `preservation_location` | Path or durable custody reference |
| `representation_count` | Count of linked representations, when useful |
| `coverage` | Not reviewed, Sampled, Near-complete, or Complete |
| `notes` | Uncertainties, risks, or immediate next action |

Use dates as typed date values where possible. Do not turn a later file-modification timestamp into an original composition date. Preserve the timestamp and state its basis.

## 5. Representation register

Use one row per file or capture when the archive needs file-level traceability.

Minimum fields:

- `representation_id`
- `source_id`
- `role`
- `filename`
- `format`
- `captured_or_created_at`
- `date_basis`
- `master_location`
- `working_location`
- `sha256`
- `relationship_note`
- `privacy`
- `review_status`

Examples of `role`: cover capture, recto, verso, alternate view, export, working draft, final submission, audio derivative, social archive index, OCR text.

## 6. Status vocabulary

Use controlled values wherever possible.

### Privacy

- `Public` — already public or approved for public release in this form.
- `Private` — creator material not approved for release.
- `Restricted` — heightened sensitivity, third-party information, credentials, health/family material, precise locations, legal/rights concerns, or another reason requiring deliberate handling.

Privacy controls disclosure. Analysis access is a separate authorization that must be recorded explicitly.

### Inventory status

- `Unassigned`
- `Inventoried`
- `Needs reconciliation`
- `Preserved and inventoried`

### Orientation coverage

- `Not reviewed`
- `Sampled`
- `Near-complete`
- `Complete`

Coverage describes the available representation reviewed, not necessarily the physical source's completeness.

### Analysis status

- `Not started`
- `Orientation complete`
- `Packet selected`
- `Extraction complete`
- `Connection testing`
- `Bounded synthesis complete`
- `Retracted or superseded`

## 7. Accession procedure

For every import:

1. Assign an accession ID.
2. Write the boundary before copying.
3. Record source application, device, folder, box, album, export, or custodian.
4. Record known incompleteness, sync instability, and unavailable files.
5. Export or copy originals using a method that preserves relevant metadata.
6. Reconcile file counts and sizes.
7. Generate a SHA-256 manifest when feasible.
8. Verify the copied files against the manifest.
9. Create working derivatives separately.
10. Add source and representation rows.
11. Record sensitive people, locations, metadata, and rights issues.
12. Name the next orientation unit and the completion test.

If the source population is changing, freeze a dated cutoff. Do not wait indefinitely for a theoretically final cloud state, and do not imply that the cutoff is complete.

## 8. Orientation procedure

Orientation is breadth-first.

For each source or coherent series:

1. state the purpose and limits;
2. identify source and representations;
3. declare coverage;
4. map internal structure and dates;
5. list material classes and named works;
6. identify privacy and quality risks;
7. record standout regions without interpreting them fully;
8. identify gaps and alternate versions;
9. propose bounded evidence packets;
10. name one next action.

Do not choose the most emotionally intense or visually dense source as the implicit definition of the batch. Complete an orientation map across the accession before whole-batch synthesis.

## 9. Evidence-packet procedure

Each packet needs:

- one question;
- an explicit boundary;
- included source IDs and locations;
- a reason for every inclusion;
- exclusions and why they matter;
- privacy level;
- completion test;
- expected disconfirmation or counterevidence.

A packet may be chronological, thematic, event-centered, work-centered, version-centered, or contradiction-centered. It should not be “everything related to this broad idea.”

## 10. Transcription and extraction rules

- Preserve original wording, spelling, line breaks, and uncertainty when fidelity matters.
- Put normalized text in a separate field or file.
- Use `[illegible]`, `[uncertain: …]`, or an equivalent visible marker; do not guess silently.
- Identify AI-generated OCR or description as such.
- Verify any quotation used in analysis against the source image or file.
- Retain positional context: page, capture, timestamp, record, paragraph, cell, slide, or commit.
- Treat card, object, face, and place recognition as candidates until directly reviewed when analytical use depends on exact identity.

## 11. Connection ledger

Each row is one claim, not a theme bucket.

Required fields:

| Field | Meaning |
|---|---|
| `connection_id` | Stable claim identifier |
| `source` | Source ID and location |
| `target` | Source, event, person, work, concept, or external record |
| `relationship` | What is being asserted |
| `basis` | Creator supplied, direct evidence, documentary evidence, external evidence, or inference |
| `confidence` | High, Medium, or Low support for this exact claim |
| `privacy` | Disclosure level |
| `note` | Bounded explanation |
| `next_action` | How to verify, weaken, or falsify the claim |
| `status` | Candidate, Supported, Disputed, Retracted, or Superseded |

Do not place multiple logically independent claims in one row. A direct textual match and an inferred causal influence are different claims.

## 12. Correction protocol

A correction record is required when:

- two representations previously grouped as one source are split;
- two sources are merged or cross-referenced;
- a date basis changes;
- authorship or rights attribution changes;
- a quotation or transcription is corrected;
- an interpretation is retracted or materially narrowed;
- a public derivative requires amendment.

Never erase the earlier state if it has been cited or used analytically. Record the old value, new value, reason, evidence, affected records, date, and reviewer.

## 13. Analysis memo standard

Every bounded synthesis should contain:

1. question;
2. evidence boundary;
3. method;
4. strongest supporting evidence;
5. counterevidence and negative evidence;
6. contradictions and unresolved issues;
7. finding with calibrated confidence;
8. plausible competing explanations;
9. what would disconfirm or materially revise the finding;
10. next evidentiary step;
11. privacy and publication boundary;
12. human and AI contribution note.

Separate a claim about **artifact order** from a claim about **internal cognitive order**. The former may be supported by dates and versions; the latter usually requires creator-at-the-time testimony and prospective records.

## 14. Human–AI operating loop

Use this loop for any AI-assisted pass:

1. Human states the purpose, boundary, and release authority.
2. AI inventories or describes candidate records.
3. AI labels uncertainty and reports omissions or tool limitations.
4. Human corrects identity, grouping, context, and privacy.
5. AI updates the durable register without erasing the correction trail.
6. AI proposes bounded connections or packets.
7. Human accepts, rejects, or reframes the question.
8. AI tests the accepted question against supporting and conflicting evidence.
9. Human reviews the finding and controls publication.

If the human cannot review every record, the AI must declare sampling, automation, confidence, and validation rates. “AI reviewed” is not a meaningful coverage statement by itself.

## 15. Public-release gate

Before release, answer each question explicitly:

- Is the source itself public, or is this a new derivative?
- Who owns or authored the source and derivative?
- Does it contain third-party names, health/family details, contact information, credentials, precise locations, or embedded metadata?
- Does quotation or reproduction require permission?
- Are creator testimony and inference labeled?
- Does the release imply more certainty than the private analysis supports?
- Are AI contributions described accurately?
- Can a reader locate the public source trail without gaining access to private masters?
- Has the creator approved this exact derivative?
- Is there a correction and withdrawal path?

Any unresolved high-risk item blocks release, not private preservation.

## 16. Quality checks

Before closing an accession or analysis pass:

- counts reconcile across source, representation, and file manifests;
- identifiers are unique and never recycled;
- every representation maps to one source or an unresolved queue;
- preservation masters are unchanged;
- date basis is explicit;
- privacy and rights fields are populated;
- orientation coverage is declared;
- every quotation is locatable;
- connection claims have basis and confidence;
- corrections are retained;
- whole-corpus language is not based on one accession or domain;
- public outputs have passed the release gate.

Blank records are available in the [templates directory](./templates/).

