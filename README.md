[**Open Prospector →**](https://prospector-cosmology.sprajs.chatgpt.site)

# Prospector

Cosmology papers → physical ideas → relationships → candidate cosmologies.

Prospector finds interesting cosmologies, mechanisms, predictions and challenges,
including the Hubble tension, dark energy, geometry, acceleration and deceleration.
The public site is the main way to explore the register, follow connections and
open source papers.

A topic groups related work. A **prospect** specifies a cosmological baseline,
the ideas that change it, retained components, observables and unresolved physics.
Ideas can eventually be combined when their equations, domains and background
and perturbation closures are compatible. Topic overlap alone does not establish
that compatibility.

## Continue the research

Open this checkout in Codex and say **“run more.”** Codex resumes the saved queue,
acquires exact arXiv versions and coordinates actual subagents: `gpt-6-luna` reads
papers; `gpt-6.1-sol` checks their science, baselines and relationships. Each bounded
batch saves its evidence and updates the register and public site.

The [crawl ledger](docs/crawling.md) remembers exact search windows and every
result's disposition. Git JSON records are authoritative and accept ordinary
PRs; an ignored local SQLite index supports fast search and can be rebuilt.
No remote database or account is required. [Bibliometric snapshots](docs/bibliometrics.md)
track dated citation counts and verified author visibility separately from
scientific review. The Connections view also offers a source-publication timeline.

Read [AGENTS.md](AGENTS.md) for the procedure and [record conventions](docs/records.md)
for the scientific and provenance requirements. Source review is distinct from
independent reproduction, current-data inference and scientific qualification.

The [ΛCDM reference](docs/lcdm-reference.md) preserves the full Planck model and
its fitted-data conditioning. A separate candidate matches Reproducible's limited
massless background/conditional-BAO comparison. Its chosen controls and supplied
drag endpoint do not reproduce Planck physics or a cosmological posterior.

The [LOWZ windowed-power source target](docs/next13-lowz-source-target.md) selects
one released clustering dependency for that audit. Its covariance ordering and
galaxy-model adapter remain blocked; the existing prospect review is unchanged.

The [HyRec helium source contract](register/contracts/next15-hyrec2011-helium-analytic-source-v1.json)
separates the analytic fit, historical accuracy comparisons and later code rate
convention. Original equation-sign reconciliation and physical history remain
open. B1608 Paper I is registered with its full reading pending.

The [EDE source-parameter contract](register/contracts/ede-n3-source-normalization-initial-coordinate-closure-v1.json)
keeps the transition fraction separate from a peak. Density normalization, initial
field coordinates and the original modified CLASS implementation remain unresolved;
the independent background fluid supplies no paper EDE perturbation closure.

## Records

- [Papers](register/papers/), [ideas](register/ideas/) and [topics](register/topics/)
- [Prospects](register/prospects/), [relationships](register/graph.json) and [citations](register/citations.json)
- [Candidate investigations](designs/), [source reviews](register/reviews/) and [scan receipts](scans/)
- [Conditioned numerical references](references/)
- [Saved continuation](state.json) and [generated register](register/README.md)
- [Search windows](register/searches/) and [bibliometric snapshots](register/bibliometrics/)

Git stores metadata, links and compact original scientific notes. Downloaded
sources, extracts, images, working scripts and logs stay inside Prospector under
ignored `.work/`, `papers/` or `downloads/`. Abstracts load from arXiv on demand;
they are not included in the site artifact.

## Check and publish

```bash
uv run python -m unittest discover -s tests -v
node --test site/abstract.test.mjs
uv run python scripts/validate_register.py
uv run python scripts/build_register.py
```

Follow [contributing](CONTRIBUTING.md), [development](docs/development.md) and
[site publication](docs/site.md). Agents may review and merge ready PRs under the
owner's standing authorization, after checking the current head and base.

Prospector owns literature and prospects. [Reproducible](https://github.com/sprajs/reproducible)
owns accepted experiments and results; [Irreducible](https://github.com/sprajs/irreducible)
owns compiled science.

Shared datasets and private evidence use the [common storage layout](docs/shared-data.md).
Read the [cloud startup guide](https://github.com/sprajs/reproducible/blob/main/docs/cloud-startup.md)
for the bounded shared-catalog readiness check; Reproducible owns the startup script.
