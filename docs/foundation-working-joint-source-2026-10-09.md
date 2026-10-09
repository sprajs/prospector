# Exploratory shared-state joint source contract

This increment defines a separately named primary-CMB plus DESI DR2 working
posterior. It retains the exact restricted primary v2 candidate, reference,
physics and normalized seven-coordinate prior. One CLASS state supplies all
three official primary likelihoods, distances and predicted comoving drag
ruler. The full13 DESI mean and covariance are used in released order, including
the final Lyalpha DH then DM pair. There are no additional extractor alpha,
damping, foreground, calibration or fitted-summary prior factors.

The new [candidate](../designs/candidate-class-planck-primary-desi-exploratory-v1.json)
contains a strict `working_joint_contract`. It binds both immutable primary
artifacts by canonical identity, path, length and SHA256 and copies their entire
consumer semantics. CLASSy returns angular distance in Mpc and Hubble rate H/c
in inverse Mpc: DM=(1+z)DA, DH=1/H_CLASS, and
DV=(DM² z/H_CLASS)^(1/3). Each distance is divided by the same-state rs_drag.
The fixed full Gaussian BAO factor includes its quadratic, log determinant
and 13 log(2pi) normalization; the official primary conventions are retained.

The [joint contract](../register/contracts/foundation-exploratory-primary-desi-joint-v1.json)
declares cross-probe block factorization as an exploratory project approximation.
Planck VI Sec5.1 and DESI cosmology SecIV.2/V provide evidence of adopted joint
CMB+BAO analyses, with different source targets. The checked sources do not
provide an empirical cross-covariance bound for our exact primary/full13 pair.
Shared large-scale structure, late ISW, primary lensing smoothing, sky/foreground
and extraction ancestry remain possible dependence channels. Source Planck
fiducial ancestry supplies no extra likelihood factor.

Same-prior Commander omission, separate-probe comparisons and BAO tracer
leaveouts are predeclared robustness checks. They do not measure covariance
zero. Numerical support, precision, convergence, predictive and prior-boundary
checks remain consumer responsibilities. This source increment permits review
of a real simultaneous working fit; it does not certify cross-probe independence,
calibrated tension or absolute evidence, or complete M2 dependence qualification.
Historical blocked contracts remain unchanged.

The [supernova contract](../register/contracts/foundation-relative-and-calibrated-sn-working-v1.json)
keeps relative Pantheon+, calibrated SN-alone and future calibrated compatibility
stress fits distinct. Exact restored producer callers and table give:

| Factor | Source selection | Rows | Mean for flagged calibrators |
| --- | --- | ---: | --- |
| Relative Pantheon+ | zHD>0.01 | 1590, including10 flags | Cosmological distance plus M |
| Calibrated Pantheon+SH0ES | zHD>0.01 OR IS_CALIBRATOR | 1657, including77 flags | Released CEPH_DIST plus M |

Relative selection removes67 low-redshift flagged rows from the calibrated
selection; removing every flagged row would change the producer selection.
For cosmological rows the producer mean is
5 log10[(1+zHD)(1+zHEL) DA(zHD)/Mpc]+25+M. Thus a luminosity-distance call at
zHD alone needs the observer-frame factor (1+zHEL)/(1+zHD). The new working
consumer can use direct official CLASS angular_distance at each zHD, with its
own frozen interpolation/refinement policy. The inherited CosmoSIS interpolation
and GaussianLikelihood inversion policies remain unknown reproduction limits.

Both callers use the released full selected STAT+SYS covariance once. Its
README states that Cepheid-host systematic covariance and CEPH_DIST uncertainty
are already included. A calibrated working factor must not append Riess H0,
a calibrated-M Gaussian, diagonal errors or copied host-modulus uncertainties.
M is a proper normalized project uniform[-21,-17] mag in dM, with boundary checks.

The separately named covariance approximation is Cs=(C_selected+C_selectedᵀ)/2,
with an exact arithmetic/byte identity and no jitter or clipping. The original
nonsymmetric covariance and its full389/calibrated-selected361 asymmetric-pair
refusal remain unchanged. Symmetrization is not proven producer reproduction
or rounding repair. SPD/order checks, upper/lower symmetric completions and
actual CLASS residual/tail sensitivity are required separately for1590 and1657
selections. Existing calibrated engineering controls do not qualify relative
selection or posterior tails, and asymmetry alone does not bound missing
symmetric systematic errors.

Brout SecIV.4 explicitly excludes SH0ES from its Planck combinations because
the authors judge them incompatible; its reported evidence ratio belongs to
its own model, priors and data. Relative Pantheon+ is the natural next joint
baseline. A separately named primary+DESI+SH0ES exploratory compatibility-stress
posterior remains available to expose tension with per-factor diagnostics;
incompatibility is an interpretation warning, not a mathematical prohibition.
The paper's81 calibrator light curves versus serialized77 flags is retained as
an unresolved serialization difference.

[Selected source evidence](source-receipts/2026-10-09-foundation-working-joint-source.json)
records exact custody pins, coverage, means, selections and limitations. This
is a targeted original-source review with zero new ordinary full-paper reads
or paper admissions. Raw papers and caller bodies remain excluded from Git;
existing privately pinned source custody is reused. No solver, covariance
factorization, likelihood or sampler was run by this source worker.
