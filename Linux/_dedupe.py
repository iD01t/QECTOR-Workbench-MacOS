"""Deduplicate the v1.0.0 block in mcp_server.py.

The previous edit accidentally inserted the block four times because the
closing marker matched a later copy. Keep the first copy, drop the rest,
and rewrite the description references in the kept copy to use the
module-level names so the registration can run at module level.
"""
from pathlib import Path

p = Path(r"D:\QECTOR APP\mcp_server.py")
text = p.read_text(encoding="utf-8")

# Find every copy of the v1.0.0 tool registration block. Each copy starts
# with the handlers (def _handle_build_dem...) and ends with the duplicated
# `async def call_mcp_tool` block.
import re

# Find all positions of `_handle_build_dem`
positions = [m.start() for m in re.finditer(r"^def _handle_build_dem", text, re.M)]
print("found", len(positions), "copies of _handle_build_dem")

# We want to keep the LAST copy (it's the most recent addition) and
# everything after it (which is _register_v1_tools and downstream).
# Drop everything between the original "async def call_mcp_tool" end and
# the start of the LAST _handle_build_dem.

# Find the start of the v1.0.0 block (the first call_mcp_tool after analyze_error_patterns)
# and the start of the last _handle_build_dem
last_pos = positions[-1]
print("last copy starts at line", text[:last_pos].count("\n") + 1)

# Find the position right after the original `async def call_mcp_tool` block
# (the first one). The first call_mcp_tool after analyze_error_patterns.
first_call = text.find("async def call_mcp_tool(name: str, params: dict[str, Any]) -> Any:")
print("first call_mcp_tool at line", text[:first_call].count("\n") + 1)

# Strategy: keep everything from the start to first_call (inclusive), then
# jump to last_pos, then keep everything from last_pos to end.
new_text = text[:first_call] + text[last_pos:]
print(f"old lines: {text.count(chr(10))}, new lines: {new_text.count(chr(10))}")

# Now fix the description references in the kept v1.0.0 block
old_block = new_text
new_block = old_block.replace("description\": _family_desc", "description\": _FAMILY_DESC")
new_block = new_block.replace("description\": _decoder_desc", "description\": _DECODER_DESC")
new_block = new_block.replace("description\": _options_desc", "description\": _OPTIONS_DESC")

p.write_text(new_block, encoding="utf-8")
print("rewrote", p)
