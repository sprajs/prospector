# Prospector

Prospector is a **Codex-led register of cosmology prospects**: papers, physical
ideas and predictions worth investigating. It covers new cosmologies, the Hubble
tension, acceleration and deceleration, dark energy, modified gravity, early
physics and alternatives in measurement or calibration.

**Luna reads the papers. GPT-6.1 Sol checks the science and overlap.** The register
keeps their sources, assumptions, useful predictions and unresolved questions.
A common signature is not proof of equivalent physics, and repeated fits to
shared observations are not independent evidence.

## Explore

- [Prospect register and browsing tree](register/README.md)
- [Interactive prospect map](register/map.html)
- [Papers](register/papers/), [ideas](register/ideas/), [prospect groups](register/prospects/)
  and [scientific reviews](register/reviews/)
- [Candidate investigations](designs/) and [scan records](scans/)

Prospects group papers by question and mechanism. The tree is a browsing view;
[typed graph relationships](register/graph.json) preserve overlap, specialization,
physical differences, criticism and shared observations. Papers may contain
several ideas and belong to several groups. Records show what was discovered,
screened, read and reviewed; metadata hits are never presented as full reads.

## Run the next batch

Open this repository in Codex and say **“run more.”**

Codex resumes the [saved queue](state.json) and searches arXiv through its
structured Atom API. A normal batch admits up to 20 new versions, reads up to
6 papers with `gpt-6-luna` and sends up to 3 useful papers to exactly
`gpt-6.1-sol` for deeper review. Actual work may be smaller. Each batch updates
the register, graph, map, scan records and queue.

[AGENTS.md](AGENTS.md) is the working procedure. Models are selected explicitly
at spawn; [project defaults](.codex/config.toml) are optional session configuration.
This is an agent-operated workflow with small acquisition and record tools.

## From a prospect to a scientific run

**Prospector → [Reproducible](https://github.com/sprajs/reproducible) →
[Irreducible](https://github.com/sprajs/irreducible).**

Prospector owns discovery, the idea graph and candidate-design JSONs.
Reproducible owns accepted experiment designs, inputs, runs and results.
Irreducible provides compiled models and accepted calculation requests.
Missing physics requires source development before a design can execute.

Candidate designs state the exact claim, a simpler test, its lost scope and its
blockers. They are not executable recipes. Source review, execution and
scientific qualification remain separate stages.

## Storage and maintenance

Git contains metadata, version links, hashes and short original notes. Full
papers, HTML, extracted text, renders and agent working files are saved **inside
this repository under ignored `.work/`, `papers/` or `downloads/`**. See
[record conventions](docs/records.md).

```bash
uv sync
uv run python -m unittest discover -s tests -v
uv run python scripts/validate_register.py
uv run python scripts/build_register.py
```

The builder regenerates the register and map from canonical JSON. Validation
checks record shape, references and promotion gates; it cannot certify science.
Follow [contributing](CONTRIBUTING.md) and [development](docs/development.md)
for repository changes and publication.

For a bounded metadata request, the acquisition helper saves responses and
receipts under the specified ignored batch directory:

```bash
uv run python scripts/arxiv.py 'cat:astro-ph.CO AND ti:quintessence' \
  --work .work/scans/my-batch --limit 10 --order lastUpdatedDate
```

It supplies sources to Codex readers. Admission, reading, scientific review and
integration follow AGENTS.md; the helper does not perform those stages.
