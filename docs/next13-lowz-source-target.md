# LOWZ windowed-power source target

This is frozen source evidence. Current scheduling follows [the sole roadmap](roadmap.md).

NEXT-13 selects one June 2016 **pre-reconstruction LOWZ P0/P2** release at
effective redshift 0.32. This is the smaller LOWZ/CMASS power-only option in the
selected release, not a claim about all available clustering datasets.

The [source contract](../register/contracts/next13-lowz-pre-recon-windowed-power-source-target-v1.json)
and [targeted review](../register/reviews/2026-10-03-next13-lowz-windowed-power-source-claims.json)
bind the exact primary [1509.06386v2](https://arxiv.org/abs/1509.06386v2), release
member hashes and reading limits. The paper remains queued for a complete reading.
The later power-plus-bispectrum source and earlier contracts remain separate ancestry.

| Released object | Inspected shape | Convention |
| --- | --- | --- |
| Measured P0 and P2 | 53 × 3 each | k, power, printed error; k in h/Mpc, power/error in (Mpc/h)^3 |
| Theory k grid | 1000 × 1 | h/Mpc |
| W00, W02, W20, W22 | 53 × 1000 each | Output data rows, input theory columns |
| P0/P2 covariance | 106 × 106 | Headerless; axis ownership unresolved |

The [primary displayed action](https://arxiv.org/html/1509.06386v2#S5.EGx4),
called Eq. 15 by the release README, is

```text
P0_win[i] = sum_j (W00[i,j] P0[j] + W02[i,j] P2[j])
P2_win[i] = sum_j (W20[i,j] P0[j] + W22[i,j] P2[j])
```

No additional integration weight is inserted into that displayed discrete action.
The source assumes only monopole/quadrupole angular shape and omits an
integral-constraint correction. Calibration, normalization and literal index
ambiguities in the preceding window definition remain unresolved; the original
PDF equation numbering has not been checked.

The source lower fit cuts are P0 k > 0.02 and P2 k > 0.04 h/Mpc; its reported
table fits use kmax = 0.24 h/Mpc. The supplied 53 bins have centers from
0.002342 to 0.317660 h/Mpc, while the theory grid spans 0.001249 to 0.499750 h/Mpc.
These describe different domains. An exact historical cut-row map is not yet admitted.

Testing the candidate order of all P0 rows followed by all P2 rows yielded only
**6 of 106 covariance diagonal/printed-error-square interval matches**. This
does not establish covariance axes or the relationship between those errors and
the released covariance. The paper's block notation supplies no serialization
proof. No permutation, rescaling, substitute diagonal covariance or score is accepted.

The historical analysis uses a fixed fiducial spectral shape, ruler-conditioned
Alcock–Paczynski coordinates and eight fitted parameters, including bias,
Fingers-of-God and non-Poisson shot-noise freedom. A changing CLASS matter spectrum
requires an explicitly sourced galaxy/RSD model, epoch/species/unit/grid adapter,
AP/ruler mapping and nuisance choices. A simpler model needs its own approximation
identity and lost scope. Continuous CMB projection geometry supplies none of these.

The existing Irreducible Gaussian owner can prepare one full covariance and evaluate
each complete ordered residual vector. Its native source capability does not admit
this covariance or predict galaxy multipoles. The source's Gaussian fit uses
finite-mock inverse and parameter-error corrections. A normalized fixed raw-C
Gaussian would be a separately declared conditional model, not parity with that fit.
Shared BOSS objects, masks, randoms and mocks also leave cross-probe dependence unresolved.

**Unresolved dependency:** source/consumer qualification requires reconciliation
of the exact released covariance axes and error semantics against producer evidence, a justified
ordered-row/covariance and historical cut map; refusal remains otherwise.
This precedes scoring; the galaxy/window adapter and statistical-model gates remain separate prerequisites.

This checkpoint accepts located source claims only. It adds no numerical experiment,
full-paper review, graph relationship or prospect promotion. The full ΛCDM audit
and all nineteen scopes remain open.
