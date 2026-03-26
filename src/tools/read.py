"""
Read-only tools: list_notes, read_note_by_name, search_notes,
get_vault_stats, recent_notes.
"""

import re
import time
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from src.cache import VaultCache
from src.utils import read_note, extract_wikilinks


def register(mcp: FastMCP, cache: VaultCache, vault_path: Path) -> None:
    """Register all read-only tools on the MCP server."""

    @mcp.tool()
    def list_notes(limit: int = 50) -> str:
        """List all notes in the Obsidian vault.

        Args:
            limit: Maximum number of notes to return (default 50)

        Returns:
            List of note names in the vault
        """
        notes = cache.get_all_notes(limit=limit)
        total = cache.note_count()
        note_names = [n.stem for n in notes]
        return (
            f"Found {total} notes. Showing first {len(note_names)}:\n"
            + "\n".join(f"- {name}" for name in note_names)
        )

    @mcp.tool()
    def read_note_by_name(name: str) -> str:
        """Read a specific note by its name (without .md extension).

        Args:
            name: The name of the note to read

        Returns:
            The full content of the note including frontmatter
        """
        note_path = cache.find_note(name)
        if not note_path:
            return f"Note '{name}' not found in vault"

        data = read_note(note_path, vault_path)
        if 'error' in data:
            return f"Error reading note: {data['error']}"

        result = f"# {data['name']}\n\n"
        if data['metadata']:
            result += "**Frontmatter:**\n"
            for key, value in data['metadata'].items():
                result += f"- {key}: {value}\n"
            result += "\n"
        result += data['content']
        return result

    @mcp.tool()
    def search_notes(
        query: str,
        limit: int = 10,
        offset: int = 0,
        path_filter: str = "",
        use_regex: bool = False,
    ) -> str:
        """Search for notes containing a specific term in their content.

        Args:
            query: The search term or regex pattern to look for
            limit: Maximum number of results to return (default 10)
            offset: Number of results to skip for pagination (default 0)
            path_filter: Only search in notes whose path starts with this
                         folder (e.g., "Projects" or "AWS/Module 1")
            use_regex: If True, treat query as a regular expression

        Returns:
            List of matching notes with preview snippets
        """
        all_matches = []

        # Compile regex if requested
        pattern = None
        if use_regex:
            try:
                pattern = re.compile(query, re.IGNORECASE)
            except re.error as e:
                return f"Invalid regex pattern: {e}"

        search_term = query.lower()

        for note_path in cache.get_all_notes():
            # Apply path filter
            if path_filter:
                try:
                    rel = str(note_path.relative_to(vault_path))
                    if not rel.startswith(path_filter):
                        continue
                except ValueError:
                    continue

            # Read raw content
            try:
                with open(note_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except Exception:
                continue

            # Match
            match_pos = -1
            if pattern:
                m = pattern.search(content)
                if m:
                    match_pos = m.start()
            else:
                content_lower = content.lower()
                if search_term in content_lower:
                    match_pos = content_lower.find(search_term)

            if match_pos >= 0:
                # Build snippet around the match
                start = max(0, match_pos - 50)
                end = min(len(content), match_pos + len(query) + 50)
                snippet = content[start:end].replace('\n', ' ')
                if start > 0:
                    snippet = "..." + snippet
                if end < len(content):
                    snippet = snippet + "..."

                all_matches.append(f"**{note_path.stem}**: {snippet}")

        total = len(all_matches)
        page = all_matches[offset:offset + limit]

        if not page:
            if offset > 0:
                return f"No more results (total: {total}, offset: {offset})"
            return f"No notes found matching '{query}'"

        header = f"Found {total} notes matching '{query}'"
        if offset > 0 or total > len(page):
            header += f" (showing {offset + 1}-{offset + len(page)} of {total})"
        header += ":\n\n"

        return header + "\n\n".join(page)

    @mcp.tool()
    def get_vault_stats() -> str:
        """Get statistics about the Obsidian vault.

        Returns:
            Vault statistics including note count, link count, etc.
        """
        notes = cache.get_all_notes()
        total_links = 0
        total_words = 0
        notes_with_frontmatter = 0

        for note_path in notes:
            data = read_note(note_path, vault_path)
            if 'content' in data:
                total_links += len(extract_wikilinks(data['content']))
                total_words += len(data['content'].split())
            if data.get('metadata'):
                notes_with_frontmatter += 1

        count = len(notes)
        avg = total_words // count if count else 0

        return f"""Obsidian Vault Statistics:
- Vault path: {vault_path}
- Total notes: {count}
- Notes with frontmatter: {notes_with_frontmatter}
- Total WikiLinks: {total_links}
- Total words: {total_words:,}
- Average words per note: {avg:,}"""

    @mcp.tool()
    def recent_notes(days: int = 7, limit: int = 20) -> str:
        """List notes modified within the last N days.

        Args:
            days: Number of days to look back (default 7)
            limit: Maximum number of notes to return (default 20)

        Returns:
            Recently modified notes sorted by modification time
        """
        cutoff = time.time() - (days * 86400)
        recent = []

        for note_path in cache.get_all_notes():
            try:
                mtime = note_path.stat().st_mtime
                if mtime >= cutoff:
                    from datetime import datetime
                    dt = datetime.fromtimestamp(mtime)
                    recent.append((note_path, dt))
            except Exception:
                continue

        if not recent:
            return f"No notes modified in the last {days} day(s)"

        recent.sort(key=lambda x: x[1], reverse=True)
        shown = recent[:limit]

        result = f"**Notes modified in last {days} day(s)** ({len(recent)} total, showing {len(shown)}):\n"
        for note_path, dt in shown:
            rel = note_path.relative_to(vault_path)
            result += f"- {note_path.stem} ({rel}) — {dt.strftime('%Y-%m-%d %H:%M')}\n"

        return result.rstrip()
