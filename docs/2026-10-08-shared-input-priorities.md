# Historical shared-input portability checkpoint

Current scheduling is superseded by [the sole roadmap](roadmap.md). Git at
`b4384c539652e7e7b6e5a426a13ce542347e0321` preserves the earlier plan text.

2026-10-08 source and interface checkpoint. The existing measured comparison
remains historical scientific feedback; this checkpoint recorded the then-current
dependency and test priorities. It introduces no new paper reading, numerical result or S3
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

## Current routing

The earlier runtime/input-root follow-up plan is superseded by the roadmap.
The subsequent restored-input evidence below retains its separate attempt
identity; exact source review, numerical acceptance and observational gates
remain as documented.

Reproducible owns accepted experiments and results; Irreducible owns compiled
physics. Source review, exact-version transport checks, numerical acceptance and
scientific qualification remain separate gates. This checkpoint changes no
scientific readiness or public Site deployment.

The [observed 2026-10-09 checkpoint](2026-10-09-observed-portability-priorities.md)
records the subsequent real restored-input run and remaining numerical failures.
