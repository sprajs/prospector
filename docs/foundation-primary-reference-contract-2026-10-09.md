# Fully varied primary reference source contract

M0 now has a new [candidate](../designs/candidate-class-planck-primary-six-parameter-v1.json),
[source reference](../references/lcdm/class-planck-primary-six-parameter-v1.json),
[probe contract](../register/contracts/foundation-primary-and-joint-contract-v1.json)
and [immutable handoff](../handoffs/foundation-primary-reference-v1.json).
They specify an H0-flat CLASS six-cosmological-coordinate plus shared-calibration target.
Consumer numerical acceptance and posterior reproduction remain open. Existing Table2,
fixed-helium, massless/supplied-drag and conditional-H0 identities are preserved.

| Item | Frozen choice and source limit |
|---|---|
| Cosmological coordinates | `omega_b,omega_cdm,H0,logA,n_s,tau_reio`; `A_s=exp(logA)*1e-10`. Uniform project bounds are `[.01,.035],[.05,.25],[40,100],[1.61,3.91],[.8,1.2],[.01,.14]`. Only the amplitude range is checked in Planck VI Sec2.1; these are not the source theta_MC priors. |
| Physical support | Nonnegative Lambda after actual photon, massless and massive density closure. The prior is the product of box densities times this explicit indicator, so conditioning couples cosmological coordinates. The conditioning normalization is uncomputed; posterior ratios are defined, evidence normalization is unqualified. |
| Species | T_CMB2.7255K, one0.06eV effective FD pair, native g2/CLASS degeneracy1, T_ncdm/T_CMB0.71611, zero chemical potential. `N_ur=3.046-(.71611/(4/11)^(1/3))^4=2.0327983725164924`. Exact nonthermal CAMB equivalence is unproved. |
| Helium | Vary `YHe=BBN` through explicit `external/bbn/sBBN_2017.dat`, SHA256 `b72607a3a2f9134130cb2c09c0140d4f68c5916962e83fc6740a664bd5b69ea5`. Its header declares PArthENoPE1.2/neutron880.2s; Planck VI declares1.1. The external CLASS key is **`sBBN file`**, verified through `macros_precision.h`; `sBBN_file` is the internal member name. |
| Early and nonlinear physics | Scalar adiabatic power law at0.05Mpc^-1, zero running/tensors; HyRec2020 and `reio_camb` with varied tau. Explicit `hmcode_version=2016`, dark-matter emulator feedback. The source parser accepts2015/2016 aliases into enum2015 and includes Mead2016 neutrino corrections; its error message lists fewer aliases. No equivalence to the historical Halofit point is claimed. |
| Primary products | Commander TT2–29, SimAll EE2–29, Plik-lite TT30–2508 and TE/EE30–1996. Theory spectra are lensed; no reconstructed-lensing likelihood is included. Use exact runtime vector maxima and nuisance ordering, Cl in microkelvin², and released constants. |
| Calibration | A_planck is the shared map-level y_P convention: official code divides theory by A_planck². Gaussian1±.0025 in dA_planck is applied once, truncated/normalized on the project bounds[.9,1.1]. Full container/runtime prior ownership is rechecked by the consumer. |
| Foregrounds | Plik-lite already marginalizes20 secondary nuisance parameters, including frequency calibration. Append neither their priors nor full Plik. Planck V reports<0.1sigma agreement for six-parameter LCDM; this is author validation, not our reproduction. |
| Likelihood support | SimAll requires every calibrated EE multipole to lie inside its released table. Check its native float32 step and operation order before the unsafe lookup. Unsupported table states and numerical failures are explicit refusals, never an undisclosed zero-density prior cut. Qualify the intended prior or stop/repair/freeze a new restricted target. |

The [targeted review](../register/reviews/2026-10-09-foundation-primary-source-claims.json)
records original hashes, complete selected sections, captions-only figure coverage,
unread scope and requested Sol/high provenance. No ordinary Luna reading stage was
filled. At source-review base `16b25a9b6bc6f3a80335161ff2e98fc83619f8fe`,
the register contained 71 papers and 63 pending stages; this audit preserves that
snapshot. See the [current register](../register/README.md) for live counts after
other lanes' subsequent admissions. Fresh Planck V HTML differs
from the historical receipt by235bytes; both hashes remain. The old bytes were not
restored for a content diff. Raw copied sources have unresolved redistribution
rights and stay ignored locally, excluded from Git and S3.

Planck V Eq38 and official clik code divide theory by y_P². Its printed Eq54 places
that division on data instead. The mismatch is recorded explicitly; the target
uses the official implementation convention rather than silently reversing the
parameter or rescaling covariance. Planck VI Sec7.8's corrected high-redshift
reionization limits and section-specific Gunn-Peterson cut were read but are not
imported into the baseline prior.

DESI DR2 full13 is a prospective first joint subset. Its exact released mean and
169-entry covariance retain BGS DV, six anisotropic pairs and the final Lyalpha
DH-then-DM order; LRG3+ELG1 supersedes individual rows. Galaxy/quasar measurements
use IterativeFFT reconstruction and nuisance-marginalized fiducial templates;
Lyalpha has a separate four-correlation fit. The checked source tests flat LCDM,
but numerical reconstruction/fiducial details and companion validation need further
checking. Its own CMB baseline uses PR4 CamSpec plus Planck+ACT reconstruction,
which differs from this reference. No quantitative justification for negligible
primary-CMB/BAO cross-covariance was located in the checked sections. AppendixB's
interbin BAO-systematic test is a different issue. **Joint admission remains blocked**;
separate primary and DESI targets can proceed through their own gates.

All11 shared dataset families are being independently checked by the data owner.
Custody, usable bytes, producer semantics and physical likelihood admission are
separate results. The fresh SN structural check retains389 full and361 selected
asymmetric pairs; the original covariance remains refused. A symmetrically averaged
working matrix is a separate target and requires producer/caller semantics.
Pantheon+/SH0ES shared calibrators, training and calibration products cannot be
added as independent observations. No broader data-readiness claim is made here.

The source packet has a fresh verified catalog pin after a retained initial CLI
PATH failure. Eligible owned notes may be preserved; raw source rights are still
open. Consumer execution must accept exact candidate/reference/contract bytes,
record actual source/build/restored-data identity and keep source agreement,
numerical acceptance, likelihood reproduction and interpretation separate.
