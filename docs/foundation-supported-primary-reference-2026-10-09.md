# Restricted primary reference v2

[Candidate v2](../designs/candidate-class-planck-primary-six-parameter-v2.json) and
[reference v2](../references/lcdm/class-planck-primary-six-parameter-v2.json) specify
a separately named, conditional project target. The model, six cosmological
coordinates, H0-flat measure, nonnegative Lambda support and official primary
likelihood components remain those of v1. The intended prior now has these bounds:

| Coordinate | Uniform bounds or calibration support |
|---|---|
| omega_b | [.018,.028] |
| omega_cdm | [.08,.18] |
| H0, km/s/Mpc | [50,90] |
| logA = ln(10^10 A_s) | [2.8,3.3] |
| n_s | [.92,1.03] |
| tau_reio | [.02,.10] |
| A_planck | N(1,.0025) in dA_planck, truncated to [.975,1.025] |

The calibration density is normalized by `Phi(10)-Phi(-10)` and applied once.
For this v2 box, max(omega_b+omega_cdm)=.208 and min(h²)=.25 leave a
.042 margin, while the conservative fixed photon/neutrino density bound is below
.001. The Lambda predicate is redundant throughout this box: the six uniform
cosmological densities remain independent and properly normalized, and the extra
conditioning factor is one. Keep exact runtime background closure verification;
a violated bound requires refusal and inspection of the implementation. These bounds are investigator choices
motivated by released table availability, reviewed with Astra and authorized by
the integration owner. They are not the Planck source prior or recovery of the
broader v1 posterior. Prior-boundary and supported expanded-prior sensitivity are
required before scientific claims about broader support.

The [source packet](source-receipts/2026-10-09-foundation-supported-primary-source.json)
pins Commander dispatch, calibration metadata, Gaussianization source and
`sigma.fits`. Its source checks distinguish a calibrated Dl range refusal from a
nonpositive interpolation derivative. The saved-vector witness identifies the
v1 failure: at ell22, calibrated Dl=2421.2311414262 microkelvin² exceeds the
released upper2343.0496262589, before spline evaluation. The v1 artifacts remain
byte-identical. The first never-frozen restricted proposal also failed SimAll at
ell4; its index3110.10 exceeds the table support[0,3000). Both failures remain
visible, with no clipping or physical-prior reinterpretation.

Consumer reports of finite amplitude/tilt/tau and density/H0 diagnostic points
motivate attempting this v2 qualification. They do not prove whole-domain
support, numerical precision or posterior convergence. The candidate remains
blocked, executable request null, and numerical/scientific qualification false.
Reproducible must accept the exact new bytes before domain qualification and
inference; future unsupported states still require explicit refusal.

Five owned follow-up note packets, including Commander support, DESI fiducial
and template limitations, calibrated SN producer semantics and the exact eleven
source-family readiness snapshot, have [persistent custody](source-receipts/2026-10-09-source-owner-notes-custody.json).
They were freshly restored and compared byte for byte. Raw papers, copied source
code and data were excluded; local originals remain. This transport preserves
unfinished work and confers no scientific admission or redistribution rights.
