"""
Shared pytest fixtures for the Obsidian MCP test suite.

Creates an isolated test vault with known content so tests are
repeatable and never touch the real vault.
"""

import os
import shutil
from pathlib import Path

import pytest

TEST_VAULT = Path("/tmp/obsidian_test_vault")


@pytest.fixture(autouse=True, scope="session")
def set_env():
    """Set VAULT_PATH before any imports touch it."""
    os.environ["VAULT_PATH"] = str(TEST_VAULT)


@pytest.fixture(scope="session")
def vault_path():
    return TEST_VAULT


@pytest.fixture(autouse=True)
def fresh_vault(vault_path):
    """
    Before EVERY test: rebuild the vault from scratch.
    Guarantees each test starts from an identical known state.
    """
    if vault_path.exists():
        shutil.rmtree(vault_path)
    vault_path.mkdir()

    # --- Seed notes ---
    (vault_path / "Alpha.md").write_text(
        "---\ntags: [aws, networking]\nmodule: 1\n---\n"
        "Alpha note content.\n"
        "Links to [[Beta]] and [[Gamma|see Gamma]].\n"
        "Line 3 of Alpha.\n"
        "Line 4 of Alpha.\n"
        "Line 5 of Alpha.\n"
    )

    (vault_path / "Beta.md").write_text(
        "---\ntags: [security]\n---\n"
        "Beta note content.\n"
        "Links back to [[Alpha]].\n"
    )

    (vault_path / "Gamma.md").write_text(
        "Gamma has no frontmatter.\n"
        "Just plain content here.\n"
    )

    # A note in a subfolder
    sub = vault_path / "Projects"
    sub.mkdir()
    (sub / "Delta.md").write_text(
        "---\nstatus: active\n---\n"
        "Delta lives in Projects.\n"
        "References [[Alpha]] and [[Nonexistent Note]].\n"
    )

    # Hidden folder (should be ignored)
    hidden = vault_path / ".obsidian"
    hidden.mkdir()
    (hidden / "config.md").write_text("This should be invisible.\n")

    yield vault_path


@pytest.fixture()
def cache(vault_path):
    """Provide a fresh VaultCache instance per test."""
    from src.cache import VaultCache

    c = VaultCache(vault_path)
    yield c
    c.shutdown()


@pytest.fixture()
def tools(cache, vault_path):
    """
    Register all tools on a throwaway MCP server and return
    {tool_name: callable} for easy invocation.
    """
    from mcp.server.fastmcp import FastMCP
    from src.tools import read, write, edit, links, folders, move, frontmatter, tags, graph

    mcp = FastMCP("test")
    read.register(mcp, cache, vault_path)
    write.register(mcp, cache, vault_path)
    edit.register(mcp, cache, vault_path)
    links.register(mcp, cache, vault_path)
    folders.register(mcp, cache, vault_path)
    move.register(mcp, cache, vault_path)
    frontmatter.register(mcp, cache, vault_path)
    tags.register(mcp, cache, vault_path)
    graph.register(mcp, cache, vault_path)

    return {name: tool.fn for name, tool in mcp._tool_manager._tools.items()}
