# Bibliometric sidecars

`register/bibliometrics/<arxiv-id>vN-<snapshot-id>.json` records descriptive citation and
author-visibility observations alongside, and separately from, scientific
paper records. These fields are not measures of scientific truth, novelty,
quality, or usefulness. Paper reading, source review, and candidate status
remain in their existing records.

## Citation snapshots

The initial adapter uses the [INSPIRE-HEP REST API](https://github.com/inspirehep/rest-api-doc)
with one exact arXiv-ID lookup per paper. A snapshot records the requested URL,
UTC retrieval time, HTTP status, response SHA-256 and byte count. The raw response
is retained under ignored `.work/`; Git holds the compact record and a relative
archive path. Fetching is constrained to `.work/` for raw responses and
`register/bibliometrics/` for public sidecars before the request or write occurs.
A failed or missing provider value remains `null` with a reason.
An observed count of zero is stored as integer `0`.

INSPIRE returns a record for the base arXiv work. The sidecar therefore declares
that its count covers the provider's base-work record and that versions are not
disaggregated. Registering another arXiv version must not be counted as another
work in a citation cohort. Snapshots are append-only: each retrieval gets a
new creation-time-and-content-hash filename, and validation recomputes that ID
from the full payload; discovery chooses the latest snapshot
for the exact paper version and provider while retaining prior observations.
Both the provider's total count and its reported
count without self-citations are retained as separate provider fields.

## Age-aware cohorts

Each sidecar computes age from the registered first-submission timestamp to the
provider retrieval time. The comparison key is exact: provider, explicitly
shared snapshot-batch ID, stated field definition, and a half-open one-year
publication-age band `[n, n+1)` by default. The band width is carried by its
boundaries, so validation checks the actual declared width and accepts a narrower
band when its boundaries are consistent. Here the field label is the paper's primary
arXiv category; it does not claim that a category is a complete field taxonomy.
The one-year band is coarse: two papers in one band can differ in age by almost
a year. `age_band(..., width_years=...)` accepts narrower bands, though those
make adequate populations harder to collect.

The adapter does not infer percentiles from this deliberately selected register
sample. A future empirical percentile needs an explicitly defined provider
query population, an archived response with its hash and returned work IDs, at
least 100 unique peer works, observed counts, and an exact match on all cohort
key fields. The 100-peer floor is an operational policy, not a validated
scientific threshold or a guarantee of small percentile error. Duplicate provider work IDs are collapsed across registered
versions; conflicting duplicate counts are rejected. Missing counts are omitted
from the peer population, never changed to zero. Percentiles use a tie-aware
midrank and remain null below the minimum population.

## Google Scholar author metrics

There is no automated profile search in the script. A manually inspected public
profile can be entered only with its exact URL and evidence that the profile is
the paper author: the profile must show the exact work and the name/identity
must be unambiguous. Provider author attribution is unresolved when the same
normalized name maps to multiple linked author records. A name-only match,
third-party profile directory, or search
snippet is not enough. If the page cannot be inspected, the profile is
ambiguous, or the metric is absent, keep `h_index` null and state why.

Every h-index observation needs its profile URL, retrieval time, metric scope,
identity evidence, and any career window shown by the profile. Career length,
field citation rates, publication volume, author disambiguation, profile
curation, and database coverage all affect interpretation. These values are
therefore source- and snapshot-specific, and cross-field comparisons are
descriptive only.

For a paper's author team, `max_h_index` and `median_h_index` are computed from
unique authors with verified identities and observed profile metrics. The
sidecar reports the number measured, number of listed unique authors, and
coverage fraction. It never sums h-indices. Incomplete coverage leaves the
team result marked partial; zero measured profiles yields null max and median.
Missing author metrics do not imply low visibility or low scientific value.

## Discovery filter

The filter only considers papers already marked reviewed, with a review ID and
registered ideas. It puts a paper in `low_visibility` only when every unique
paper author has a verified, observed Google Scholar h-index and the team maximum
is strictly below the requested threshold. Reviewed papers with missing or
partial metrics are returned separately as `unresolved_visibility`; incomplete
coverage cannot qualify as low visibility. Other statuses can be included for
inspection with `--include-other`.

```bash
uv run python scripts/bibliometrics.py fetch-inspire register/papers/1811.04083v2.json --batch-id inspire-example-batch
uv run python scripts/bibliometrics.py validate
uv run python scripts/bibliometrics.py discover --threshold 10 --profile-batch-id scholar-example-batch
```

`fetch-inspire` performs one work lookup per invocation. A shared batch ID is
only appropriate when collecting a deliberately bounded set close enough in
time to treat as one provider snapshot window. Discovery requires all author
metrics to come from the same declared Google Scholar batch and the same
all-time scope. The script does not crawl author coauthors or use selected
prospects as a percentile population.

## Initial bounded sample

The five initial work snapshots were chosen from three already registered
papers and two queued recent papers, spanning different publication ages and
arXiv categories. INSPIRE returned exact base-ID/title matches for all five.
The selected sample is not a sampling frame, so all percentiles remain null.
Google Scholar did not provide a usable profile observation in this initial
sample: one profile linked from the author's institutional research-group page
returned HTTP 429 when opened, and no retry was made. Accordingly, every team
visibility aggregate remains null with zero h-index coverage. This is
unresolved author-metric coverage, not evidence that these authors have low
visibility.
