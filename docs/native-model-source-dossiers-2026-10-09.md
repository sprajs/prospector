# Native model source and scope dossiers

This is frozen source evidence. Current scheduling follows [the sole roadmap](roadmap.md).

These dossiers connect the new compiled-model campaign to selected original
source equations. They are not full paper readings, source-author numerical
reproductions or observational qualification. No registered paper stage, graph
edge, prospect, candidate definition or research queue changes here.

The worker was explicitly launched as `gpt-6.1-sol`; reasoning effort was
omitted/inherited and is not independently recorded. Backend identity is not
exposed. Consequently these standalone dossiers do not claim the register's
explicit high/xhigh targeted-review acceptance gate. Original source identities,
checked locators and unread scope live in the
[source receipt](source-receipts/2026-10-09-native-model-source-equations.json).
Independent native-code review, numerical acceptance and repository CI remain
separate evidence, owned by Irreducible and Reproducible.

## Canonical exponential quintessence

[Copeland, Liddle and Wands, gr-qc/9711068v2](https://arxiv.org/abs/gr-qc/9711068v2),
*Exponential potentials and cosmological scaling solutions*, rendered page 2,
Table I and Eqs.6–10 were checked. For reduced Planck mass M, define
x=phi_dot/(sqrt(6) M H), y=sqrt(V)/(sqrt(3) M H), N=ln(a),
V=V0 exp(-lambda phi/M). With separately conserved dust and radiation,

    Omega_m = 1 - x² - y² - Omega_r
    epsilon = -d ln H/dN = 3x² + 3 Omega_m/2 + 2 Omega_r
    x' = -3x + sqrt(3/2) lambda y² + epsilon x
    y' = -sqrt(3/2) lambda xy + epsilon y
    Omega_r' = (-4 + 2epsilon) Omega_r

The source treats one barotropic fluid. Its dust and radiation limits support
analytic fixed-point controls; simultaneous dust/radiation is an independently
conservation-derived extension. Scalar domination gives x=lambda/sqrt(6),
y²=1-lambda²/6 and w_phi=lambda²/3-1; acceleration requires lambda²<2.
Dust scaling has Omega_phi=3/lambda²; radiation scaling has 4/lambda².
Boundary points and attractor conditions must retain their distinct domains.
Positive-potential expanding states have y>0; a zero-potential numerical boundary
needs its own scope. This is a canonical scalar model, not the separately chosen
constant-w PPF fluid and not EDE/NEDE microphysics or perturbation closure.

## Self-accelerating DGP background and quasistatic growth

[Koyama and Maartens, astro-ph/0511634v1](https://arxiv.org/abs/astro-ph/0511634v1),
*Structure formation in the DGP cosmological model*, Eq.5 and rendered page 3
Eqs.30–35 were checked, including the subhorizon/quasistatic conditions.
The flat pressureless self-accelerating branch has

    H² - H/r_c = 8piG rho_m/3
    E(a) = sqrt(Omega_m0 a^-3 + Omega_rc) + sqrt(Omega_rc)
    Omega_rc = (1-Omega_m0)²/4
    beta = 1 - 2Hr_c [1 + H_dot/(3H²)]
    delta_ddot + 2H delta_dot = 4piG [1 + 1/(3beta)] rho_m delta

Writing instantaneous Omega_m=Omega_m0 a^-3/E² gives
H_N/H=-3Omega_m/(1+Omega_m), beta=-(1+Omega_m²)/(1-Omega_m²), and
mu=2(1+2Omega_m²)/[3(1+Omega_m²)]. The Omega_m0=1 endpoint is the
infinite-r_c GR limit; beta's singular expression must not be evaluated there.
This growth law is linear, pressureless and quasistatic with k/(aH)>>1;
it is not an arbitrary-wavelength 5D solver, radiation perturbation closure,
Vainshtein calculation or GR growth evaluated on a new background.

[Gorbunov, Koyama and Sibiryakov, hep-th/0512097v1](https://arxiv.org/abs/hep-th/0512097v1),
*More on ghosts in DGP model*, title and abstract explicitly identify a ghost
around the self-accelerating cosmology. The ghost derivation was not read.
Runnable background/growth predictions cannot establish physical viability.

## Spherical untruncated NFW halo and lens

[Wright and Brainerd, astro-ph/9908213v1](https://arxiv.org/abs/astro-ph/9908213v1),
*Gravitational Lensing by NFW Halos*, Eqs.1–3,9 and rendered page 5
Eqs.10–14 were checked. For x=r/r_s,

    rho(r) = rho_s/[x(1+x)²]
    M_3D(r) = 4pi rho_s r_s³ [ln(1+x)-x/(1+x)]
    Sigma(R) = integral_-infinity^infinity rho(sqrt(R²+z²)) dz
    kappa = Sigma/Sigma_crit, gamma_t = (Sigma_bar-Sigma)/Sigma_crit
    Sigma_crit = c² D_s/(4piG D_l D_ls)

The source's M200 normalization uses critical density, not mean matter density.
An explicitly supplied rho_s/r_s law needs no inferred concentration or cosmology.
Physical and reduced deflections differ by D_ls/D_s; angular and physical radii
must remain distinct. Exact x=1 projected limits and independent line-of-sight
integrals control branch cancellation. Untruncated total mass diverges
logarithmically: do not describe it as a finite total-mass model. The source's
shear-function notation must not be confused with projected-mass notation.
This is a spherical mass/lens law, not observed halo inference, selection,
substructure, baryonic or stellar-kinematic qualification.

## Decaying pressureless matter to massless daughters

[Audren et al., 1407.2418v1](https://arxiv.org/abs/1407.2418v1),
*Strongest model-independent bound on the lifetime of Dark Matter*, rendered
physical PDF page 4 (printed page 3), Sec.2.1 Eqs.2.1–2.2 were checked.
The source uses conformal derivatives and a Gamma transfer factor. Converting
with dt=a d_eta gives proper-time conservation equations

    rho_parent_dot + 3H rho_parent = -Gamma rho_parent
    rho_daughter_dot + 4H rho_daughter = +Gamma rho_parent

A finite supplied initial anchor a_i,H_i and initial fractions define an
initial-value model. They differ from the source's present-fraction shooting
and asymptotic initial daughter boundary. Gamma/H_i is dimensionless; H_i
is inverse seconds, not an assumed present H0. For x=ln(a/a_i),
tau=H_i(t-t_i), initial parent fraction f_d and g=Gamma/H_i,

    rho_parent/rho_ci = f_d exp(-3x-g tau)
    R = (rho_daughter/rho_ci) exp(4x)
    R' = g f_d exp(x-g tau)/E, tau' = 1/E

The energy-transfer terms cancel in total continuity. Parent survival,
monotonic comoving daughter production and Gamma=0 are independent controls.
This is not the registered staged-decay daughter-quintessence coupling/EOS
proposal. Gauge-specific perturbation transfer and source observational bounds
do not transfer to a background-only finite-anchor calculation.

## Curved conserved GR FLRW geometry

[Hogg, astro-ph/9905116v1](https://arxiv.org/abs/astro-ph/9905116v1),
*Distance measures in cosmology*, rendered pages 3–4 Eqs.13–15 and extracted
Eqs.17,20 were checked. The source's Omega_R means curvature; reserve Omega_r
for radiation and write curvature Omega_k in the native contract:

    E²(z) = Omega_r(1+z)^4 + Omega_m(1+z)^3 + Omega_k(1+z)^2 + Omega_Lambda
    Omega_k = 1-Omega_m-Omega_r-Omega_Lambda
    chi = integral_0^z dz'/E(z')
    D_M = (c/H0) S_k(chi), D_A = D_M/(1+z), D_L = (1+z) D_M

S_k is sinh(sqrt(k)chi)/sqrt(k), chi, or sin(sqrt(-k)chi)/sqrt(-k).
The radiation term follows separate energy conservation; the source's
matter/Lambda formulas do not qualify radiation species or perturbations.
The early source's coordinate-dependent spatial-curvature remark is rejected;
intrinsic spatial curvature cannot be removed by changing coordinates.
Expanding light paths require positive E² throughout, not just at endpoints;
closed models stop before the first antipode. Einstein-static H0=0 is outside
this H0-normalized expanding identity. Milne, EdS, radiation and de Sitter
limits independently test geometry. No lens mass or observational data is supplied.

## Finite-mass Hernquist proposal and source access failures

Hernquist (1990), ApJ 356,359, [DOI 10.1086/168845](https://doi.org/10.1086/168845),
was proposed as a separate finite-total-mass spherical Newtonian law:

    rho(r) = M a/[2pi r(r+a)^3]
    M_enc(r) = M r²/(r+a)², Phi(r) = -GM/(r+a)

The displayed law is an explicit implementation contract, independently checked
by dM_enc/dr=4pi r²rho and dPhi/dr=GM_enc/r², not a claim that original equation
locators were read. The ADS PDF route timed out after 20 seconds; the alternate
full-text route returned HTTP202 with an empty body. Source access remains
unresolved; no equation numbers, full source reading or source-author numerical
parity are claimed. This distinct finite-mass law is not an NFW truncation.

An initial incorrect-category Copeland lookup downloaded astro-ph/9711068v2,
a different astrophotometry paper; title mismatch rejected it. DGP v2 main and
export PDF routes returned 404; verified v1 was used. These are acquisition
failures/corrections, not failures of the physical models.

## Evidence custody

Raw PDFs, extracted text and rendered source excerpts remain local because
copying rights are unverified. They are excluded from published selections;
metadata preservation does not establish raw-source preservation or permission.
Owned acquisition/failure receipts, source-equation notes and runtime receipts
are selected separately, with exact archive pins below. Full main texts,
appendices, scientific plots and ghost proof remain unread outside the named
coverage. A source check and successful compiled control cannot establish
an observational result, a cosmological posterior or generic model viability.

Published owned metadata (`research-named-manifest/v1`):

- URI: `s3://research-data-436908790672-eu-west-2/reproducible/handoffs/prospector/native-model-source-review-20261009t0158z/versions/6755d334fd803372ea14336376c6a0446f083af9c487aa0a6daa21b7588e51fa/manifest.json`
- SHA256: `a79ff9946a889a95c6867e0e5e5c77ec9b91c6765ee2aa3921d01ccfe10c91b8`
- VersionId: `FunxAcCVvU_b8.pG88ru0HWlZTam5OjM`

The uploader checked exact-version bytes for every object and published the
completion manifest last. A separate fresh-directory readback is retained in
the source handoff evidence. Raw source copying remains an explicit unresolved
custody limitation.

The separately authorized seventh Plummer finite-core follow-up uses the
original citation Plummer (1911), MNRAS 71,460, DOI10.1093/mnras/71.5.460.
Its DOI acquisition returned HTTP403; no original equation locators were read.
The explicit density/potential/projection law must therefore be described as
an independently derived implementation contract, with source parity pending.

The Plummer access-failure receipt and fresh six-file restoration verification
are separately preserved (`research-named-manifest/v1`):

- URI: `s3://research-data-436908790672-eu-west-2/reproducible/handoffs/prospector/native-model-source-followup-20261009t0202z/versions/0e20d9e6f65abaf705686d085464353dc53e17606dba735aaec38468fcf6fbf4/manifest.json`
- SHA256: `124b14a9bdce53c03885711cfa943207832135b3464a6f1686c45ddd065240cb`
- VersionId: `1HyvjSDvZRku5D7NRwG8R9mA5XiLGF_Q`

The [Chaplygin and isotropic Plummer follow-up](chaplygin-plummer-source-dossiers-2026-10-09.md)
adds selected barotropic source equations and an independently derived collisionless
population contract, preserving the original Eddington access refusal.
