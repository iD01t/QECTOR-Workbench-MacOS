QECTOR Decoder v3 — Extended Reference (package only)  
Version: 0.7.0 · PyPI: qector-decoder-v3 · Backend: Rust \+ PyO3

This document covers only the installable Python package qector-decoder-v3==0.7.0. It does not describe the Workbench GUI or the Workbench’s 56-tool MCP server.

---

### 1\. Installation and platforms

```
pip install qector-decoder-v3==0.7.0
pip install "qector-decoder-v3[stim]"    # Stim / Sinter / PyMatching
pip install "qector-decoder-v3[bench]"   # benchmarks
pip install "qector-decoder-v3[all]"     # full research stack
```

| Item | Value |
| ----- | ----- |
| Python | 3.9 – 3.13 |
| Platforms | Linux x86\_64 (manylinux), Windows x64, macOS arm64 |
| License | Source-available (free academic / personal / non-commercial; commercial licence required) |
| Startup notice | Suppressed with QECTOR\_SILENT=1 |
| Licence env | QECTOR\_LICENSE (Ed25519 token); overrides "academic" / "commercial" for testing |

---

### 2\. Core architecture

* Rust core (compiled extension) — matching, UF, batch, GPU paths  
* Python surface — API, Stim/Sinter compat, belief/GNN, licensing  
* Zero-copy NumPy where possible; GIL-free decode on native paths

Public version string: qector\_decoder\_v3.\_\_version\_\_ \== "0.7.0".

---

### 3\. Decoder families (package API)

| Class / entry | Best for | Status | Graph-like required |
| ----- | ----- | ----- | ----- |
| UnionFindDecoder | Low-latency approximate | Stable | Yes (weight ≤ 2 / participation ≤ 2\) |
| FastUnionFindDecoder | Faster UF hot path | Stable | Yes |
| BlossomDecoder | Exact MWPM | Stable | No |
| SparseBlossomDecoder | Near-optimal matching | Experimental | Prefer graph-like |
| BeliefMatching | Correlated-noise accuracy | Research | Prefer graph-like |
| BpOsdDecoder / BPOSDDecoder | LDPC / qLDPC | Experimental | No |
| BatchDecoder / CPUBatchDecoder | High-throughput CPU batch | Stable | Yes for UF-based batch |
| CUDABatchDecoder | GPU batch | Runtime-dependent | — |
| OpenCLBatchDecoder | OpenCL batch | Build/runtime-dependent | — |
| AutoDecoder | 7-tier self-debugging fallback | Stable | — |
| HybridDecoder | UF \+ Blossom routing | Experimental | Prefer graph-like |
| PredecodedDecoder | Easy-syndrome prefilter | Experimental | Prefer graph-like |
| LookupTableDecoder | Small codes only | Experimental | Small *n\_checks* |
| TwoStageDecoder / AmbiguityClusterDecoder | Multi-round / ambiguity-cluster | Experimental | — |
| GNNBeliefMatcher / GNNPredecoder | GNN-guided matching | Research | Prefer graph-like |
| NeuralPredecoder | Learned predecoder | Research | — |
| Workbench | High-level orchestration | Stable | — |
| DecoderPool | Multi-process batch | Stable | — |
| LERBenchmark | LER sweeps | Experimental | — |

Graph-like rule (UF family): every qubit must participate in at most two checks. Matrices that violate this raise a clear error (no silent wrong results). BlossomDecoder, SparseBlossomDecoder, and BpOsdDecoder accept hyperedge / higher-degree codes.

---

### 4\. Code generators (package)

```
from qector_decoder_v3 import (
    generate_repetition_code_checks,  # (checks, n_qubits)
    generate_ring_code_checks,
    generate_surface_code_checks,     # hyperedge-style surface
    generate_toy_code_checks,
)
```

| Generator | Shape | Graph-like? |
| ----- | ----- | ----- |
| generate\_repetition\_code\_checks(d) | path of length *d* | Yes |
| generate\_ring\_code\_checks(d) | cycle, *n\_qubits* \= *d*² | Yes |
| generate\_surface\_code\_checks(d) | surface-like, often hyperedge | No (e.g. d=3 → participation 8\) |

For production surface-code work, prefer a Stim DEM (decompose\_errors=True) via stim\_compat.from\_stim\_detector\_error\_model, or use the Workbench’s graph-like rotated\_surface generator outside this package.

---

### 5\. Minimal usage examples

Single syndrome (graph-like)

```
import numpy as np
from qector_decoder_v3 import UnionFindDecoder, BlossomDecoder

checks, n_qubits = [[0, 1], [1, 2], [2, 3], [3, 4]], 5
syndrome = np.array([0, 1, 0, 0], dtype=np.uint8)

uf = UnionFindDecoder(checks, n_qubits)
print(uf.decode(syndrome))

mwpm = BlossomDecoder(checks, n_qubits)
print(mwpm.decode(syndrome))
```

Batch

```
from qector_decoder_v3 import BatchDecoder, CUDABatchDecoder

batch = BatchDecoder(checks, n_qubits)
syndromes = np.random.randint(0, 2, (4096, 4), dtype=np.uint8)
corrections = batch.parallel_batch_decode(syndromes)

if CUDABatchDecoder.is_available():
    gpu = CUDABatchDecoder(checks, n_qubits)
    corrections = gpu.batch_decode(syndromes)
```

AutoDecoder (7-tier fallback)

```
from qector_decoder_v3 import AutoDecoder

dec = AutoDecoder(checks, n_qubits)
corrections = dec.batch_decode(syndromes)
# inspect: dec._diag.backend_health, dec._diag.active_backend
```

BeliefMatching / BP-OSD

```
from qector_decoder_v3 import BeliefMatching, BpOsdDecoder
import numpy as np

H = np.array([[1,1,0,0,0],[0,1,1,0,0],[0,0,1,1,0],[0,0,0,1,1]], dtype=np.uint8)
bm = BeliefMatching.from_numpy_h(H)          # v0.7.0: returns length-n_qubits vector
print(bm.decode(np.array([0,1,0,0], dtype=np.uint8)))

bp = BpOsdDecoder(H, error_rate=0.05, osd_order=0, bp_method="exact")
print(bp.decode(np.array([0,1,0,0], dtype=np.uint8)))
```

Stim

```
import stim
from qector_decoder_v3 import BlossomDecoder
from qector_decoder_v3.stim_compat import from_stim_detector_error_model

circuit = stim.Circuit.generated(
    "surface_code:rotated_memory_z", distance=5, rounds=5,
    after_clifford_depolarization=0.005,
)
dem = circuit.detector_error_model(decompose_errors=True)
checks, n_qubits = from_stim_detector_error_model(dem)
decoder = BlossomDecoder(checks, n_qubits)
```

Licence

```
from qector_decoder_v3.license import verify_license_token
verify_license_token("")                    # False
verify_license_token("garbage")             # False (no raise; hardened)
verify_license_token("academic")            # True (dev override)
```

---

### 6\. v0.7.0 package highlights

| Area | Change |
| ----- | ----- |
| BeliefMatching | from\_numpy\_h returns faithful length-n\_qubits correction (H @ corr ≡ syndrome) |
| BP-OSD | Exact log-domain sum-product BP by default; OSD-1/2 via osd\_order |
| GNN | GNNBeliefMatcher end-to-end GNN-guided MWPM with faithfulness fallback |
| Licence | Malformed tokens return False (no exception); v2 tokens carry tier \+ expiry |
| Docs | Tuning env vars documented (accuracy vs throughput) |

Tuning environment variables

| Variable | Default | Effect |
| ----- | ----- | ----- |
| QECTOR\_BLOSSOM\_K\_MULT | 2.0 | Candidate-neighbour multiplier (affects accuracy) |
| QECTOR\_BLOSSOM\_INTRA\_PAR | auto | Intra-decode parallelism (throughput only) |
| QECTOR\_BLOSSOM\_INTRA\_THREADS | unset | Dedicated Rayon pool size |
| QECTOR\_CUDA\_DEVICE\_ID | 0 | CUDA device index |
| QECTOR\_OPENCL\_DEVICE\_ALLOW | unset | Device name filter substrings |

Only QECTOR\_BLOSSOM\_K\_MULT and device selection change matching quality.

---

### 7\. Package MCP server (run\_mcp\_server)

```
from qector_decoder_v3 import run_mcp_server
run_mcp_server()   # JSON-RPC 2.0 on stdin/stdout
```

Tools (13, verified in the v0.7.0 benchmark set)

| Tool | Role |
| ----- | ----- |
| decode\_syndrome | Single syndrome; accepts decoder\_type |
| batch\_decode | Batch decode over cpu / cuda / opencl backends |
| decode\_hyperedge | Decode against a raw hyperedge check matrix |
| decode\_syndrome\_blossom | Exact Blossom MWPM decode |
| batch\_decode\_blossom | Batch exact Blossom MWPM decoding |
| decode\_syndrome\_cascade | Union-Find first, Blossom/BP-OSD escalation |
| benchmark\_decoder | Latency / throughput harness |
| run\_ler\_benchmark | Logical-error-rate benchmark (comparable rows only) |
| get\_decoder\_info | Version \+ capability list |
| get\_backend\_health | cpu / cuda / opencl probe |
| clear\_decoder\_cache | Clear native decoder cache |
| get\_server\_env | Runtime environment summary |
| recommend\_decoder | Decoder recommendation per code family |

decoder\_type values that route successfully (graph-like codes):  
UnionFind, FastUnionFind, Blossom, SparseBlossom, bposd, LookupTable, Auto, Hybrid, BeliefMatching, Predecoded, GNNBeliefMatcher, Batch, … (case variants often accepted).

Limitation: the package MCP applies a UF-style structural gate (qubit participation ≤ 2). Hyperedge matrices (including generate\_surface\_code\_checks) are rejected for all decoder\_type values with error −32602. There is no argument that disables this gate.

Workbench MCP (56 tools) is a separate product surface and is not part of this package reference.

---

### 8\. Hyperedge workaround (package only)

```
import numpy as np
from qector_decoder_v3 import BlossomDecoder, SparseBlossomDecoder, BpOsdDecoder

def decode_hyperedge(checks, n_qubits, syndrome, kind="Blossom", **opts):
    """Use when MCP or UF-family reject high-degree incidence matrices."""
    syn = np.asarray(syndrome, dtype=np.uint8).ravel()
    if kind in ("Blossom", "blossom"):
        return BlossomDecoder(checks, n_qubits).decode(syn)
    if kind in ("SparseBlossom", "sparse_blossom"):
        return SparseBlossomDecoder(checks, n_qubits).decode(syn)
    if kind.lower() in ("bposd", "bp_osd"):
        H = np.zeros((len(checks), n_qubits), dtype=np.uint8)
        for i, c in enumerate(checks):
            for q in c:
                if 0 <= q < n_qubits:
                    H[i, q] ^= 1
        return BpOsdDecoder(H, error_rate=opts.get("error_rate", 0.05),
                            osd_order=opts.get("osd_order", 0)).decode(syn)
    raise ValueError(f"unsupported kind for hyperedge: {kind}")
```

MCP \+ fallback pattern: try package MCP; on message containing "hyperedge" / "weight ≤ 2" / "participates in", call decode\_hyperedge (or BlossomDecoder directly).

---

### 9\. AutoDecoder 7-tier fallback (v0.6.8+)

| Tier | Backend |
| ----- | ----- |
| 1 | CUDA batch |
| 2 | OpenCL batch |
| 3 | CPU Rayon parallel batch |
| 4 | CPU batch |
| 5 | CPU single |
| 6 | Blossom (exact) |
| 7 | Lookup / pure Python |

Failed backends are health-scored and suspended; reset\_backend\_health() re-enables them.

---

### 10\. Validated claims (package artefacts)

The only citable figures for this release are the verified v0.7.0 benchmark set: REPORT.md, summary.json, benchmarks.csv (54 rows, zero unfaithful corrections), and VERIFIED_APPLE_TO_APPLE_REPORT.pdf.

* Peak throughput: 11,540,387 shots/s (FastUnionFind, 5-qubit repetition code, 8,000 samples) — package MCP server, Linux glibc 2.35, Python 3.12.13.
* 54/54 benchmark points with zero unfaithful corrections (repetition n=5–65, ring n=16–48; unionfind, fastunionfind, blossom, sparseblossom, bposd, auto).
* 42/42 syndrome-faithfulness cases passed.
* 13 MCP tools operational (MCP stdio, JSON-RPC 2.0).
* Apple-to-apple vs PyMatching: comparable; PyMatching often slightly ahead on the synchronized batch. No speedup multiplier is claimed.
* Pre-v0.7.0 comparison tables (MWPM parity vs PyMatching at d=13/15, Belief-Matching LER gain at d=5/7, GPU bit-identity, native memory profile) are formally withdrawn — do not cite them.

Run the harness yourself: qector benchmark --verify or python -m qector.validate. Regenerate benchmarks on target hardware before publishing numbers.

---

### 11\. Stim / Sinter integration

```
from qector_decoder_v3.sinter_compat import qector_sinter_decoders
import sinter
# custom_decoders=qector_sinter_decoders()
# names e.g. qector_belief, qector_blossom, qector_unionfind
```

```
from qector_decoder_v3.stim_compat import from_stim_detector_error_model
```

Optional extra: pip install "qector-decoder-v3\[stim\]".

---

### 12\. Practical recommendations (v0.7.0 package)

| Goal | Choice |
| ----- | ----- |
| Fast graph-like Monte Carlo | FastUnionFindDecoder / BatchDecoder / AutoDecoder |
| Exact MWPM validation | BlossomDecoder |
| Hyperedge / general stabilizer | BlossomDecoder or BpOsdDecoder (direct API) |
| qLDPC / LDPC | BpOsdDecoder (bp\_method="exact", osd\_order as needed) |
| Accuracy research | BeliefMatching / GNNBeliefMatcher |
| Agent / stdio automation | Package MCP for graph-like only; else direct API \+ fallback |
| Licence checks | verify\_license\_token (offline Ed25519; v2 tokens with tier/exp) |

---

### 13\. What this package is not

* Not the Workbench application (no 56-tool MCP, no GUI).  
* Not a drop-in claim of universal PyMatching replacement (honest latency positioning in docs).  
* Not open-source: source-available; commercial use requires a licence.

---

Package: qector-decoder-v3==0.7.0  
Docs / site: [https://www.qector.store](https://www.qector.store/) · [https://pypi.org/project/qector-decoder-v3/](https://pypi.org/project/qector-decoder-v3/)  
Repository: [https://github.com/GuillaumeLessard/qector-decoder](https://github.com/GuillaumeLessard/qector-decoder)

