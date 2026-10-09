# Chaplygin background and isotropic Plummer source dossiers

This follow-up to the [native model dossiers](native-model-source-dossiers-2026-10-09.md)
checks selected source equations and declares independent physical derivations.
It adds no full paper read, registered paper stage, graph edge or candidate
promotion. Requested worker model was `gpt-6.1-sol`; launch reasoning was
omitted/inherited and remains independently unrecorded. These standalone notes
do not claim the register's explicit high/xhigh source-review acceptance gate.
Exact source and failure metadata are in the
[receipt](source-receipts/2026-10-09-chaplygin-plummer-distribution.json).

## Generalized Chaplygin gas

Bento, Bertolami and Sen,
[*Generalized Chaplygin Gas, Accelerated Expansion and Dark Energy-Matter Unification*,
gr-qc/0202064v1](https://arxiv.org/abs/gr-qc/0202064v1), was acquired from its
pinned original PDF route. Its title, authors, arXiv version watermark, rendered
page 1 Eq.1 and page 2 Eqs.12–13 were checked. PDF SHA256 is
`0e246430a70015a450f4994cecef6f748272295f9e7a77523358f9419362aa04`,
173,794 bytes. Remaining main text, appendices, figures and microphysical or
perturbation arguments were not read or qualified.

The selected source equation is a barotropic pressure law and its homogeneous
continuity solution:

    p = -A/e^alpha
    de/dt + 3H(e+p) = 0
    e(a) = [A+B/a^(3(1+alpha))]^(1/(1+alpha))

Here e is energy density and p has the same units, using c=1. The source writes
rho for e. A has units [energy density]^(1+alpha); its numerical value therefore
cannot be carried between different alpha values as if it were dimensionless.
The source explicitly uses A>0 and 0<alpha<=1. Its Eq.1 first introduces alpha=1;
page 2 Eq.13 supplies the generalized continuity solution.

For the independently declared finite anchor a=1, define
A_s=A/e_anchor^(1+alpha), with the chosen nonnegative interpolation branch
0<=A_s<=1. Then

    X(a) = A_s + (1-A_s) a^[-3(1+alpha)]
    F(a) = e(a)/e_anchor = X(a)^[1/(1+alpha)]
    w(a) = p/e = -A_s/X(a)
    dp/de = -alpha w(a)
    E(a)^2 = Omega_dust a^-3 + Omega_rad a^-4 + Omega_cg F(a)
    Omega_cg = 1-Omega_dust-Omega_rad

This is a flat homogeneous GR fluid with separately conserved ordinary dust and
isotropic radiation. Native anchor H is in km/s/Mpc; supplied dust/radiation
fractions are at that anchor. The generalized fluid replaces its own sector;
it does not erase ordinary dust or radiation by calling all matter Chaplygin gas.
Its past-domain initial values and fractions do not reproduce a source-author
fit or a primordial perturbation state.

Independent controls include A_s=0 dust, A_s=1 constant density, alpha=1 ordinary
Chaplygin gas and alpha=0 constant-pressure background
F=A_s+(1-A_s)a^-3. A_s=0 and alpha=0 are explicitly mathematical extensions to
the source's positive-A, positive-alpha domain. The alpha=0 background matches
a dust-plus-Lambda expansion decomposition but does not establish equivalence
of perturbations, entropy or microphysics. The derivative dp/de is dimensionless
in this convention; an SI speed-squared would require a factor c^2 and an earned
perturbation/rest-frame contract. In particular, w=-1 does not supply an ordinary
propagating fluid rest frame. No sound-mode, Born–Infeld action, structure-growth,
CMB, ruler or observational qualification follows from this background law.

## Isotropic collisionless Plummer population

The historical inversion citation target is Eddington (1916), MNRAS 76,572,
[DOI10.1093/mnras/76.7.572](https://doi.org/10.1093/mnras/76.7.572).
Its DOI route returned HTTP403; the lawful alternate ADS original-PDF route
timed out after 20 seconds. No original title metadata, equation locator or
paper text was verified. The following is an independent calculation for an
explicit self-gravitating Plummer density, not an original-source reproduction.
The earlier original Plummer-source access refusal remains unchanged.

The model is stationary, spherical, collisionless and velocity-isotropic.
Its one-component density supplies both mass and tracer weight. Use SI total
mass M (kg), scale b (m), supplied G (m^3 kg^-1 s^-2), native gravitational
potential Phi (m^2 s^-2), and relative potential Psi=-Phi with Phi(infinity)=0:

    Psi(r) = GM/sqrt(r^2+b^2)
    rho(r) = 3Mb^2/[4pi(r^2+b^2)^(5/2)] = C Psi^5
    C = 3b^2/(4pi G^5 M^4)
    epsilon = Psi - v^2/2

The population consumer must reuse the compiled Plummer potential/density and
their numerical diagnostics. A separately reimplemented potential is not an
independent test of the retained gravity owner.

For an isotropic mass phase-space density f(epsilon), velocity integration gives
the Abel relation and its independently applied inversion:

    rho(Psi) = 4sqrt(2) pi integral_0^Psi f(epsilon) sqrt(Psi-epsilon) d_epsilon
    f(epsilon) = [1/(sqrt(8) pi^2)] integral_0^epsilon rho''(Psi)/sqrt(epsilon-Psi) d_Psi

The usual endpoint derivative term vanishes here because rho'(0)=0. Since
rho''=20C Psi^3 and B(4,1/2)=32/35, direct integration yields

    f(epsilon) = [24sqrt(2)/(7pi^3)] b^2/(G^5 M^4) epsilon^(7/2), epsilon>0
    f(epsilon) = 0, epsilon<=0

Specific binding energy has units m^2/s^2. f has units kg s^3/m^6.
At a fixed radius, f/rho is the velocity-vector probability density (s^3/m^3),
and 4pi v^2 f/rho is the speed probability density (s/m). These are different
measures. Physical speeds obey 0<=v<sqrt(2Psi), and bound energy cannot exceed
Psi(r), whose global maximum is GM/b. Numerical support must use the retained
potential/energy diagnostic: an interval straddling zero is an unresolved
support case, not permission to clamp epsilon or silently choose a bound state.

An independent velocity Beta integral recovers rho and gives the radial
one-component variance sigma_r^2=Psi/6. The same result follows from the isotropic
stationary Jeans equation. Native Plummer projection supplies
Sigma(R)=Mb^2/[pi(R^2+b^2)^2]. The line-of-sight second-moment numerator is

    integral_-infinity^infinity rho sigma_r^2 dz = [3GM^2 b^2/64] (R^2+b^2)^(-5/2)

Dividing by Sigma gives the projected **mass-weighted** variance
sigma_los^2(R)=3pi Psi(R)/64. This is not measured luminosity-weighted stellar
kinematics unless an explicit tracer/mass-to-light contract earns that mapping.
No Gaussian approximation, random realization, anisotropic DF, multi-component
tracer, NFW/Hernquist DF or full projected velocity-distribution operator is
supplied by these formulas.

## Custody and qualification

Only owned acquisition/failure metadata and equation/derivation notes are
eligible for the source handoff. Raw PDF, extracted text and rendered copied
source equations have unverified copying rights and remain local, excluded from
uploads. This is an explicit raw-source custody limitation, not full archival
preservation. Selected-source checks, native independent code review, permanent
numerical tests, repository CI and observational acceptance remain separate.

Owned source handoff (`research-named-manifest/v1`):

- URI: `s3://research-data-436908790672-eu-west-2/reproducible/handoffs/prospector/chaplygin-plummer-source-20261009t0301z/versions/f6af7f0050da579f886033f896a1a0b6c48793b61a653a084038a0c0386fb4b5/manifest.json`
- SHA256: `ae4d866251ee49f374bd5d8fdf269f0fea39a1365cd8909f87105ea8bae0579c`
- VersionId: `m9PT3oHEbF8b8Q28PoUMgivnyUQ1kAaB`

Dry-run admission passed before publication. The uploader checked every exact
object version and published the completion manifest last. A separate new
directory restored all five selected files (10,353 bytes); every byte length
and SHA256 matched. This verifies selected metadata/owned-note custody, not
redistribution or preservation of the excluded raw original paper.
