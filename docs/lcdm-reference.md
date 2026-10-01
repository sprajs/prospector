# ΛCDM reference

The [full-reference candidate](../designs/candidate-lcdm-baseline-reference-audit.json)
and [conditional comparison](../designs/candidate-lcdm-massless-conditional-comparison.json)
have different scientific scope. Neither claims ΛCDM is uniquely correct.
Alternative prospects retain their existing source identities and readiness.

## Full source model

[Planck 2018 VI, 1807.06209v4](https://arxiv.org/abs/1807.06209v4), Sec.2.1,
defines spatially flat six-parameter GR ΛCDM: baryons, cold dark matter, photons,
two effectively massless neutrinos, one fixed 0.06 eV neutrino and Λ. It also needs
adiabatic power-law scalar perturbations, standard thermal history, BBN-consistent
helium, recombination and tanh reionization.

The [numerical reference](../references/lcdm/planck2018-reference.json) retains
Table 2's `TT,TE,EE+lowE+lensing` column, using baseline Plik, without BAO. These
are marginalized, model-conditioned posterior values. Their errors are neither
independent measurement errors nor numerical tolerances. The table supplies no
joint covariance; its marginal means need not define an exact posterior sample.
Reported Ωm includes the massive neutrino. θMC is a sampling proxy for θ*.

## Limited comparison

Reproducible's `experiments/lcdm-baseline` uses declared synthetic fractional
controls: H₀=67.4 km/s/Mpc, Ωm=0.315, Ωr=0.000092, Ωb=0.049,
Ωγ=0.0000545 and supplied zdrag=1059. Baryons and photons are subsets of matter
and radiation; ΩΛ=1−Ωm−Ωr. Matter stays pressureless and radiation stays massless.
This is not a Planck draw or a fixed-Tcmb/Neff conversion.

The comparison exports E(z), D_M(z), D_L(z), the 13 ordered BAO ratios and
the Gaussian quadratic, log determinant, normalization and log density. Internal
H, D_H, D_V and supplied-endpoint ruler values support these calculations; their
standalone values are not required comparison outputs. No SN profile is included. Irreducible at pinned
`db4765838fc404a489a0115ee69713f2ea6cd2f4` has native early/late and conditional
BAO kernels, but no early/late CLI route or generic recipe runner. The separate
late `background.evaluate` LCDM descriptor omits radiation. Full massive-neutrino
evolution, predicted drag, recombination, perturbations, CMB, growth and lensing
remain outside this candidate's supported physics.

## Input ancestry

[DESI DR2 II, 2503.14738v3](https://arxiv.org/abs/2503.14738v3), Table 4,
provides seven baseline tracer samples. Combined LRG3+ELG1 supersedes its two
separate rows. Distance/ruler ratios arise from fiducial templates, reconstruction
and nuisance marginalization; Table 4 reports marginalized BAO-fit posterior means
and standard deviations. Preserve the official 13-coordinate mean/covariance
release and order. BAO alone does not measure H₀ separately from its ruler.
[The official release portal](https://data.desi.lbl.gov/doc/papers/dr2/) links the
analysis products; Reproducible owns immutable released-data receipts and runs.

Pantheon+ [cosmology](https://arxiv.org/abs/2202.04077v2),
[dataset](https://arxiv.org/abs/2112.03863v2) and
[calibration](https://arxiv.org/abs/2112.03864v2) sources describe standardized,
selected light curves with correlated calibration, duplicate observations and
SALT2 training. They are reference context here, not executed SN likelihoods.
[SH0ES](https://arxiv.org/abs/2112.04510v3) shares SN/calibrator information and
covariance with Pantheon+. A free SN offset cannot establish absolute H₀; adding
the overlapping SH0ES H₀ summary as an independent constraint would double count.

## Handoff

Prospector supplies source claims and immutable candidate/reference hashes.
Reproducible accepts those bytes, implements a dedicated typed consumer and records
inputs, failed attempts, numerical comparisons and qualification. Irreducible owns
shared compiled equations. Source agreement, numerical checks, likelihood
reproduction and scientific interpretation have separate acceptance gates.

This audit checks selected original-source sections. It does not claim Luna full
readings, complete bibliography coverage or independent reproduction of a paper.

Two unused printed expressions need care: Planck Sec.7.5.2 Eq.62 omits the
photon contribution while describing total radiation, and the Pantheon+ dataset
paper Sec.III.2 has inconsistent inline covariance shorthand. Neither expression
is used for the candidate controls or covariance. The source inconsistencies are
recorded separately from our corrected SH0ES equation locator.
