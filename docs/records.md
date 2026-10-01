# Record conventions

Strict JSON is canonical; Markdown and the map are generated views. Preserve
source identity and decisions so Codex can continue without a transcript.

| Path | Purpose |
| --- | --- |
| `register/papers/<version>.json` | Metadata, source receipts, screen, Luna extraction and review |
| `register/ideas/<id>.json` | Reviewed mechanisms, assumptions, predictions and locators |
| `register/prospects/<id>.json` | Navigation groups linking papers, ideas and investigations |
| `register/reviews/<id>.json` | Sol source checks, corrections, overlap and limits |
| `register/graph.json` | Typed evidence relationships |
| `register/README.md`, `register/map.html` | Generated tree and interactive map |
| `designs/<id>.json` | Candidate investigation handoffs |
| `scans/<id>.json`, `state.json` | Actual batch records and continuation queue |
| `.work/`, root `papers/`, root `downloads/` | Ignored full sources, rendering and working material |

## Papers and reading

Paper identity is `arxiv:<base-id>vN`. Encode legacy filename slashes as `__`,
keeping real IDs/URLs. New versions get separate records, not independent-paper
claims. Receipts retain URL, UTC time, bytes and SHA-256. Derived reading text
also identifies its source PDF digest and extraction tool.

The [paper schema](../schemas/paper.schema.json) separates discovery, screening,
reading and review. A metadata discovery has no reading claim. Screens identify
metadata/abstract/full-text basis and a specific decision/reason. Topic membership
from an abstract is provisional navigation, not accepted scientific identity.

Luna writes a local packet with `paper_id`, `requested_model`, `reading_level`,
`coverage`, `summary`, `ideas`, `quantities`, `data_dependencies`, `caveats`,
`usefulness` and `citation_leads`. Add agent ID/provenance on integration. Coverage
names sections/pages, visual figure checks and missing material. Keep original
source-derived prose compact; do not publish abstracts/full text.

Preserve the original worker-packet digest and source hashes. Correct coverage
with a dated amendment naming the agent, new checks and previous statement;
retain the original packet locally. Review details must cover each reviewed
paper and reference its receipted original-source hashes. A metadata digest
alone cannot support a full reading or scientific review.

Extracted ideas have local ID, title, statement type, description, locators and
equations. Separate author proposal/prediction, reported fit/measurement and
reader inference. Equations need expression, locator, conventions/definitions,
domain and transcription confidence. Quantities need value, unit, uncertainty
interpretation, conditioning and locator. Distinguish means, best fits, assumptions
and test choices. Null means unknown/unreported, with a reason in context.

## Review and grouping

Sol checks original sources and the extraction. Retain checked coverage, source
hashes, corrections, data ancestry, overlap and limits. Keep original extraction
with visible review corrections; accepted ideas/designs use the reviewed reading.
A printed source error and an algebraic repair have separate identities.

Ideas have stable slug, title, family, source evidence, assumptions, predictions
and review ID. Prospects have stable slug, title, scope and paper/idea/design ID
arrays. Prospect membership is navigation, not a theory-equivalence judgement.

Graph nodes are all paper and idea IDs. Edges have unique ID, `from`, `to`, type,
status, rationale, evidence and review ID. Types: `describes`, `motivates`,
`specializes`, `partial_overlap`, `physically_distinct`, `shares_data`, `critiques`,
`updates`. Reviewed edges require Sol provenance; uncertainty stays provisional.
Specialization points child to parent and must be acyclic. Other relationships
can form cycles. Shared data is not an independent confirmation.

## Candidate investigations and continuation

The [candidate-design schema](../schemas/candidate-design.schema.json) names one
sourced claim, minimal test, equations/definitions/domain, assumptions, observables,
lost scope, inputs, unknowns, verification/falsification gates and consumer blockers.

Readiness is `needs_review`, `blocked` or `ready_for_consumer_review`. The last
requires Sol review, no blockers/unknowns and a separate consumer-validated request
with digest and inspected revision. It still needs Reproducible acceptance.
Blocked concepts keep executable request null; runs/qualification belong to consumers.

Scan records retain exact queries/order/offset, UTC times, result IDs, admitted
versions, screens, full reads, reviews, changes, failed access and pending stages.
Counts name actual stages. State queues existing IDs and next action. Updated-date
feeds require overlap and deduplication; small batches cannot claim gap-free coverage.

`registered_papers` lists records admitted or worked on in that batch;
`new_versions` lists first admissions only. Reused records and duplicate search
hits do not increase discovery counts. Unfinished non-excluded papers must remain
queued; review stages require full readings, and completed-scan claims require
the corresponding reading/review records.

The acquisition helper saves a partial manifest after rate limits or extraction
failure, alongside successful receipts. HTML title/body screening and a PDF
signature are intake checks; the reader still verifies exact source identity and
coverage. HTTP 429 stops acquisition in that batch directory, including on resume.

Integrate/validate/build before recording completion. Preserve unfinished stages
on interruption. Recheck cache hashes; record changed bytes rather than replacing
old provenance. Full sources/working files stay ignored inside Prospector. Unknown
licence/access terms stay explicit. Public records never carry credentials or
complete worker transcripts; local paths are relative.

Validation rejects duplicate keys/nonfinite numbers and checks record schemas,
references, graph cycles and promotion gates. Scientific accuracy, actual reading,
licensing and model equivalence remain evidenced review responsibilities.
