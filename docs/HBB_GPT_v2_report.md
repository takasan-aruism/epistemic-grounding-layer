# HBB SEALED GPT rubric-v2 adjudication

Rubric SHA-256: `012941aba485f33b8328b7e5cba2a84b5c1db82119bb96554bc8dea84f4f9f17`

## 1. Result

### H0 / free response

| Arm | DET mean | RECON mean | D=2 | R=2 |
|---|---:|---:|---:|---:|
| A | 0.818 | 0.182 | 1 | 1 |
| B | 1.455 | 0.545 | 5 | 1 |
| F | 0.545 | 0.000 | 0 | 0 |
| C | 0.636 | 0.273 | 2 | 1 |
| D | 1.000 | 0.455 | 4 | 2 |

### All four independent hint rungs pooled as answer-level observations

| Arm | DET mean | RECON mean | D=2 | R=2 |
|---|---:|---:|---:|---:|
| A | 0.909 | 0.273 | 9 | 3 |
| B | 1.000 | 0.364 | 12 | 4 |
| F | 0.523 | 0.045 | 1 | 1 |
| C | 0.773 | 0.364 | 10 | 6 |
| D | 1.068 | 0.523 | 15 | 9 |

The requested DETECTION/RECONSTRUCTION split changes the interpretation.

At H0, arm B has the highest DETECTION mean (1.455) and the most perfect detections (5/11). Its RECONSTRUCTION mean is much lower (0.545) and only 1/11 responses build a fully historical-equivalent replacement frame.

This supports the narrow form of the Taka hypothesis: **generic skepticism is a strong detection gate, but detection does not normally complete the frame rebuild.**

It does **not** support the stronger statement that an Arism/Formal engine already dominates reconstruction. At H0, B RECONSTRUCTION=0.545, C=0.273, D=0.455. D is closer to B than the prior reach framing suggested, but neither C nor D cleanly surpasses B on free reconstruction.

Across all independent rungs, D has the highest RECONSTRUCTION mean (0.523), followed by B (0.364), A (0.273), C (0.364), F (0.045). This is **hint-sensitive**, not evidence that D wins at autonomous H0 operation.

## 2. Suspended claims

- **'Engine is weaker than B'**: not sustained as a general two-dimensional statement. B clearly leads H0 detection; D is competitive and stronger on pooled reconstruction under hints.
- **'Engine is stronger than B'**: also not sustained. C/D do not outperform B on H0 reconstruction, and the preregistered C-unique/D-unique AA breakthrough claim remains unsupported.
- **Taka hypothesis 'B detects; reconstruction is the missing stage'**: supported in mechanism form. The strongest signal in this re-score is the large DETECTION→RECONSTRUCTION drop, especially for B.

## 3. Hard-core reading

HBB-03 remains the clearest hard case. Several answers question whether higher-order NLP/QwQ input is really richer, but almost none perform the historical reconstruction: **return to a substrate-level primitive physical disturbance**. This is exactly the detection/reconstruction boundary the old reach metric blurred.

The same pattern appears in HBB-08 and HBB-11. Models often identify risk, confounding, namespace, or physical-state issues, but fewer explicitly rebuild the subject/layer frame required by the historical move.

## 4. Procedural deviations

1. Rubric was frozen before raw-file opening.
2. Some raw answer snippets with arm labels were exposed by file-search after rubric freeze but before the mixed-batch artifact was generated. Human-level arm blindness is therefore not pristine.
3. The incident-specific historical-equivalence target map was formalized after raw-file access because a sealed breakthrough-structure map was absent from the handoff. This is recorded as a deviation.
4. ALT_UNTESTED entries are only candidates here; they require separate adjudication/RRI routing.

## 5. HBB-30

HBB-30 is now reconstructed from Taka's explicit historical attestation plus the surviving 6x theory claim. It is marked `USER_ATTESTED_HISTORICAL_RECONSTRUCTION`, not source-extracted T0.

The T0 frame is deliberately: **the document reports 6x, therefore reconstruct why/how the reported result was obtained.** It excludes the later move that the supporting experiment may not exist and the claim should be returned to unverified status.

## 6. Output files

- `HBB_GPT_v2_normalized_blind_batch.json`
- `HBB_GPT_v2_scores.json`
- `HBB_GPT_v2_report.md`
- `HBB-30_T0_GPT_user_attested.json`
