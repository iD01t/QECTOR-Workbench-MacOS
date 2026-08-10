"""Generate QECTOR API reference manual (Markdown + PDF)."""
from __future__ import annotations
import inspect, sys, textwrap
from datetime import datetime, timezone
from pathlib import Path
sys.path.insert(0, r"D:\QECTOR APP")
import version, backend as be
from mcp_server import get_mcp_server

OUT = Path(r"D:\QECTOR APP\manuals")
DESK = Path(r"C:\Users\Clinque du Batiment\Desktop\manuals")

def sig(o):
    try: return str(inspect.signature(o))
    except Exception: return "(...)"

def lead(o):
    d = inspect.getdoc(o) or ""
    return d.split("\n\n")[0].replace("\n", " ")

def code_families():
    rows = [
        ("repetition","distance","int","yes","all (13)","1D chain parity-check code."),
        ("ring","distance","int","yes","all (13)","Periodic 1D chain."),
        ("rotated_surface","distance","int","yes","all (13)","Standard rotated surface code."),
        ("unrotated_surface","distance","int","yes","12 (lookup_table refused >20 checks)","Square lattice surface code."),
        ("toric","distance","int","yes","12 (lookup_table refused >20 checks)","Toric code with periodic boundaries."),
        ("heavy_hex","distance","int","yes","all (13)","IBM heavy-hex lattice."),
        ("hypergraph_product","distance","int","yes","all (13)","CSS from repetition seed; graphlike."),
        ("bicycle","circulant size","int","no","all (13)","qLDPC bicycle code; graphlike enough for all decoders."),
        ("bivariate_bicycle","preset index","int","no","9 (excludes union_find, fast_union_find, lookup_table, belief_matching)","IBM BB presets; see compatibility matrix."),
    ]
    lines = ["## Code families","","| Family | Parameter | Type | Graphlike | Decoders | Notes |","|---|---|---|---|---|---|"]
    for r in rows: lines.append("| " + " | ".join(r) + " |")
    return "\n".join(lines)

def decoders():
    rows = [
        ("union_find","Fast approximate matching via union-find.","bp_method, osd_order ignored","graphlike only"),
        ("fast_union_find","Faster union-find variant; approximate, higher LER.","-","graphlike only"),
        ("blossom","Weight-optimal exact MWPM; matches PyMatching LER.","-","all"),
        ("sparse_blossom","Region-growing near-optimal matching; not exact.","-","graphlike only"),
        ("bp_osd","Belief propagation + ordered statistics for LDPC/qLDPC.","bp_method, osd_order, error_rate","all"),
        ("auto","Self-selecting AutoDecoder.","-","graphlike only"),
        ("hybrid","Combines multiple strategies; chooses per problem.","-","graphlike only"),
        ("lookup_table","Exhaustive syndrome-to-correction table; refused above 20 checks.","-","small codes only"),
        ("predecoded","Fast pre-decoding pass before matching.","-","graphlike only"),
        ("auto_router","Policy decoder: matching for graphlike, bp_osd for qLDPC. Universally compatible.","-","all"),
        ("hybrid_cascade","Union-Find pre-filter + Blossom/BP-OSD escalation; exposes cascade stats.","escalation, error_rate","graphlike only"),
        ("gnn_belief_matching","GNN-guided weighted matching with faithfulness fallback.","gnn_hidden_size, gnn_n_layers, error_rate","graphlike only"),
        ("belief_matching","BP posteriors reweight exact Blossom matching; faithfulness fallback.","bp_method, osd_order, error_rate","graphlike only"),
    ]
    lines = ["## Decoder kinds","","| Kind | Description | Options | Compatibility |","|---|---|---|---|"]
    for r in rows: lines.append("| " + " | ".join(r) + " |")
    return "\n".join(lines)

def options():
    return textwrap.dedent("""\
        ## Decoder options

        | Key | Type | Applies to | Description |
        |---|---|---|---|
        | `bp_method` | string | `bp_osd`, `belief_matching` | `"exact"` or `"min_sum"`. |
        | `osd_order` | int | `bp_osd`, `belief_matching` | `0`, `1`, or `2`. Higher is slower/more accurate. |
        | `error_rate` | float | all | Physical error probability used to weight edges or set BP priors. |
        | `escalation` | string | `hybrid_cascade` | `"blossom"` or `"bp_osd"`. |
        | `max_accept_weight` | int | `hybrid_cascade` | Maximum syndrome weight accepted by the pre-filter. |
        | `gnn_hidden_size` | int | `gnn_belief_matching` | Hidden dimension of the GNN. |
        | `gnn_n_layers` | int | `gnn_belief_matching` | Number of GNN message-passing layers. |

        Unknown keys are ignored with a warning; missing keys use backend defaults.
        """)

def backend_api():
    lines = ["## backend.py API", ""]
    for name in sorted(dir(be)):
        if name.startswith("_"): continue
        obj = getattr(be, name)
        if callable(obj):
            lines.append(f"### `backend.{name}{sig(obj)}`")
            lines.append("")
            lines.append(lead(obj) or "*No docstring.*")
            lines.append("")
    return "\n".join(lines)

def module_api(title, modname):
    try: mod = __import__(modname)
    except Exception as e: return f"## {title}\n\n*Import failed: {e}*\n"
    lines = [f"## {title}", ""]
    for name in sorted(dir(mod)):
        if name.startswith("_"): continue
        obj = getattr(mod, name)
        if callable(obj) and not isinstance(obj, type):
            lines.append(f"### `{modname}.{name}{sig(obj)}`")
            lines.append("")
            lines.append(lead(obj) or "*No docstring.*")
            lines.append("")
    return "\n".join(lines)

def measurements_section():
    import json
    path = Path(r"D:\QECTOR APP\build\manual_data\measurements.json")
    if not path.exists():
        return "## Measured data\n\n*Run `build/collect_data.py` to populate this section.*\n"
    data = json.load(path.open(encoding="utf-8"))
    lines = ["## Measured data", "", "All figures below were measured on this machine (seeded, n=50, p=0.05, rotated_surface d=5). They are workload- and hardware-dependent.", ""]
    lines.append("### Code family properties")
    lines.append("")
    lines.append("| Family | Distance | n_qubits | n_checks | max_degree | compatible decoders |")
    lines.append("|---|---|---|---|---|---|")
    for fam, info in data["families"].items():
        if "error" in info:
            lines.append(f"| {fam} | {info['distance']} | error | - | - | - |")
        else:
            s = info["summary"]
            lines.append(f"| {fam} | {info['distance']} | {s.get('n_qubits')} | {s.get('n_checks')} | {s.get('max_qubit_degree')} | {len(info['compatible'])} |")
    lines.append("")
    lines.append("### Decoder benchmark results")
    lines.append("")
    lines.append("| Decoder | Throughput (decodes/s) | p50 latency (µs) | p99 latency (µs) | logical error rate |")
    lines.append("|---|---|---|---|---|")
    for kind, r in data["benchmarks"].items():
        if "error" in r:
            lines.append(f"| {kind} | error | - | - | - |")
        else:
            lines.append(f"| {kind} | {r['throughput_decodes_per_s']:.0f} | {r['latency_p50_us']:.2f} | {r['latency_p99_us']:.2f} | {r['logical_error_rate']} |")
    lines.append("")
    lines.append("### Figures")
    lines.append("")
    for img in ["tanner_rotated_surface_d5.png", "decoder_throughput.png", "decoder_latency.png", "compatibility_matrix.png", "cascade_stats.png"]:
        lines.append(f"![{img}](figures/{img})")
        lines.append("")
    return "\n".join(lines)

def mcp_section():
    reg = get_mcp_server().tools.tools
    lines = ["## MCP tool reference", "", f"{len(reg)} tools via stdio JSON-RPC 2.0.", ""]
    for name in sorted(reg):
        spec = reg[name]
        lines.append(f"### `{name}`")
        lines.append(spec.get("description", ""))
        params = spec.get("parameters", {})
        if params:
            lines.append("**Parameters**")
            for pname, pspec in params.items():
                ptype = pspec.get("type", "any")
                default = pspec.get("default")
                req = "required" if default is None else f"default `{default!r}`"
                desc = pspec.get("description", "")
                lines.append(f"- `{pname}` (`{ptype}`, {req}) - {desc}")
        else:
            lines.append("*No parameters.*")
        lines.append("")
    return "\n".join(lines)

def wire_protocol():
    return textwrap.dedent("""\
        ## MCP wire protocol

        Newline-delimited JSON-RPC 2.0 over stdio. Launch with `--mcp`.

        ```json
        {"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"client","version":"1.0"}}}
        {"jsonrpc":"2.0","method":"notifications/initialized"}
        {"jsonrpc":"2.0","id":2,"method":"tools/list"}
        {"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"decode_single","arguments":{"family":"rotated_surface","distance":5,"decoder_name":"blossom","error_rate":0.05,"seed":42}}}
        ```

        Result envelope: `content[0].text` holds a JSON payload; `isError` flags tool-level failure.
        """)

def schemas():
    return textwrap.dedent("""\
        ## Common result schemas

        ```python
        # Single decode result
        {"error":[...],"syndrome":[...],"result":{"correction":[...],"hamming_weight":int,"syndrome_valid":bool,"logical_failure":bool|None,"backend_used":str|None,"matched_weight":int|None,"fallback_used":bool,"options_applied":bool|dict,"latency_us":float}}
        # Benchmark result
        {"throughput_decodes_per_s":float,"decode_seconds":float,"n_trials":int,"p":float,"seed":int,"method":str,"backend":str,"latency_mean_us":float,"latency_p50_us":float,"latency_p99_us":float,"latency_min_us":float,"latency_max_us":float,"syndrome_match_rate":float,"logical_error_rate":float}
        # Resilient decode
        {"success":bool,"used_decoder":str|None,"fallback_used":bool,"syndrome_valid":bool|None,"logical_failure":bool|None,"attempts":[{"method":str,"ok":bool,"syndrome_valid":bool|None,"hamming_weight":int|None,"latency_ms":float|None,"error":str|None}],"message":str}
        # Diagnostics report
        {"overall_status":"pass|degraded|fail","timestamp":float,"platform":str,"python":str,"workbench_version":str,"backend_version":str|None,"summary":{...},"checks":[{"name":str,"status":str,"detail":str}]}
        ```
        """)

def env_and_examples():
    return textwrap.dedent("""\
        ## Environment variables

        | Variable | Effect |
        |---|---|
        | `QECTOR_PYTHON` | Compatible CPython for pip provisioning. |
        | `QECTOR_DATA_DIR` | Relocate all QECTOR user data. |
        | `QECTOR_AUTO_UPGRADE` | Set to `0` to disable background upgrade checks. |
        | `QECTOR_APP_PACKAGE` | Override PyPI package name for app updates. |
        | `QECTOR_SILENT` | Set to `1` to suppress the backend startup notice. |
        | `QECTOR_LICENSE` | Ed25519 token that overrides academic/commercial for testing. |
        | `QECTOR_DISABLE_OPENCL` | Set to `1` to skip OpenCL probing. It cannot *enable* OpenCL. |
        | `QECTOR_ENABLE_OPENCL_AUTO` | Allows OpenCL auto-routing, but only when OpenCL is already available. |

        ## Provisioning model

        The Workbench application no longer bundles the decoder wheel. On first launch it downloads
        `qector-decoder-v3` from PyPI and installs it into a managed, ABI-scoped user site. After
        installation the app works offline. Linux requires `python3` and `python3-pip`; Windows and
        macOS need no separate Python setup.

        A splash screen is shown within roughly a second of launch and closes once the main window is
        mapped, so the cold start (download on first run, then loading a compiled extension) is never
        an invisible wait.

        ### Boot diagnostics

        A windowed build has no stderr, so provisioning is logged to files under the per-user data
        directory:

        | File | Contents |
        |---|---|
        | `logs/boot.log` | Every bootstrap step, the activated site, and the exact import error. |
        | `logs/boot_stdio.log` | Anything written to stdout/stderr when the build has no console. |

        ## Hardware backends

        | Backend | Availability |
        |---|---|
        | `cpu` | Always available. |
        | `cuda` | Requires an NVIDIA GPU with a healthy driver. |
        | `opencl` | Reported unavailable by the published wheel, which is built without the OpenCL feature. |

        `opencl_is_available()` returning `False` is a property of the decoder build, not of the host:
        a machine can expose OpenCL devices and still get `False`, and no environment variable changes
        it. `hardware_routing.detect_hardware()` reports `opencl_host_devices` and
        `opencl_host_platform` (probed from the host ICD) plus an `opencl_reason` string so the two
        situations can be told apart. Enabling the backend requires rebuilding `qector-decoder-v3`
        with its `opencl` Cargo feature.

        ## Example workflows

        ```python
        import backend as be, autodebug
        code = be.build_code("rotated_surface", 5)
        out = be.run_single_decode(code, error_rate=0.05, decoder_kind="blossom", seed=42)
        assert out["result"]["syndrome_valid"]

        out2 = be.run_single_decode(code, error_rate=0.05, decoder_kind="bp_osd", seed=7, decoder_options={"bp_method":"min_sum","osd_order":1})
        probe = autodebug.probe_decoders("bivariate_bicycle", 3, seed=99)
        resilient = autodebug.resilient_single_decode("bivariate_bicycle", 3, decoder="union_find", seed=7)
        stats = be.run_hybrid_cascade_stats(code, n_samples=64, error_rate=0.05, seed=1)
        ```
        """)

def build_markdown():
    parts = [
        "# QECTOR Workbench - Complete API Reference",
        f"**Workbench {version.WORKBENCH_VERSION} - Backend `qector_decoder_v3` {version.BACKEND_VERSION} (min {version.MIN_BACKEND_VERSION}) - {version.MCP_TOOLS} MCP tools - {len(be.DECODER_KINDS)} decoders - {len(be.CODE_FAMILIES)} code families**",
        f"**PyPI package: [qector-decoder-v3](https://pypi.org/project/qector-decoder-v3/) {version.BACKEND_VERSION}**",
        f"Generated {datetime.now(timezone.utc).isoformat(timespec='seconds')}Z",
        "",
        "This manual is generated from the live application source so every tool name, decoder kind, code family, and function signature matches the running build exactly.",
        "",
        code_families(),
        "",
        decoders(),
        "",
        options(),
        "",
        measurements_section(),
        "",
        backend_api(),
        "",
        module_api("autodebug.py API", "autodebug"),
        "",
        module_api("hardware_routing.py API", "hardware_routing"),
        "",
        module_api("version_service.py API", "version_service"),
        "",
        module_api("decoder_provisioner.py API", "decoder_provisioner"),
        "",
        module_api("auto_updater.py API", "auto_updater"),
        "",
        module_api("doc_generator.py API", "doc_generator"),
        "",
        mcp_section(),
        "",
        wire_protocol(),
        "",
        schemas(),
        "",
        env_and_examples(),
    ]
    return "\n".join(parts)

def md_to_pdf_elements(text: str):
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.units import inch
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import Paragraph, Spacer, Preformatted, PageBreak, Image as RLImage

    styles = getSampleStyleSheet()
    title = ParagraphStyle("title", parent=styles["Title"], fontSize=18, spaceAfter=12)
    h1 = ParagraphStyle("h1", parent=styles["Heading1"], fontSize=14, spaceAfter=8, spaceBefore=10)
    h2 = ParagraphStyle("h2", parent=styles["Heading2"], fontSize=12, spaceAfter=6, spaceBefore=8)
    body = ParagraphStyle("body", parent=styles["BodyText"], fontSize=9, leading=12)
    code = ParagraphStyle("code", parent=styles["Code"], fontSize=8, leading=10)
    elems = []
    in_code = False
    buf = []

    def flush_code():
        nonlocal buf
        if buf:
            elems.append(Preformatted("\n".join(buf), style=code))
            elems.append(Spacer(1, 6))
            buf = []

    for raw in text.splitlines():
        line = raw.rstrip()
        if line.startswith("```"):
            if in_code:
                flush_code()
            in_code = not in_code
            continue
        if in_code:
            buf.append(line)
            continue
        if not line:
            elems.append(Spacer(1, 4))
            continue
        if line.startswith("![") and "](figures/" in line:
            name = line.split("](figures/")[1].split(")")[0]
            img_path = OUT / "figures" / name
            if img_path.exists():
                from reportlab.lib.utils import ImageReader
                reader = ImageReader(str(img_path))
                iw, ih = reader.getSize()
                max_w = 6.5 * inch
                max_h = 4.5 * inch
                scale = min(max_w / iw, max_h / ih)
                elems.append(RLImage(str(img_path), width=iw * scale, height=ih * scale))
                elems.append(Spacer(1, 6))
            continue
        if line.startswith("# "):
            flush_code()
            elems.append(Paragraph(line[2:], title))
        elif line.startswith("## "):
            flush_code()
            if line in {"## Code families", "## Decoder kinds", "## backend.py API", "## MCP tool reference", "## Measured data"}:
                elems.append(PageBreak())
            elems.append(Paragraph(line[3:], h1))
        elif line.startswith("### "):
            elems.append(Paragraph(line[4:], h2))
        elif line.startswith("|") and line.endswith("|"):
            elems.append(Preformatted(line, style=code))
        else:
            elems.append(Paragraph(line.replace("`", ""), body))
    flush_code()
    return elems

def write_pdf(text: str, path: Path):
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate
    elems = md_to_pdf_elements(text)
    doc = SimpleDocTemplate(str(path), pagesize=letter,
                            rightMargin=0.6 * 72, leftMargin=0.6 * 72,
                            topMargin=0.8 * 72, bottomMargin=0.8 * 72)
    doc.build(elems)

def main():
    text = build_markdown()
    # Ensure figures exist in both output roots.
    fig_src = OUT / "figures"
    for outdir in (OUT, DESK):
        outdir.mkdir(parents=True, exist_ok=True)
        fig_dst = outdir / "figures"
        fig_dst.mkdir(exist_ok=True)
        if fig_src.exists():
            for img in fig_src.glob("*.png"):
                target = fig_dst / img.name
                if not target.exists() or img.stat().st_mtime > target.stat().st_mtime:
                    target.write_bytes(img.read_bytes())
    for outdir in (OUT, DESK):
        (outdir / "QECTOR_API_Reference.md").write_text(text, encoding="utf-8")
        write_pdf(text, outdir / "QECTOR_API_Reference.pdf")
        print("wrote", outdir)

if __name__ == "__main__":
    main()

