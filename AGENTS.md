# Working in Prospector

Prospector is our Codex-led register of cosmology prospects. Find interesting
physics, read the actual papers and preserve evidence for useful investigations.
Welcome conventional and unusual cosmologies, predictions, criticism and null
results. Novelty, popularity and confidence are not scientific evidence.

Prospector owns literature, idea relationships and candidate investigations.
Reproducible owns accepted experiments and results; Irreducible owns compiled
science. Work in this checkout unless the user asks otherwise.

## Continue when the user says “run more”

Read `state.json`, the latest `scans/` record, the register and graph. Resume
pending screens, acquisitions, reads and reviews before new discovery. Use the
least recently searched topic lane; alternate fresh work with foundations,
citation leads and challenges. Do not repeat questions already settled here.

A normal batch admits at most 20 new versions, reads at most 6 papers with Luna
and sends at most 3 useful papers to Sol. These are ceilings, not quotas. Use
at most 3 simultaneous workers, respecting a lower live limit. Follow at most
5 citation leads and one citation hop. Finish a coherent batch, save remaining
work and stop. Two distinct empty searches may close a batch; never call the
literature exhausted. This authorizes bounded literature work and requested
repository publication, not endless scans, numerical experiments, schedules,
external messages or merges.

## Use the requested Codex agents

Use actual Codex subagents. **Luna is `gpt-6-luna`, medium reasoning; scientific
review is exactly `gpt-6.1-sol`, high reasoning.** No silent Astra/model substitution.
If unavailable, preserve the blocked stage and report it.

Select the model explicitly with fresh or small context; full-history forks can
inherit the coordinator's model. Give each Luna reader one admitted version,
local sources and `docs/records.md`. Record requested model, agent ID, source
hashes and coverage. Do not invent actual backend identity when unexposed.

Luna reads all main text and relevant appendices, extracts distinct mechanisms,
equations, predictions, assumptions and caveats, and assesses usefulness.
Separate author proposals, fitted results, measurements and reader inferences.
Record unread material, uncertain math and captions-only figure checks.

Sol checks original sources, Luna's packet and relevant graph neighbours:
equations, units, conventions, limits, data ancestry, overlap and what a simpler
test would establish. Correct extraction visibly. Useful ideas need Sol review
before graph acceptance or design promotion. Review is not independent
reproduction, current-data reassessment or scientific qualification.

Workers write separate packets; one coordinator integrates public records.
**Keep all working files inside Prospector**, under ignored `.work/`, `papers/`
or `downloads/`, including renders, temporary scripts and logs. Never use a
sibling checkout or `/tmp`. Acquire centrally before parallel reading; readers
reuse local sources rather than launching competing download loops.

## Search and acquire arXiv efficiently

Use the HTTPS Atom API at `https://export.arxiv.org/api/query`, through
`scripts/arxiv.py` or equivalent bounded calls. Save exact query, order, offset,
UTC time, result IDs and disposition.

1. Prefer narrow `ti:`/`abs:` phrases and appropriate `astro-ph.CO`, `gr-qc`,
   `hep-ph` or `hep-th` categories. Use `all:` for deliberate breadth. Include
   legacy `astro-ph` and cross-field searches for foundations.
2. Retrieve 10–20 entries. Use `lastUpdatedDate` for recent work, `relevance`
   for mechanisms. Neither proves usefulness or coverage. Split broad queries
   by mechanism/date rather than downloading thousands of entries.
3. Deduplicate versions/base IDs. Batch known-ID lookups and verify title,
   authors, categories and version before admission. Journal versions may differ.
4. Try pinned `/html/<id>vN`; verify title/body and preserve math/section anchors.
   A status 200 alone is not proof it is the intended complete paper.
5. Acquire pinned PDF for missing HTML and source checks. On main-route failure
   try `https://export.arxiv.org/pdf/<id>vN`. `pdftotext -layout` is a reading aid;
   check important formulas, tables and figures against original math/rendered
   pages. Captions are not visual inspection. Use TeX only for unresolved needs.

RSS supports current-category intake; web search supports terminology/citation
leads. Resolve hits to primary metadata/full text. Record failed access and try
another lawful route; never treat it as rejection or repeatedly scrape failures.

Follow current [arXiv API terms](https://info.arxiv.org/help/api/tou.html): one
connection and at least 3 seconds between legacy API/RSS requests. The helper
uses a repo-local lock and applies the interval to full text too. Defaults:
20-second timeout, 10 MiB response allowance. Record a larger allowance explicitly
or defer oversized files. On transient failures allow one retry after 30 seconds
or longer Retry-After; change route on 403/406 and stop acquisition on 429.

Check cache hashes before reuse. Reacquire missing assets from pinned URLs; a
hash mismatch needs a new receipt and explicit report. Metadata query feeds are
changing snapshots. Preserve earlier paper source identity rather than overwriting
it to hide change. Do not evade access controls or redistribute raw sources.

## Store evidence and group prospects

Use `docs/records.md` and schemas. Store identity/version, URLs, UTC retrieval,
read-source hashes, licence/access status, coverage, decisions, model/agent
provenance, equations/locators, definitions, units, domains, predictions and
observation lineage. Values need uncertainty interpretation and model/dataset
conditioning. Missing values are null with reasons, never guessed parameters.

Git holds metadata, links and short original notes. Keep PDFs, TeX, full HTML/text,
copied abstracts, large tables, chains, credentials and complete worker logs local
and ignored. Public local paths are relative. Ignore rules do not grant rights
or remove previously tracked files.

Group papers under `register/prospects/` by question/mechanism. Groups are
navigation aids, not equivalence claims. Papers/ideas can have multiple groups.
The source of relationships is `register/graph.json`; generate the browsing tree
and map from it. Use stable idea IDs and reviewed source evidence.

Sol checks degrees of freedom, equations, parameterization, domains, background
and perturbation closure, and observables before accepting equivalence. Edges
separate specialization, partial overlap, physical distinction, motivation,
critique, shared data and updates. Keep uncertain links provisional. Only the
specialization subgraph must be acyclic.

Track shared objects, calibrators, simulations and likelihoods. Repeated fits
to shared observations are not independent; unknown cross-covariance stays
unknown. Keep negative and corrected records. A printed source inconsistency
is distinct from our transcription error and any suggested repair.

## Prepare a candidate investigation

A candidate-design JSON names an exact sourced claim, equations, minimal test,
lost scope, input lineage, unknowns and readiness. It is a Prospector handoff,
not an accepted Reproducible recipe or executable Irreducible request.

Inspect Irreducible's current request schema, compiled capabilities and
`docs/run-recipes.md` before offering execution. Record commit and dirty state;
discover the current sibling checkout. Missing physics means a blocked design
and source-development task. Never relabel EDE, NEDE, timescape or modified
gravity as LCDM/CPL to make a request run. JSON selects compiled models; it does
not execute arbitrary equations/scripts. Do not invent hashes, covariance,
priors, perturbations or tolerances.

A background ruler test cannot establish a CMB Hubble-tension solution. Present
and past deceleration, decreasing acceleration and jerk differ. Declare time,
redshift and observable conventions. Keep observational, numerical, inference
and interpretation qualification separate.

## Close and publish a batch

Integrate valid records, write a scan receipt and update state last. Preserve
pending stages on interruption; save screen/defer/exclude decisions to prevent
repeated reading. Run:

```bash
uv run python scripts/validate_register.py
uv run python scripts/build_register.py
```

Check views, source hashes, local links, ignored storage and Git diff. Structural
validation is not scientific validation. Report new versions, actual Luna reads,
Sol reviews, new/overlapping ideas, readiness and material limitations.

Follow `CONTRIBUTING.md` and `docs/development.md`. Use a `codex/` branch, stage
coherent explicit paths, commit useful checkpoints, push for backup and open a
reviewable PR. Preserve unrelated work. The owner gives standing authorization
across Irreducible, Reproducible and Prospector to create PRs, review our own
changes in a separate deliberate pass and merge ready PRs without asking again.
Inspect the complete final diff, fix actionable findings, resolve conversations
and require applicable green CI on the latest integrated head and up-to-date
base. Verify the exact head and use a merge commit. A separate human reviewer is
not required; scientific independence and qualification need their own evidence.
Direct main pushes, force pushes and external messages still require specific
authorization. A literature batch does not authorize numerical experiments or
scheduling. Verify merged state and ancestry before safe cleanup; preserve dirty
or active worktrees and extra commits. Never force-delete work or bypass a failed
check or claim absent CI passed.
