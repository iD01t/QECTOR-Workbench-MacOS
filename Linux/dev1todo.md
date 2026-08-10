> **Created**: 2026-08-04
> **Audited**: 2026-08-04 (empirical verification of every claim)
> **Remediated**: 2026-08-04 (all findings fixed, plus a Zenodo-grade doc upgrade)
> **Extended**: 2026-08-04 (v0.5.3 release prep + publication figure suite ported from SATI_OS)
> **Scope**: doc-gen quality, UX, coverage, publication readiness, release plumbing
> **Status**: ✅ **COMPLETE AND VERIFIED.** 403 tests pass, every button exercised headlessly, every artifact inspected.

---

## Session 3 additions: v0.5.3 release prep and the figure suite

### Version chain repaired
`WORKBENCH_VERSION` had been set to **the backend's** version (0.7.0) while the
public product line is 0.5.x, so the window title, MCP `status` response,
generated manuals and `.deb` package name all claimed the wrong release. Fixed
to **0.5.3**, with a comment recording why the two lines are independent, and
every hardcoded copy removed:

- [x] `version.py` -> 0.5.3 (product), `DOC_GENERATOR_VERSION` -> 0.5.3
- [x] `installer.iss` had `0.5.2` frozen in; it now `#include`s
      `installer_version.iss`, generated from `version.py` at build time
- [x] `scripts/build_installer.py` had `VERSION = "3.5.1"` hardcoded -> reads `version.py`
- [x] `scripts/update_release_assets.py` had `3.5.1` and the counts `47/13/9`
      hardcoded (live values are 56/16/10) -> rewritten to read the version from
      `version.py` and the counts from the live registry, and to manifest whatever
      artifacts are actually present rather than a fixed list
- [x] `EULA.txt` -> v0.5.3, dates refreshed
- [x] `docs/architecture.md`, `docs/api.md`, `README.md`, `README_v3.md`,
      `PROJECT_STATUS.md` version claims corrected; genuine historical
      references ("removed in v0.5.2") deliberately left intact
- [x] all manuals and `docs/` regenerated; `Mac/VERSION` and `Linux/VERSION` -> 0.5.3

### Release plumbing added
- [x] **`CHANGELOG.md`** created (none existed): full 0.5.2 -> 0.5.3 entry
- [x] **`scripts/build_public_bundles.py`** created. The v0.5.2 public zips were
      assembled **by hand** with no script, so a rebuild could not be reproduced.
      The new script refreshes both staging folders, drops payloads from older
      versions, writes per-bundle manifests with real digests, zips to
      `release_assets/`, and **refuses to bundle a payload older than the newest
      source file** unless `--allow-stale` is passed.
- [x] Build junk removed (`frozen_*.txt`, `build_*.done`, and a file literally
      named `=1.24,` from an unquoted pip specifier); `.gitignore` extended to
      cover all three patterns so they cannot come back
- [x] `dist/QectorWorkbench-Portable.exe` rebuilt from current source (56.4 MB)

### Publication figure suite (ported from SATI_OS practice)
Generated reports previously contained **one** figure (a Tanner graph) and a text
table. SATI_OS's analysis scripts are figure-driven, and that is the gap that made
QECTOR's graph generation look weak. Implemented in `doc_generator.py`:

- [x] **`FIGURE_STYLE` house style** applied per figure: white background, print
      DPI (150 screen / 300 saved), consistent fonts, grid at alpha 0.3, top and
      right spines removed. Applied locally so document figures never inherit the
      GUI's dark rcParams and render white-on-white when printed.
- [x] **Figure 1 Tanner graph** (existing, now numbered and captioned)
- [x] **Figure 2 parity-check sparsity pattern**: square cells, cell borders while
      still resolvable, density and row/column weight range stated
- [x] **Figure 3 mean latency by decoder**: sorted fastest first, every bar
      labelled, fastest marked with a reference line, automatic log scale when the
      spread exceeds two orders of magnitude (and the axis says so)
- [x] **Figure 4 logical failure fraction**: bars coloured against the physical
      error rate, reference line at *p*, and the **sampling resolution limit
      (1/25) stated on the figure** so a zero bar is not read as "never fails"
- [x] **Figure 5 speed against accuracy**: Pareto front computed and marked,
      dominated points greyed
- [x] All five embedded in the **PDF** (300 dpi, numbered captions), the **HTML**
      (base64 data URIs, so the report stays a single self-contained archivable
      file) and the **Markdown** (sibling PNGs, relative links)
- [x] New numbered "Figures" section in the TOC of all three formats

Three defects were found and fixed by looking at the rendered output rather than
trusting the code:

- [x] **Bar labels floated far above short bars on a log axis** because the pad was
      additive in data units. Now offset in points, so the gap is identical on
      linear and log scales.
- [x] **The Pareto plot was an unreadable smear of overlapping labels** when many
      decoders shared a value. Now only the Pareto front, anything that actually
      failed, and the slowest decoder are labelled; the remainder is summarised
      honestly in a note ("12 further decoders recorded zero failures in 25 trials,
      spanning 0.105 to 1.503 ms").
- [x] **The parity-matrix annotation collided with the title** and `aspect="auto"`
      stretched cells into bars. Annotation moved below the axis, aspect made
      square for matrices that fit.

---

## What happened

The original pass in this file self-reported "ALL PHASES COMPLETE (100%)" without
running anything. An empirical audit (real `QectorApp`, `filedialog` stubbed to a
temp dir, every format generated and inspected) found:

* **5 claimed-done items broken at runtime** (4 export buttons silently no-oped, 1 called a method that does not exist)
* **6 items never implemented** (HTML TOC, preview highlighting, preview zoom/search, recent folders, progress readout, clipboard exporter)
* **2 regressions** (the Buy Licence section deleted, the test suite turned red)
* **1 false cleanup claim** (the hardcoded developer desktop path was still there)

All of it is now fixed, and the doc generator has been raised to deposit-ready
quality on top. Evidence is inline below.

| | before audit | after remediation |
|---|---|---|
| Tabs whose export button **works** | 2 of 7 | **7 of 7** |
| Test suite | 2 failing | **403 passed, 4 skipped, 0 failed** |
| Doc formats | 6 | **8** (+ `.zenodo.json`, `CITATION.cff`) |
| Typographic dashes in output | throughout | **0 across every rendered artifact** |
| Remote network calls from a generated report | 1 (Google Fonts) | **0** |
| Fabricated author identity in deposits | yes | **none, ever** |

---

## 🔴 BROKEN, now fixed

### B1. `Path` used but never imported: 4 export buttons silently no-oped ✅ FIXED
Each handler wrapped its body in a bare `except Exception` and only logged, so the
user clicked Export, picked a filename, and nothing happened.

- [x] **B1.1** `benchmark_tab.py` added `from pathlib import Path`
- [x] **B1.2** `batch_streaming_tab.py` same
- [x] **B1.3** `diagnostics_tab.py` same
- [x] **B1.4** `hardware_tab.py` same

Before: `Export failed: name 'Path' is not defined`, `file_written=False` on all four.
After: `file_written=True` on all four, files verified on disk.

### B2. Decoder Lab called a method that does not exist ✅ FIXED
- [x] **B2.1** `decoder_lab_tab.py` called `generator.generate(...)`; the class only
      exposes `generate_all()`. Now calls `generate_all(code, formats=["markdown",
      "html", "pdf"])`, reports which formats succeeded, which failed, and the
      output folder. Verified live.
- [x] **B2.2** Quick Export had no real guard and exported the traceback as a
      "Decode Report". It now refuses unless `_last_decode_result` is set and the
      pane holds an actual decode, not a placeholder or a status notice.

### B3. Test suite turned red ✅ FIXED
- [x] **B3.1** `EXPECTED_TABS` updated for the new "Lab & Personal Info" tab, and the
      hardcoded "8 named tabs" message now derives from the list.
- [x] **B3.2** *(pre-existing, also fixed)* `test_batch_and_streaming_live` selected
      CUDA whenever a device was present, but GPU batch is **Enterprise-tier gated**.
      On a Community licence it failed with a misleading "batch decode did not
      complete". It now detects the tier refusal and falls back to CPU, so the
      end-to-end path is still tested on any host.

### B4. Hardcoded developer desktop path ✅ FIXED
- [x] **B4.1** `generate_manuals.py` no longer writes to
      `C:\Users\<developer>\Desktop\manuals`. Mirrors are opt-in via `--also DIR`
      (repeatable) or `QECTOR_MANUALS_MIRROR`. The script now runs on any machine.

---

## 🟠 NEVER IMPLEMENTED, now implemented

- [x] **F1** HTML section TOC: `<nav class="toc">` with 8 entries, 8 matching
      `id="sec-*"` anchors. Verified: `href="#"` count 8, `id=` count 8.
- [x] **F2** Preview syntax highlighting: 5 tag classes (headings, paths, keys,
      errors, numbers) applied on every preview update, re-applied when the text changes.
- [x] **F3** Preview zoom and search: `A+`/`A-` step the font 8pt to 22pt with a live
      readout; the search box marks all hits, Enter cycles forward, Shift+Enter back,
      with an "n of m" counter and scroll-into-view.
- [x] **F4** Recent export folders: persisted to `~/.qector/recent_export_dirs.json`
      (8 deep, newest first), surfaced as a dropdown that opens any past folder.
- [x] **F5** Real progress reporting: the readout now moves through
      "Generating N format(s)" to "Done: N file(s) written" / "N written, M failed" /
      "Generation failed", colour-coded, and mirrors into the app status bar when the
      host exposes one. Previously it was created saying "Ready" and never touched again.
- [x] **F6** Clipboard export: rewritten as `docs_exporter.copy_to_clipboard(text,
      widget=...)` and wired to a **Copy** button on the preview toolbar.

---

## 🔺 REGRESSIONS, now reversed

- [x] **R1** **Buy Licence restored.** `_build_licence_section` is called again from
      `_build_ui`, so the Documentation tab once more shows Developer & Licensing with
      **Buy Licence** (qector.store/pricing), **Contact Sales** and **Website**. The
      section had been orphaned (84 lines of dead code) by dropping the call, silently
      removing the app's only purchase path.
- [x] **R2** `_build_actions` dead code removed by folding its behaviour into the top
      action bar (it also re-bound `self.generate_btn`, which would have clobbered the
      real button).
- [x] **R3** Watermark is one value again. `WATERMARK` is the provenance constant;
      the operator's optional header override comes from the profile and is applied
      consistently to Markdown, HTML, LaTeX, SVG, JSON and every PDF page.

---

## 🟡 QUALITY DEFECTS, now fixed

- [x] **Q1** "Generate and Open Folder" no longer races. It sets
      `_open_folder_when_done`; `_on_generate_done` opens the folder only after the
      worker has written the files, and not at all if generation was refused or failed.
- [x] **Q2** DOCX is honest. The "write raw Markdown into a .docx and return True"
      fallback is gone: a file Word cannot open is worse than a missing file.
      `export_to_docx` returns `(ok, message)`, `python-docx` is declared in
      `requirements.txt` and installed. Verified: real DOCX, 42 KB, ZIP magic `PK\x03\x04`.
- [x] **Q3** Clipboard uses the app's own Tk root via a passed widget, instead of
      creating a second `tk.Tk()` inside a live CustomTkinter app (the flakiness
      pattern `lastdev.md` §4.3 warns about) and destroying it before the paste.
- [x] **Q4** `QECTOR_API_Reference.html` is a real document. It was the whole Markdown
      source dumped into one unescaped `<pre>`. A dependency-free renderer now emits
      headings, tables, lists, code blocks, blockquotes, images and links, with every
      literal span HTML-escaped first. Verified: 8 tables, 17 `<h2>`, 148 `<li>`,
      and `dict[str, Any]` survives intact.
- [x] **Q5** Google Fonts `@import` removed. A generated report no longer calls out to
      a CDN on every open (reader-IP leak, and `CMU Serif` is not a Google font anyway).
      Fonts resolve locally; the document renders identically offline.
- [x] **Q6** `lab_info` save is honest. `save_lab_info` returns `(ok, message)` and the
      UI shows the real outcome. It previously always said "Profile saved successfully!"
      even when the write raised.
- [x] **Q7** The licence key field is real. It writes `~/.qector/license.key` (mode 600
      where the OS supports it), sets `QECTOR_LICENSE_KEY`, hands the key to the
      decoder's own `set_license_key`/`activate_license` for Ed25519 verification, and
      shows the resulting tier. It previously wrote plaintext into a profile file that
      nothing read, so an Enterprise key silently did nothing. The tier readout is live:
      `Community (max distance 7; GPU disabled; GNN disabled)`.
- [x] **Q8** All four tab HTML exporters now `html.escape` before interpolating into
      `<pre>`, so a `<` in a decoder name or error string cannot break the report.
- [x] **Q9** Benchmark button relabelled **📊 Export Report** (it said "Export JSON"
      while offering three formats) and `defaultextension` changed to `.html` so the
      first filter entry matches the default.
- [x] **Q10** No fabricated identity. "Dr. Lead Researcher" / `contact@qector.org` are
      gone; every profile field defaults to empty and an unset profile renders as
      "Unattributed (set your profile in Lab and Personal Info)", plus an explicit note
      in the PDF telling the user to set a profile before depositing.
- [x] **Q11** JSON carries both `generator` and `generator_version`; schema bumped to
      `1.2` for the new `publication` block.
- [x] **Q12** Stale docstrings corrected: the module docstring no longer claims
      "PDF (matplotlib multi-page)", and `_stamp_watermark` no longer claims to stamp
      every PDF page (ReportLab's page callback does that).
- [x] **Q13** Unused imports removed (`html`, `subprocess` in `docs_exporter.py`;
      `tkinter`, `Any`, `Optional` in `lab_info_tab.py`).

---

## 📚 Zenodo-grade upgrade

Generated documents are now deposit ready rather than merely well formatted.

- [x] **Z1** **Deposit sidecars.** Two new formats: `.zenodo.json` (upload_type,
      publication_type, creators with ORCID and affiliation, keywords, licence,
      access_right, language, version) and `CITATION.cff` (Citation File Format 1.2.0).
      Both are record-level, so a deposit carries exactly one of each.
- [x] **Z2** **YAML front matter** on the Markdown: title, authors with ORCID and
      affiliation, date, licence, keywords, resource_type, DOI. Pandoc and Quarto
      consume it directly.
- [x] **Z3** **Publication metadata layer** (`_publication_metadata`) shared by every
      format, so Markdown, HTML, LaTeX, PDF and both sidecars cannot disagree.
- [x] **Z4** **Real scientific structure**: Abstract, Code Parameters, Structural
      Analysis, Decoder Benchmark, **Methods**, **Data Availability**, **How to Cite**,
      Provenance. The Methods section states the seeding scheme
      (`seed = {base} + i`), what latency excludes, and that the failure fraction at
      25 trials is a screening estimate and not a converged logical error rate.
- [x] **Z5** **Licence and citation** in every format: CC-BY-4.0 by default, with a
      formatted citation string and the licence URL.
- [x] **Z6** **PDF metadata** carries title, author, keywords and subject; the report
      body gains a citation block, a funding line when set, and an explicit warning
      when no author profile is set.
- [x] **Z7** **New profile fields**: ORCID, DOI, funding, publisher and extra keywords
      (which extend the standing subject list rather than replacing it).

### No dashes
- [x] **Z8** `_nodash()` purges em dashes, en dashes, figure dashes, horizontal bars,
      Unicode minus and the `&mdash;`/`&ndash;`/`&minus;` entities from **every rendered
      artifact**, applied at the single write choke point in `generate_all`.
      It is line-aware: Markdown table rules, YAML fences and LaTeX booktabs rules are
      exempt, leading indentation is preserved, and hyphens inside identifiers
      (`qector-decoder-v3`, `bp-osd`) are untouched. JSON payloads stay byte-exact.
      Verified: **0 dashes** in `.md`, `.html`, `.tex`, `.svg`, `.json`, `.zenodo.json`
      and `CITATION.cff`.

---

## ✅ Evidence

```
pytest tests/                      403 passed, 4 skipped, 0 failed  (was 2 failed)
export handlers driven headlessly  7 of 7 tabs write real files     (was 2 of 7)
doc formats generated              8 of 8 ok
dash audit                         0 typographic dashes in every rendered artifact
HTML                               8 TOC anchors, 8 section ids, 0 remote requests
PDF                                %PDF-1.4, Producer ReportLab, searchable, watermark per page
official docs export               15 of 15 artifacts, DOCX valid (ZIP magic), 2.0s
API reference HTML                 8 tables, 17 h2, 148 li  (was one unescaped <pre>)
licence tier readout               Community (max distance 7; GPU disabled; GNN disabled)
three OS trees                     root / Linux / Mac byte-identical on all 13 changed files
```

## 📇 Contact

- [x] `version.CONTACT_EMAIL`, the `.deb` maintainer field and README support row
      updated to **admin@qector.store**; `manuals/` and `docs/` regenerated so the
      shipped documentation set carries it (`Sales contact : admin@qector.store`).

---

## Files changed (sessions 1-3)

`benchmark_tab.py`, `batch_streaming_tab.py`, `diagnostics_tab.py`, `hardware_tab.py`,
`decoder_lab_tab.py`, `documentation_tab.py`, `doc_generator.py`, `docs_exporter.py`,
`lab_info_tab.py`, `api_reference.py`, `generate_manuals.py`, `version.py`,
`build_production.py`, `requirements.txt`, `README.md`, `tests/test_gui_smoke.py`
— all synced to `Linux/` and `Mac/`.

---

## Session 4: v1.0.0 Phase 2 — remaining features

> **Started**: 2026-08-06
> **Scope**: GUI enhancements, testing infrastructure, security hardening, documentation tooling

### GUI Enhancements
- [x] **G1** Experiment history panel (decode log with timestamps)
- [x] **G2** Side-by-side decoder comparison view
- [x] **G3** Progressive rendering for large Tanner graphs
- [x] **G4** Accessibility (a11y): high-contrast theme, font slider, keyboard hints
- [x] **G5** Internationalization (i18n): English, French, Japanese
- [x] **G6** Print/report preview (in-app PDF widget)
- [x] **G7** Dark/light theme toggle persisted in preferences
- [x] **G8** Additional visualizations (2D lattice, radar chart)
- [x] **G9** Real-time streaming visualization (live chart)
- [x] **G10** Batch job queue with progress tracking

### Testing Infrastructure
- [x] **T1** Performance regression test (baseline comparison)
- [x] **T2** Memory leak test (RSS growth monitoring)
- [x] **T3** GUI integration test (headless smoke)

### Security Hardening
- [x] **S1** Input length limits (paths, names, fields)
- [x] **S2** CSRF protection on MCP (connection handshake token)
- [x] **S3** Dependency vulnerability scanning (`pip-audit`)
- [x] **S4** Secret detection in CI (`check_secrets.py`)

### Documentation Tooling
- [x] **D1** API reference completeness check (`check_docstrings.py`)
- [x] **D2** Changelog automation from git history
- [x] **D3** Architecture diagrams (Mermaid)
