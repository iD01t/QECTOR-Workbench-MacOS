# QECTOR Decoder v3 (v0.7.0) - Verified Benchmark Report

**Generated:** 2026-07-24 20:15:35  
**Machine:** Windows-11-10.0.26100-SP0  
**Python:** 3.12.13  
**Backend:** qector_decoder_v3 0.7.0  
**Competitors:** PyMatching 2.4.0, Stim 1.16.0, ldpc 2.4.1  
**Total wall time:** 378.07 s

## Methodology

- Head-to-head decoders consume the identical problem instance (same Stim DEM and same detector samples for MWPM; same BB72 syndromes for BP-OSD).
- All codes are built via `backend.build_code`; sizes are the real code sizes (`rotated_surface` d=5 = 25 qubits / 12 checks, `bivariate_bicycle` 3 = 72 qubits / 36 checks).
- A correction is counted valid only if it reproduces the observed syndrome over GF(2) (`backend.verify_correction` / explicit `H·c mod 2`).
- Logical error rate is reported only where the code exposes logical operators; BB72 does not here, so its LER is n/a (not fabricated).
- Parallel scaling is the real multiprocess `DecoderPool`; GPU rows use the real CUDA/OpenCL batch backends with honest availability.

## Section A - MWPM on the same Stim DEM (PyMatching vs QECTOR)

| d | qubits | detectors | PyMatching dec/s | QECTOR dec/s | ratio Q/PM | pred agreement | LER PM | LER Q |
|---|---|---|---|---|---|---|---|---|
| 3 | 9 | 24 | 1,595,066 | 1,454,842 | 0.91x | 100.0% | 0.0477 | 0.0477 |
| 5 | 25 | 120 | 177,991 | 66,024 | 0.37x | 99.9% | 0.0690 | 0.0693 |
| 7 | 49 | 336 | 47,054 | 15,874 | 0.34x | 99.7% | 0.0802 | 0.0807 |
| 9 | 81 | 720 | 18,199 | 4,490 | 0.25x | 99.8% | 0.0957 | 0.0961 |

## Section B - BP-OSD on the same BB72 syndromes (ldpc vs QECTOR)

BB72: 72 qubits, 36 checks, p=0.03, shots=1000. Logical error rate: n/a (no logicals exposed).

| decoder | decodes/s | syndrome valid | mean us | p50 us | p99 us |
|---|---|---|---|---|---|
| ldpc BpOsd | 17,281.5 | 100.0% | 47.29 | 12.60 | 207.20 |
| QECTOR bp_osd | 1,153.8 | 100.0% | 853.33 | 811.05 | 1197.83 |

## Section D - Distance scaling (real rotated surface codes)

| d | qubits | checks | blossom dec/s | blossom LER | union_find dec/s | union_find LER |
|---|---|---|---|---|---|---|
| 3 | 9 | 4 | 596,427 | 0.0480 | 477,966 | 0.0585 |
| 5 | 25 | 12 | 331,548 | 0.0610 | 387,830 | 0.0960 |
| 7 | 49 | 24 | 157,102 | 0.0575 | 295,251 | 0.0705 |
| 9 | 81 | 40 | 73,331 | 0.0640 | 228,441 | 0.0690 |
| 11 | 121 | 60 | 38,015 | 0.0525 | 177,481 | 0.0545 |
| 13 | 169 | 84 | 7,580 | 0.0645 | 137,224 | 0.0660 |

## Sections C, E, F, G

See `benchmark_results.json` for the full decoder x family matrix (C), the real multiprocess parallel-scaling curve (E), the CPU/CUDA/OpenCL backend throughput (F), and the sliding-window streaming telemetry (G).

## What changed relative to the earlier scripts

The previous `epic` / `hyper` / `ultimate` scripts benchmarked `py_generate_ring_code_checks(d)` (a 1-D ring code: d qubits, d checks) while labelling it a surface code or BB72, and compared it against PyMatching running on a genuine 25-qubit surface-code DEM. They also reported an 8-thread number that was the single-thread time divided by 1.6, a CUDA number that was the CPU time multiplied by 1.8, and hard-coded '100% accuracy' / '0 bytes leaked' strings. This suite removes all of that: real codes, identical problem instances, verified corrections, real pool/GPU execution.
