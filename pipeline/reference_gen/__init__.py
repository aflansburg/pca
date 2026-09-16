"""Generators for committed reference files (keyless, run occasionally).

These fetch slow-moving reference data and write it under data/reference/ (tracked in git),
so the normal pipeline reads committed files and needs neither network nor the DuckDB spatial
extension. Refresh a vintage by re-running the matching module.
"""
