# Bounded discovery and local search

`register/searches/*.json` is the contributor-facing memory of arXiv search
windows. JSON is canonical in Git; `.work/crawl.sqlite3` is a disposable local
index built with Python's standard `sqlite3`. There is no database service,
database migration or database file to contribute. Any public source-byte change
invalidates the index. Missing or corrupt databases rebuild from public records.

Use [the sole active roadmap](roadmap.md), the existing `state.json`, relevant
latest scan and queued work first. The tool does
not admit papers, download full texts, launch model readers, run experiments or
schedule future work. A search command makes at most one API page request,
through `arxiv.Client` and its shared repository lock and rate limit. It never
walks the following pages automatically.

```bash
uv run python scripts/crawl.py status
uv run python scripts/crawl.py find 'perturbation' --kind papers --limit 20
uv run python scripts/crawl.py timeline 1811.04083
```

Status combines saved pending screens, failed/interrupted searches and the
existing registered-paper queue. Lanes are ordered by least recent recorded
search, with never-searched lanes first and stable state-file ordering for ties.
The existing `next_work_mode` remains visible. Dates and counts guide bounded
work; they do not measure scientific merit or completeness.

`experiment_priorities` exposes unsuperseded versioned consumer findings and
historical follow-up proposals from `register/feedback/`. They are evidence,
not an active scheduling plan. `active_roadmap` and `next_work_mode` route current
work to the roadmap. Preserve the ordinary queue and source gates, and inspect
pinned feedback before revising a target. Superseded receipts remain in Git and
local search; a newer receipt is not scientific promotion or independent evidence.

## Search a single window

After pending work has been dispatched, completed or explicitly deferred, an
operator can document why one bounded discovery window is appropriate:

```bash
uv run python scripts/crawl.py search \
  '(cat:astro-ph.CO OR cat:gr-qc) AND ti:"modified gravity"' \
  --lane modified-gravity --work-mode foundational_or_citation_linked \
  --order relevance --direction descending --start 0 --limit 10 \
  --discovery-reason 'Queued readers are running; this window screens foundations for the least searched lane.'
```

The reason is a durable operator statement, not an automatic claim that the
queue was completed. When any queue entries remain, a new network attempt needs
`--discovery-reason`. The CLI cannot inspect running reader agents. Page size is
1–20, with 10–20 normally appropriate. Page offset, sort order and direction are
part of request identity; there is no completeness claim from requesting a page.

An identical completed window returns the saved receipt without making a network
call, even if it still has pending screens. Query normalization trims **only
outer whitespace**. It preserves internal whitespace, capitalization, quoted
phrases, category selection and Boolean syntax. Mechanism synonyms and similar
phrases remain distinct requests. This deliberately prefers occasional duplicate
search intent to silently erasing different questions.

Updated-date feeds and other search results change. An explicit refresh keeps
the previous snapshot and needs a concrete `--refresh-reason`, such as checking
for versions published after the previous retrieval. The new receipt references
its predecessor. It never replaces the earlier result order or source identity.

A failed window returns its failure receipt by default. A single reasoned retry
uses `--retry-reason`, with at least 30 seconds elapsed or the longer recorded
`Retry-After`. There is no automatic retry loop. HTTP 403/406 requires a changed
lawful route; this API-only command cannot manufacture such a route. HTTP 429
stops acquisition. A retry that fails is retained and cannot be retried again
through the same chain. Changing request parameters is recorded as a different
window; this is not permission to evade rate limits or repeatedly scrape failures.

Acquisition logs are kept under `.work/crawl-acquisition/<batch-id>/`, defaulting
to the UTC date. A 429 stops all further requests in that batch, including other
query windows. Use `--batch-id` only for a later, newly authorized bounded batch;
changing it does not authorize continuing around a 429 in the same batch. Old
logs and failed receipts remain intact. All batches share the repository's
single arXiv connection/rate-limit lock.

Before networking, the tool writes an interrupted-attempt placeholder. Success
or failure atomically replaces that placeholder under the same search ID. A
process interruption therefore leaves the exact intended request visible. Cached
Atom feeds and acquisition logs remain ignored under `.work/`.

## Resume and screen the same snapshot

```bash
uv run python scripts/crawl.py resume SEARCH_ID
uv run python scripts/crawl.py screen SEARCH_ID arxiv:2202.08291v3 deferred \
  --reason 'Need the pinned original source before deciding whether the perturbation mechanism is useful.'
```

Resume makes no arXiv call. It returns the saved result IDs, order and decisions,
and checks the source digest when the local cache is present. Missing caches on
another contributor's checkout are reported as unavailable, not invented. A
metadata/abstract screen needs that original snapshot or an explicitly receipted
reacquisition; the title-only public receipt cannot stand in for an abstract.
Changed cache bytes block resume until an explicit new acquisition; the earlier
receipt is retained.

All hits have a disposition, including hits never admitted as paper records:
`pending`, `duplicate`, `selected`, `excluded`, `deferred` or legacy `unknown`.
A new exact-version hit already in the register is a duplicate. Another version
of the same base ID is a separate hit requiring screening, never independent
scientific confirmation. A selection records screening intent; it does not
create a paper record or claim reading/review. Screens require reasons. Subsequent
corrections append decision history, retaining the previous disposition and reason.
`dispositions_complete` describes final/deferred decisions for all recorded hits;
it is false while any hit is pending or unknown. It does not certify scientific
screening quality. `result_ids_complete` and `metadata_complete` are separate
source-coverage statements. Unknown coverage remains explicit.

A coordinator that already acquired a window centrally can import it without
another request using `crawl.save_snapshot(entries, receipt, query, ...)`.
Pass its exact `order`, `direction`, `start`, `limit`, lane and work mode, and use
`search_id` when linking a scan. The helper copies only IDs and titles from entries;
abstracts remain local. Its source receipt keeps relative `.work/` cache paths,
retrieval time, digest, HTTP status/error and `Retry-After`. Public exports must
omit ignored source contents and local cache paths.

## Historical records and local navigation

```bash
uv run python scripts/crawl.py backfill
uv run python scripts/crawl.py rebuild
```

The initial backfill contains four topic-query windows from two 2026-10-01 scans:
three from `initial-register` and one from `late-expansion`. The known-primary-ID
baseline audit is not a topic search. Backfill is idempotent and never queries
arXiv. It reads request parameters from the original URL where needed, preserves
explicit duplicate records and original scan membership, and labels missing
per-hit dispositions unknown. Registered/worked-on membership supports a
`selected` navigation record, not a reconstructed historical screen. Missing
retrieval timestamps/hashes stay null; request-time fallback to batch start is
explained in coverage limitations. All four legacy receipts retain incomplete
metadata and per-hit screening coverage, even when their IDs were registered.

`find` searches only public JSON records, with a literal case-insensitive SQLite
substring query and a bounded result limit. It searches no raw abstract, PDF,
HTML, ignored worker packet or downloaded full text. `timeline` groups registered
versions by base arXiv ID and separates source publication, source version-update
and recorded discovery dates. Bibliographic links come only from
`register/citations.json`, retaining null cited versions. Typed physical/workflow
relationships come only from `register/graph.json`. Shared topics or titles do
not manufacture links. The local index reports recorded relationships and cannot
establish citation absence, independent evidence, priority or popularity.

The search schema and `crawl.receipts()` validate strict JSON, envelope fields,
exact version IDs, positions, window digests and predecessor ordering before
index import. Retry and refresh references require the same window and compatible
predecessor status. The main register validator remains a separate repository
integrity gate. These checks establish structural consistency, not complete
search coverage, scientific usefulness, actual reading or scientific qualification.
