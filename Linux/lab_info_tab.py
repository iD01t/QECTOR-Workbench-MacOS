"""lab_info_tab.py: lab, author and deposit metadata for generated documentation.

The profile saved here is what turns a generated report into a depositable
record: creator name, ORCID, affiliation, DOI, funding and keywords all flow
into the Markdown front matter, the PDF metadata, ``.zenodo.json`` and
``CITATION.cff``.

Two rules the rest of the app relies on:

* **No invented identity.** Every field defaults to empty. A report generated
  from an unset profile says so explicitly rather than shipping a plausible
  fake researcher name, which would be worse than no attribution at all.
* **The licence key is a real key.** It is written to the location the decoder
  actually reads (``~/.qector/license.key`` plus the process environment), not
  to a profile file nothing consults, and the resulting tier is reported back.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

try:
    import customtkinter as ctk
    _HAS_GUI = True
except Exception:
    _HAS_GUI = False

import theme

_QECTOR_DIR = Path.home() / ".qector"
_CONFIG_PATH = _QECTOR_DIR / "lab_info.json"
#: Where qector_decoder_v3 looks for a licence key when the environment is unset
#: (see qector_decoder_v3/license.py: QECTOR_LICENSE_KEY, then
#: QECTOR_LICENSE_FILE, then this path).
_LICENSE_KEY_PATH = _QECTOR_DIR / "license.key"

#: Profile fields, in display order: (key, label, placeholder hint).
PROFILE_FIELDS: tuple[tuple[str, str, str], ...] = (
    ("author", "Lead Author / PI Name", "Ada Lovelace"),
    ("orcid", "ORCID iD", "0000-0002-1825-0097"),
    ("institution", "Institution / University", "Example University"),
    ("department", "Department / Division", "Department of Physics"),
    ("email", "Contact Email", "you@example.edu"),
    ("website", "Lab Website URL", "https://lab.example.edu"),
    ("doi", "Reserved DOI (optional)", "10.5281/zenodo.0000000"),
    ("funding", "Funding / Grant (optional)", "NSF PHY-0000000"),
    ("publisher", "Publisher / Repository", "Zenodo"),
    ("keywords", "Extra Keywords (comma separated)", "topological codes, BP-OSD"),
    ("watermark", "Report Header / Watermark", "Internal draft, do not circulate"),
)

#: Every field defaults to empty: an unset profile must never look like a set one.
_DEFAULTS: dict[str, str] = {key: "" for key, _label, _hint in PROFILE_FIELDS}


def load_lab_info() -> dict[str, str]:
    """Load the saved lab and author profile.

    Returns every known field, with unset ones as empty strings.  Never raises:
    a corrupt or unreadable profile yields the empty profile.
    """
    info = dict(_DEFAULTS)
    try:
        if _CONFIG_PATH.exists():
            data = json.loads(_CONFIG_PATH.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                for key, value in data.items():
                    if key in _DEFAULTS:
                        info[key] = "" if value is None else str(value)
    except Exception:
        pass
    # A licence key must never be carried in the documentation profile: it is
    # secret, and it belongs in the file the decoder reads. Drop it on load so a
    # profile written by an older build cannot leak into a generated report.
    info.pop("license_key", None)
    return info


def save_lab_info(info: dict[str, str]) -> tuple[bool, str]:
    """Persist the profile.

    Returns ``(ok, message)``.  The caller is expected to surface the message:
    silently swallowing a failed write and reporting success is how a user ends
    up depositing a record with no creator.
    """
    payload = {k: str(v) for k, v in info.items() if k != "license_key"}
    try:
        _CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        _CONFIG_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return True, f"Profile saved to {_CONFIG_PATH}"
    except Exception as exc:
        return False, f"Could not save profile: {type(exc).__name__}: {exc}"


def current_licence_tier() -> str:
    """Report the decoder's current licence tier and what it unlocks.

    Reads ``qector_decoder_v3.get_license_info()``, which is the same source the
    decoder enforces against, so the tier shown here is the tier that will
    actually gate a GPU batch decode.
    """
    try:
        import qector_decoder_v3 as qd
    except Exception as exc:
        return f"decoder unavailable ({type(exc).__name__})"
    try:
        info = qd.get_license_info()
    except Exception as exc:
        return f"tier unreadable ({type(exc).__name__}: {exc})"
    if not isinstance(info, dict):
        return str(info)

    tier = str(info.get("tier", "unknown"))
    bits = [tier]
    if info.get("key_status") and info["key_status"] != "no_key":
        bits.append(f"key {info['key_status']}")
    if info.get("is_expired"):
        bits.append("EXPIRED")
    caps = []
    if info.get("max_distance") is not None:
        caps.append(f"max distance {info['max_distance']}")
    caps.append("GPU " + ("enabled" if info.get("gpu_enabled") else "disabled"))
    caps.append("GNN " + ("enabled" if info.get("gnn_enabled") else "disabled"))
    return ", ".join(bits) + " (" + "; ".join(caps) + ")"


def apply_license_key(key: str) -> tuple[bool, str]:
    """Install a licence key where the decoder will actually find it.

    Writes ``~/.qector/license.key`` (encrypted) and sets ``QECTOR_LICENSE_KEY`` for this
    process, then reports the tier the decoder resolves.  An empty key clears
    the stored file.  Returns ``(ok, message)``.
    """
    key = (key or "").strip()
    try:
        import utils
        _QECTOR_DIR.mkdir(parents=True, exist_ok=True)
        if not key:
            if _LICENSE_KEY_PATH.exists():
                _LICENSE_KEY_PATH.unlink()
            os.environ.pop("QECTOR_LICENSE_KEY", None)
            return True, "Licence key cleared. Tier: " + current_licence_tier()

        encrypted = utils.encrypt_license_key(key)
        _LICENSE_KEY_PATH.write_text(encrypted + "\n", encoding="utf-8")
        try:
            os.chmod(_LICENSE_KEY_PATH, 0o600)
        except Exception:
            pass  # best effort; Windows ACLs are not POSIX modes
        os.environ["QECTOR_LICENSE_KEY"] = key

        # Hand the key to the decoder's own entry point: it verifies the Ed25519
        # signature rather than trusting whatever landed in the file.
        try:
            import qector_decoder_v3 as qd
            applied = False
            for attr in ("set_license_key", "activate_license"):
                fn = getattr(qd, attr, None)
                if callable(fn):
                    fn(key)
                    applied = True
                    break
            if not applied:
                from qector_decoder_v3 import license as _lic
                _lic.activate_license(key)
        except Exception as exc:
            return True, (f"Key written to {_LICENSE_KEY_PATH}, but the decoder rejected it: "
                          f"{exc}. Tier: {current_licence_tier()}")
        return True, f"Key installed at {_LICENSE_KEY_PATH}. Tier: {current_licence_tier()}"
    except Exception as exc:
        return False, f"Could not install licence key: {type(exc).__name__}: {exc}"


if _HAS_GUI:

    class LabInfoTab(ctk.CTkFrame):
        """Tab for the deposit profile: author, affiliation, DOI and licence key."""

        def __init__(self, master, state=None, console=None, fonts=None, **kwargs):
            super().__init__(master, fg_color="transparent", **kwargs)
            self.state = state
            self.console = console
            self.fonts = fonts if fonts is not None else theme.get_fonts()

            self.grid_columnconfigure(0, weight=1)
            self.grid_rowconfigure(0, weight=1)

            scroll = ctk.CTkScrollableFrame(self, fg_color=theme.c("bg_panel"), corner_radius=10)
            scroll.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
            scroll.grid_columnconfigure(1, weight=1)

            ctk.CTkLabel(
                scroll, text="Lab and Author Profile",
                font=ctk.CTkFont(family=self.fonts.heading, size=18, weight="bold"),
                text_color=theme.c("text_primary"),
            ).grid(row=0, column=0, columnspan=2, sticky="w", padx=20, pady=(20, 4))

            ctk.CTkLabel(
                scroll,
                text=("These values become the creator, affiliation and licence metadata of every "
                      "generated report, including the Zenodo deposit sidecars. Leave a field "
                      "empty rather than guessing: reports state plainly when the profile is unset."),
                font=ctk.CTkFont(family=self.fonts.ui, size=11),
                text_color=theme.c("text_secondary"),
                wraplength=660, justify="left",
            ).grid(row=1, column=0, columnspan=2, sticky="w", padx=20, pady=(0, 16))

            info = load_lab_info()
            self.entries: dict[str, ctk.CTkEntry] = {}

            row_idx = 2
            for key, label_text, hint in PROFILE_FIELDS:
                ctk.CTkLabel(
                    scroll, text=f"{label_text}:",
                    font=ctk.CTkFont(family=self.fonts.ui, size=12, weight="bold"),
                    text_color=theme.c("text_primary"),
                ).grid(row=row_idx, column=0, sticky="w", padx=(20, 10), pady=6)

                entry = ctk.CTkEntry(
                    scroll, width=450, placeholder_text=hint,
                    font=ctk.CTkFont(family=self.fonts.ui, size=12),
                )
                value = info.get(key, "")
                if value:
                    entry.insert(0, value)
                entry.grid(row=row_idx, column=1, sticky="ew", padx=(0, 20), pady=6)
                self.entries[key] = entry
                row_idx += 1

            # ---- Licence key: separate, because it is a secret, not metadata ----
            ctk.CTkLabel(
                scroll, text="Decoder Licence Key:",
                font=ctk.CTkFont(family=self.fonts.ui, size=12, weight="bold"),
                text_color=theme.c("text_primary"),
            ).grid(row=row_idx, column=0, sticky="w", padx=(20, 10), pady=6)

            self.license_entry = ctk.CTkEntry(
                scroll, width=450, show="*",
                placeholder_text="paste an Enterprise key to raise the tier",
                font=ctk.CTkFont(family=self.fonts.mono, size=12),
            )
            self.license_entry.grid(row=row_idx, column=1, sticky="ew", padx=(0, 20), pady=6)
            row_idx += 1

            ctk.CTkLabel(
                scroll,
                text=(f"Stored at {_LICENSE_KEY_PATH}, which is where the decoder looks. "
                      "It is never written into the profile file and never appears in a "
                      "generated report."),
                font=ctk.CTkFont(family=self.fonts.ui, size=10),
                text_color=theme.c("text_secondary"),
                wraplength=640, justify="left",
            ).grid(row=row_idx, column=1, sticky="w", padx=(0, 20), pady=(0, 8))
            row_idx += 1

            self.tier_label = ctk.CTkLabel(
                scroll, text=f"Current tier: {current_licence_tier()}",
                font=ctk.CTkFont(family=self.fonts.mono, size=11),
                text_color=theme.c("text_secondary"),
            )
            self.tier_label.grid(row=row_idx, column=1, sticky="w", padx=(0, 20), pady=(0, 4))
            row_idx += 1

            # ── License info detail section ──────────────────────────────
            def _get_license_details() -> dict:
                """Pull raw fields from the decoder, not the formatted summary."""
                try:
                    import qector_decoder_v3 as qd
                    return qd.get_license_info() or {}
                except Exception:
                    return {}

            lic_details = _get_license_details()
            self._lic_detail_labels: dict[str, ctk.CTkLabel] = {}

            lic_detail_frame = ctk.CTkFrame(scroll, fg_color="transparent")
            lic_detail_frame.grid(row=row_idx, column=0, columnspan=2, sticky="we", padx=20, pady=(0, 8))

            # Section header
            ctk.CTkLabel(
                lic_detail_frame, text="License Details",
                font=ctk.CTkFont(family=self.fonts.ui, size=12, weight="bold"),
                text_color=theme.c("text_primary"),
            ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 6))

            detail_fields = [
                ("tier", "Tier"),
                ("key_status", "Key Status"),
                ("is_expired", "Expired"),
                ("max_distance", "Max Distance"),
                ("gpu_enabled", "GPU"),
                ("gnn_enabled", "GNN"),
            ]
            for col, (key, label) in enumerate(detail_fields):
                ctk.CTkLabel(
                    lic_detail_frame, text=f"{label}:",
                    font=ctk.CTkFont(family=self.fonts.ui, size=11),
                    text_color=theme.c("text_secondary"),
                ).grid(row=1, column=col * 2, sticky="w", padx=(0 if col == 0 else 8, 2), pady=2)
                raw = lic_details.get(key)
                display = str(raw) if raw is not None else "N/A"
                if key in ("gpu_enabled", "gnn_enabled"):
                    display = "Enabled" if raw else "Disabled"
                if key == "is_expired":
                    display = "Yes" if raw else "No"
                lbl = ctk.CTkLabel(
                    lic_detail_frame, text=display,
                    font=ctk.CTkFont(family=self.fonts.mono, size=11),
                    text_color=theme.c("accent") if raw and key not in ("is_expired",) else theme.c("text_secondary"),
                )
                lbl.grid(row=1, column=col * 2 + 1, sticky="w", pady=2)
                self._lic_detail_labels[key] = lbl

            row_idx += 1


            btn_row = ctk.CTkFrame(scroll, fg_color="transparent")
            btn_row.grid(row=row_idx, column=0, columnspan=2, sticky="we", padx=20, pady=24)
            btn_row.grid_columnconfigure(2, weight=1)

            btn_save = ctk.CTkButton(
                btn_row, text="Save Profile", width=120, height=28,
                command=self._on_save,
                font=ctk.CTkFont(family=self.fonts.ui, size=11, weight="bold"),
                fg_color=theme.c("accent"),
            )
            btn_save.grid(row=0, column=0, sticky="w")

            self.lbl_status = ctk.CTkLabel(
                btn_row, text="",
                font=ctk.CTkFont(family=self.fonts.ui, size=11),
                text_color=theme.c("success"), wraplength=520, justify="left",
            )
            self.lbl_status.grid(row=0, column=1, sticky="w", padx=15)

            # ---- Appearance Theme Dropdown ----
            ctk.CTkLabel(
                btn_row, text="Theme:",
                font=ctk.CTkFont(family=self.fonts.ui, size=11),
                text_color=theme.c("text_secondary"),
            ).grid(row=0, column=2, sticky="e", padx=(0, 10))

            self.theme_dropdown = ctk.CTkOptionMenu(
                btn_row, values=["Dark", "Light", "High Contrast"],
                command=self._on_theme_change, width=120, height=28,
            )
            # Default to current theme state (e.g. Dark)
            self.theme_dropdown.set(theme._current_mode)
            self.theme_dropdown.grid(row=0, column=3, sticky="e", padx=(0, 20))

            # ---- Language Dropdown ----
            ctk.CTkLabel(
                btn_row, text="Language:",
                font=ctk.CTkFont(family=self.fonts.ui, size=11),
                text_color=theme.c("text_secondary"),
            ).grid(row=0, column=4, sticky="e", padx=(10, 10))

            self.lang_dropdown = ctk.CTkOptionMenu(
                btn_row, values=["English", "French", "Japanese"],
                command=self._on_lang_change, width=100, height=28,
            )
            self.lang_dropdown.set("English")
            self.lang_dropdown.grid(row=0, column=5, sticky="e", padx=(0, 20))

            row_idx += 1
            # ---- Accessibility Font Slider & Hints ----
            a11y_frame = ctk.CTkFrame(scroll, fg_color="transparent")
            a11y_frame.grid(row=row_idx, column=0, columnspan=2, sticky="we", padx=20, pady=10)
            a11y_frame.grid_columnconfigure(1, weight=1)

            ctk.CTkLabel(
                a11y_frame, text="Font Scaling (a11y):",
                font=ctk.CTkFont(family=self.fonts.ui, size=12, weight="bold"),
                text_color=theme.c("text_primary"),
            ).grid(row=0, column=0, sticky="w", padx=(0, 10))

            self.font_scale_slider = ctk.CTkSlider(
                a11y_frame, from_=0.8, to=1.6, number_of_steps=8,
                command=self._on_font_scale_change, width=200,
            )
            self.font_scale_slider.set(1.0)
            self.font_scale_slider.grid(row=0, column=1, sticky="w")

            ctk.CTkLabel(
                scroll,
                text="Keyboard Shortcuts Hint:\n"
                     "• Ctrl+N: Clear/New Code    • Ctrl+R: Run Decode    • F5: Refresh Plots\n"
                     "• Ctrl+D: Gen Report        • Ctrl+S: Save Profile",
                font=ctk.CTkFont(family=self.fonts.ui, size=11, slant="italic"),
                text_color=theme.c("text_secondary"),
                justify="left",
            ).grid(row=row_idx+1, column=0, columnspan=2, sticky="w", padx=20, pady=(10, 15))

            row_idx += 2
            btn_frame = ctk.CTkFrame(scroll, fg_color="transparent")
            btn_frame.grid(row=row_idx, column=0, columnspan=2, sticky="w", padx=20, pady=(0, 24))

            self.apply_license_btn = ctk.CTkButton(
                btn_frame, text="Apply Licence Key", command=self._on_apply_license,
                font=ctk.CTkFont(size=12), width=160,
                fg_color=theme.COLORS.get("bg_widget", "#3A3D4E"),
            )
            self.apply_license_btn.pack(side="left")

        def _on_theme_change(self, mode: str) -> None:
            theme.set_appearance_mode(mode)

        def _on_lang_change(self, val: str) -> None:
            try:
                import i18n
                lang_map = {"English": "en", "French": "fr", "Japanese": "ja"}
                i18n.set_language(lang_map.get(val, "en"))
                self._log(f"Language set to {val}", "INFO")
            except Exception as e:
                self._log(f"Failed to change language: {e}", "ERROR")

        def _on_font_scale_change(self, value: float) -> None:
            try:
                import customtkinter as ctk
                ctk.set_widget_scaling(value)
                self._log(f"Font scale set to {value:.2f}", "INFO")
            except Exception as e:
                self._log(f"Failed to change font scaling: {e}", "ERROR")

        def _set_status(self, text: str, ok: bool = True) -> None:
            try:
                self.lbl_status.configure(
                    text=text,
                    text_color=theme.c("success") if ok else theme.c("error"),
                )
                self.after(8000, lambda: self.status_label.configure(text=""))
            except Exception:
                pass

        def _log(self, message: str, level: str = "INFO") -> None:
            if self.console is not None:
                try:
                    self.console.log(message, level)
                except Exception:
                    pass

        def _on_save(self) -> None:
            data = {k: entry.get().strip() for k, entry in self.entries.items()}
            ok, message = save_lab_info(data)
            self._set_status(message, ok)
            self._log(message, "SUCCESS" if ok else "ERROR")

        def _on_apply_license(self) -> None:
            ok, message = apply_license_key(self.license_entry.get())
            self._set_status(message, ok)
            self._log(message, "SUCCESS" if ok else "ERROR")
            try:
                self.tier_label.configure(text=f"Current tier: {current_licence_tier()}")
            except Exception:
                pass
            # Refresh the detail labels
            try:
                import qector_decoder_v3 as qd
                details = qd.get_license_info() or {}
                for key, lbl in getattr(self, "_lic_detail_labels", {}).items():
                    raw = details.get(key)
                    if key in ("gpu_enabled", "gnn_enabled"):
                        display = "Enabled" if raw else "Disabled"
                    elif key == "is_expired":
                        display = "Yes" if raw else "No"
                    else:
                        display = str(raw) if raw is not None else "N/A"
                    lbl.configure(text=display)
            except Exception:
                pass

else:
    class LabInfoTab:
        def __init__(self, master=None, state=None, console=None, fonts=None, **kwargs):
            pass
