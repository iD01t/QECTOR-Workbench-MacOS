"""One-shot: rewrite the v1.0.0 tool registration block to use module-level
description names so the function can be called from outside ``_build_registry``.
"""
import sys
from pathlib import Path

p = Path(r"D:\QECTOR APP\mcp_server.py")
text = p.read_text(encoding="utf-8")

start_marker = "def _register_v1_tools() -> None:"
end_marker = "async def call_mcp_tool"
i = text.find(start_marker)
j = text.find(end_marker)
if i < 0 or j < 0:
    sys.exit("markers not found")

block = text[i:j]
old_block = block
block = block.replace("description\": _family_desc", "description\": _FAMILY_DESC")
block = block.replace("description\": _decoder_desc", "description\": _DECODER_DESC")
block = block.replace("description\": _options_desc", "description\": _OPTIONS_DESC")

n_fam = old_block.count("description\": _family_desc")
n_dec = old_block.count("description\": _decoder_desc")
n_opt = old_block.count("description\": _options_desc")

if n_fam + n_dec + n_opt == 0:
    # Diagnostic: show what's actually in the block
    sample = old_block[:300]
    sys.stderr.write(f"no replacements; first 300 chars of block: {sample!r}\n")
    sys.exit(2)

p.write_text(text[:i] + block + text[j:], encoding="utf-8")
print(f"rewrote {n_fam} family + {n_dec} decoder + {n_opt} options refs")
