"""
Shared utilities for the Obsidian MCP server.
"""

import re
from pathlib import Path

import frontmatter


def read_note(note_path: Path, vault_path: Path) -> dict:
    """Read note content and metadata via python-frontmatter."""
    try:
        with open(note_path, 'r', encoding='utf-8') as f:
            post = frontmatter.load(f)
            return {
                'name': note_path.stem,
                'path': str(note_path.relative_to(vault_path)),
                'metadata': dict(post.metadata) if post.metadata else {},
                'content': post.content,
            }
    except Exception as e:
        return {'error': str(e), 'path': str(note_path)}


def read_note_raw_lines(note_path: Path) -> list[str]:
    """Read a note and return its raw lines (preserving newlines)."""
    with open(note_path, 'r', encoding='utf-8') as f:
        return f.readlines()


def write_note_lines(note_path: Path, lines: list[str]) -> None:
    """Write lines back to a note file."""
    with open(note_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)


def extract_wikilinks(content: str) -> list[str]:
    """Extract unique [[WikiLinks]] from content, handling aliases."""
    pattern = r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]'
    return list(set(re.findall(pattern, content)))


def safe_resolve(path_str: str, vault_path: Path) -> Path:
    """Resolve a user-supplied path safely within the vault.

    Raises ValueError if the resolved path escapes the vault root.
    """
    # Reject obvious traversal attempts
    if '..' in path_str:
        raise ValueError(f"Path cannot contain '..': {path_str}")

    # Resolve and verify containment
    resolved = (vault_path / path_str).resolve()
    vault_resolved = vault_path.resolve()

    if not str(resolved).startswith(str(vault_resolved)):
        raise ValueError(f"Path escapes vault root: {path_str}")

    return resolved


def prepare_lines(content: str) -> list[str]:
    """Ensure content ends with newline and split into lines."""
    if not content.endswith('\n'):
        content += '\n'
    return content.splitlines(keepends=True)
