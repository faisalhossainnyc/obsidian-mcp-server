"""
Tag tools: list_tags, search_by_tag.

Supports both frontmatter `tags:` arrays and inline `#hashtag` formats.
"""

import re
from collections import Counter
from pathlib import Path

import frontmatter as fm
from mcp.server.fastmcp import FastMCP

from src.cache import VaultCache


def _extract_inline_tags(content: str) -> list[str]:
    """Extract #hashtag style tags from content, excluding headings."""
    # Match #word but not ## headings or #123 (pure numbers)
    # Also exclude tags inside code blocks
    tags = re.findall(r'(?<!\w)#([a-zA-Z][a-zA-Z0-9_/-]*)', content)
    return tags


def _get_all_tags(cache: VaultCache) -> Counter:
    """Scan all notes and count every tag (frontmatter + inline)."""
    tag_counts: Counter = Counter()

    for note_path in cache.get_all_notes():
        try:
            with open(note_path, 'r', encoding='utf-8') as f:
                post = fm.load(f)

            # Frontmatter tags
            if post.metadata:
                fm_tags = post.metadata.get('tags', [])
                if isinstance(fm_tags, list):
                    for tag in fm_tags:
                        tag_counts[str(tag).lower()] += 1
                elif isinstance(fm_tags, str):
                    tag_counts[fm_tags.lower()] += 1

            # Inline tags
            for tag in _extract_inline_tags(post.content):
                tag_counts[tag.lower()] += 1

        except Exception:
            continue

    return tag_counts


def register(mcp: FastMCP, cache: VaultCache, vault_path: Path) -> None:
    """Register tag tools on the MCP server."""

    @mcp.tool()
    def list_tags(limit: int = 50) -> str:
        """List all tags across the vault with occurrence counts.

        Scans both frontmatter `tags:` fields and inline `#hashtag` usage.

        Args:
            limit: Maximum number of tags to return (default 50, sorted by count)

        Returns:
            Tags sorted by frequency with occurrence counts
        """
        tag_counts = _get_all_tags(cache)

        if not tag_counts:
            return "No tags found in the vault"

        # Sort by count descending, then alphabetically
        sorted_tags = sorted(tag_counts.items(), key=lambda x: (-x[1], x[0]))[:limit]

        result = f"**Tags in vault** ({len(tag_counts)} unique, showing top {len(sorted_tags)}):\n"
        for tag, count in sorted_tags:
            result += f"- #{tag} ({count})\n"

        return result.rstrip()

    @mcp.tool()
    def search_by_tag(tag: str) -> str:
        """Find all notes that contain a specific tag.

        Searches both frontmatter `tags:` arrays and inline `#hashtag` usage.

        Args:
            tag: The tag to search for (with or without #)

        Returns:
            List of notes containing the tag
        """
        # Normalize: strip leading # if present
        tag_clean = tag.lstrip('#').lower()
        matches = []

        for note_path in cache.get_all_notes():
            try:
                with open(note_path, 'r', encoding='utf-8') as f:
                    post = fm.load(f)

                found = False

                # Check frontmatter tags
                if post.metadata:
                    fm_tags = post.metadata.get('tags', [])
                    if isinstance(fm_tags, list):
                        if any(str(t).lower() == tag_clean for t in fm_tags):
                            found = True
                    elif isinstance(fm_tags, str) and fm_tags.lower() == tag_clean:
                        found = True

                # Check inline tags
                if not found:
                    inline_tags = [t.lower() for t in _extract_inline_tags(post.content)]
                    if tag_clean in inline_tags:
                        found = True

                if found:
                    rel_path = note_path.relative_to(vault_path)
                    matches.append(f"- {note_path.stem} ({rel_path})")

            except Exception:
                continue

        if not matches:
            return f"No notes found with tag '#{tag_clean}'"

        return (
            f"**Notes tagged #{tag_clean}** ({len(matches)}):\n"
            + "\n".join(matches)
        )
