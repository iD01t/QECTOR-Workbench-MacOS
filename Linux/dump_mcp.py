"""Quick dump of which MCP tools are registered."""
import sys
sys.path.insert(0, r"D:\QECTOR APP")
import mcp_server
s = mcp_server.get_mcp_server()
tools = sorted(s.tools._tools.keys())
print("total tools:", len(tools))
for needed in (
    "decode_hyperedge", "run_ler_benchmark", "get_backend_health",
    "get_server_env", "export_figure", "export_session", "import_stim",
    "decode_dem", "build_dem", "analyze_logicals", "analyze_error_patterns",
    "get_license_info", "generate_reproducibility_package", "import_syndrome",
    "estimate_threshold", "finite_size_scaling", "generate_parity_check",
    "build_code_from_matrix",
):
    print(f"  {needed}: {'present' if needed in tools else 'MISSING'}")
