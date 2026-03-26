#!/usr/bin/env python3
"""
Obsidian MCP Server v2 — Modular architecture with vault cache.

Entry point for the MCP server. Initializes the vault cache and registers
all tool modules.
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from src.cache import VaultCache
from src.tools import read, write, edit, links, folders, move, frontmatter, tags, graph

# Load environment variables
load_dotenv()

# Configuration
VAULT_PATH = Path(os.getenv('VAULT_PATH', '')).expanduser()

# Initialize MCP server and vault cache
mcp = FastMCP("obsidian-vault")
cache = VaultCache(VAULT_PATH)

# Register all tool modules
read.register(mcp, cache, VAULT_PATH)
write.register(mcp, cache, VAULT_PATH)
edit.register(mcp, cache, VAULT_PATH)
links.register(mcp, cache, VAULT_PATH)
folders.register(mcp, cache, VAULT_PATH)
move.register(mcp, cache, VAULT_PATH)
frontmatter.register(mcp, cache, VAULT_PATH)
tags.register(mcp, cache, VAULT_PATH)
graph.register(mcp, cache, VAULT_PATH)

# MCP resource
@mcp.resource("vault://info")
def vault_info() -> str:
    """Basic information about the connected Obsidian vault."""
    return f"Obsidian vault at {VAULT_PATH} with {cache.note_count()} notes"


if __name__ == "__main__":
    mcp.run()
