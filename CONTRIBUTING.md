# Contributing

Help turn interesting cosmology papers into traceable candidate investigations.
Source corrections, careful reading, useful overlap distinctions, negative findings
and clearer handoffs are welcome, including work written with agents.

Prospector owns literature discovery, exact paper/version provenance, original
notes, idea relationships and candidate designs. Reproducible owns experiment
designs, runs and plots; Irreducible owns scientific models and numerical code.
A reviewed paper is not an independently reproduced or scientifically qualified
result. Preserve this distinction in every record and PR.

Work on a branch and open a coherent PR. Agents use `codex/` branches. Keep useful
checkpoint commits and push branches promptly for backup, including before a PR
or handover. Requested repository changes should finish as reviewable PRs; split
unrelated changes and explain dependencies. A large coherent change is welcome.
Describe the problem, resulting behavior, source coverage and checks actually run.

The owner authorizes agents to review their own PRs in a separate deliberate
pass and merge ready changes without another confirmation. Inspect the final
diff, fix actionable findings and require green applicable CI on the latest
integrated head and up-to-date base. A separate human reviewer is not required;
scientific qualification and independence still need their own evidence.
Do not push directly to `main` or force-push without a specific request. Literature
search or batch authorization does not authorize an endless search, numerical
experiment, scheduled automation or external message.

Downloaded papers, HTML, full-text extractions, screenshots and worker logs stay
in ignored local storage. Publish descriptive provenance and short original notes.
Record exact versions, source hashes and reading coverage; access failures and
unread sections remain visible. Public access does not grant redistribution
rights. Repeated fits to shared observations are not independent evidence.

Follow the scientific working instructions in [AGENTS.md](AGENTS.md) and the
[development workflow](docs/development.md). Where record schemas/validators are
implemented, run their current checks and explain their structural limits. Never
invent files, implemented features, reading coverage or validation success.

Contribute ordinary JSON and short original notes through PRs; no shared
database credentials are needed. Search windows and per-result decisions live
in `register/searches/`; dated citation/author-visibility snapshots live in
`register/bibliometrics/`. Verify identities and preserve unknown values and
earlier snapshots. Physical connections still require located source evidence
and scientific review. Rebuild the ignored SQLite index with
`uv run python scripts/crawl.py rebuild` after changing public records.

You can propose a connection between existing nodes as a `provisional` edge
with a rationale and exact paper locators, or contribute a corrected paper
identity, search screen or explicit bibliography link. Mark what you actually
checked and keep unread material visible. New mechanisms can first be proposed
in reading packets; acceptance into the reviewed idea graph follows the source
review gates in AGENTS.md. Contributor PRs need no access to the local database
or ignored paper cache.
