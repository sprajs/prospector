# Observed portability and comparison priorities

This consumer-informed checkpoint adds no paper reading, source qualification,
graph acceptance or candidate promotion. Preserve the research queue and all
nineteen source-scope gates. Historical results retain their original identities.

## Actual consumer evidence

Reproducible PR25 merged at `df6932cf` after the actual clean, committed,
restored-input consumer gate; its exact-main CI passed. The new quick attempt
restored 50,207 bytes through selected exact-version S3 objects: 3,019 bytes of
DESI DR2 full13 means/covariance and 47,188 bytes of released CMB-redshift
header overrides. The latter is a derived redshift/velocity release product,
not raw SDSS observations or a photometric calibration likelihood. Its
SHA256 is `ffb20e03bdb65bb236802f7fac9ff4516477fd8bc947eeca321f51479a29acf8`;
source is PantheonPlusSH0ES/DataRelease commit
`c447f0fea703fcd0fff57de5000947b5ca81286b`,
`Pantheon+_Data/1_DATA/header_overrides/REDSHIFT_CMB.txt`.

The completed quick attempt manifest is:

- URI: `s3://research-data-436908790672-eu-west-2/reproducible/experiments/observational-cosmology/attempts/s3-portability-20261009t011242z-4a339d25d54d/versions/e03b5650ab666196190dfee1bad57718ecf9fed62b0f03de1a425d2917946252/manifest.json`
- SHA256: `0dc9e2739e6dff4353b943f9224da1b2126f5776d83243b9f1d1a27bf8ed8697`
- VersionId: `GKI3otD.skAKbaO4i1SBDvA14Spv.7VK`

Under the unchanged physical densities, species and fixed nuisance state, quick
conditional fits gave LCDM H0=68.833139031 km/s/Mpc and BAO quadratic
10.641051755; the explicitly chosen fixed w=-0.9 PPF branch gave
66.698450495 and 16.957094484. Broader gave 68.831349455/10.641025920 and
66.697420798/16.957078450. Both profiles use the same full13 observations,
row ordering and every covariance entry. Broader tightens optimizer resolution,
not probe coverage. These are conditional minima, not posteriors or a generic
constant-w exclusion. Planck scores remain separate DESI-selected-point scores.

Candidate SHA256 remains
`ea15c707b8bbfa53e2b50bab095f5729aec6a99334388bd0fc4cf061e0442414`,
from Prospector `99673d5ddb457732c1660a586305eb8b98de5eb6`.
CLASS `0ceb7a9a4c1e444ef5d5d56a8328a0640be91b18` and native SDK
`7a006f81a36a70cdcd3187a1298a8a1ea2cf3f39` retain their historical roles;
advancing main does not repin these experiments.

## Observed failures and next actions

| Capability | Observed failure or prerequisite | Owner | Scientific impact and next action |
|---|---|---|---|
| Numerical sensitivity | At fixed-w H0=75, changed CLASS precision shifted separate Planck score by +0.2996146, exceeding declared 0.2 budget | Reproducible | Retain failed numerical acceptance; study parameter-dependent CMB precision before larger comparisons |
| Spectrum comparison | Four common P(k) axes provide partial coverage; integration case has zero common axes and is unassessed | Reproducible | Preserve correction/refusal; define comparable grids before interpreting spectrum sensitivity |
| Attempt provenance | Sensitivity attempt 001 failed in harness before CLASS; corrected 002 preserves numerical failures | Reproducible | Retain both attempts; harness failure is not model failure |
| Calibrated SN | Raw covariance/runtime convention and calibrated residual/selection law unresolved; averaged repair separate | Prospector, Reproducible | Resolve exact matrix/caller/rank/calibrator ancestry or retain refusal; no combined SN score |
| Lensing reconstruction | Primary official likelihood and lensed CLASS spectra do not supply reconstruction likelihood | Prospector, Reproducible | Acquire exact reconstruction likelihood, response/noise/binning and dependence contracts |
| Galaxy clustering/RSD/AP/window | LOWZ covariance candidate axes match only 6/106 error-square intervals; cut map unresolved | Prospector, Reproducible | Producer axes/error/cut evidence precedes scoring; then source galaxy/nuisance/AP/window and finite-mock adapters |
| Broader inference | H0-only fixed-state target; priors and cross-probe ancestry incomplete | Prospector, Reproducible | Specify identifiable parameter/prior/calibration/dependence contract before joint inference |
| Native physics | Supplied-drag massless/native controls differ from full CLASS species/perturbations | Irreducible, Prospector | Keep approximation identities and lost scope; never substitute unsupported cosmologies |

Solver/table/interpolation sensitivity and optimizer-bracket refinement are
separate diagnostics. Empirical agreement supplies no certified aggregate error
bound. Exact transport verification does not resolve event/frame identity,
calibration, covariance or shared-object independence.
