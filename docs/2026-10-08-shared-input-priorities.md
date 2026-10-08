# Shared input portability and next comparison priorities

2026-10-08 source and interface checkpoint. The existing measured comparison
remains the scientific feedback; this checkpoint records the next dependency and
test priorities. It introduces no new paper reading, numerical result or S3
verification.

## Source and runtime status

The audited Prospector source is
`dc19ee04a003e32270a16c30d2de5efeb3bae324`. Its exact-main
[Register integrity CI](https://github.com/sprajs/prospector/actions/runs/37861074790)
passed. The coordinated runtime failed with `vpn_enrollment_failed` before a
shell became available. AWS binding configuration was available, but its identity,
catalog and exact-version reads were inaccessible in that runtime. Zero compiler
or compute jobs were allocated; configured storage is not verified readiness.

At Reproducible
[`c64f052f5f347f7c554c4cae8adcd89442eaba07`](https://github.com/sprajs/reproducible/blob/c64f052f5f347f7c554c4cae8adcd89442eaba07/experiments/observational-cosmology/controller.py#L373),
the observational controller reads BAO inputs from repository `ROOT` at intake
and [terminal drift checking](https://github.com/sprajs/reproducible/blob/c64f052f5f347f7c554c4cae8adcd89442eaba07/experiments/observational-cosmology/controller.py#L451).
It exposes no separate input root. Restoring an exact manifest into a new directory
therefore does not yet provide this controller an explicit input route.
Reproducible owns the proposed `--input-root` repair and its acceptance checks;
this source observation does not certify that repair or a restored execution.

Use the [canonical startup route](https://github.com/sprajs/reproducible/blob/main/docs/cloud-startup.md)
and [shared storage contract](shared-data.md). Keep the verified catalog-release
pin, then select the input manifest URI, SHA256 and exact VersionId. Restore into
a new directory and retain source, candidate, runtime and original attempt
identities separately. Never select an entire bucket or treat its discovery
pointer as a scientific pin.

## Preserve the measured feedback

The [existing execution feedback](../register/feedback/conditional-lcdm-constant-w-execution-20261008-v1.json)
records the broader conditional H0 values 68.831349 for flat LambdaCDM and
66.697421 km s^-1 Mpc^-1 for the chosen w=-0.9 PPF fluid, with BAO quadratics
10.641026 and 16.957078. The fluid branch is worse by about 6.31605 under the
fixed physical state. These are historical consumer results, not measurements
from this checkpoint. Its exact consumer account and historical hashes retain
their original role.

Primary-CMB scores remain separate evaluations at DESI-selected points.
There is no joint posterior, separate lensing likelihood or generic constant-w
exclusion. The original SN raw-covariance/runtime refusal and the separate averaged
working repair remain distinct. Preserve the immutable candidates, all 63 queued
paper entries and all nineteen source-scope gates.

## Next bounded work

1. After runtime recovery and input-root acceptance, restore the selected exact
   input manifest and run a new quick LambdaCDM control with explicit restored
   paths and unchanged scientific pins. Compare its retained outputs with the
   historical control; preserve any refusal and the new attempt identity.
2. Specify a separate changed-parameter target with an explicit baseline,
   retained sectors, finite coordinates and bounds. Test declared solver precision
   sensitivity separately from optimizer-bracket refinement before expanding
   model comparisons. Neither numerical diagnostic supplies an uncertainty interval.
3. Review source multi-coordinate inference, prior and dependence conventions
   before interpreting a broader alternative. Keep the chosen PPF fluid distinct
   from scalar microphysics, EDE, NEDE and timescape.
4. Continue the separate SN covariance/runtime and calibrated residual/selection
   source target. For lower-level clustering, first resolve the
   [LOWZ covariance axes, error semantics and cut map](next13-lowz-source-target.md),
   then admit the galaxy/RSD/AP/window and finite-mock statistical adapters.
   A matter spectrum alone is not a galaxy likelihood; shared observations and
   unknown cross-covariance cannot be counted as independent probes.

Reproducible owns accepted experiments and results; Irreducible owns compiled
physics. Source review, exact-version transport checks, numerical acceptance and
scientific qualification remain separate gates. This checkpoint changes no
scientific readiness or public Site deployment.
