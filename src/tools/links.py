"""
Link tools: get_note_links, validate_wikilinks.
"""

from pathlib import Path

from mcp.server.fastmcp import FastMCP

from src.cache import VaultCache
from src.utils import read_note, extract_wikilinks


def register(mcp: FastMCP, cache: VaultCache, vault_path: Path) -> None:
    """Register link-related tools on the MCP server."""

    @mcp.tool()
    def get_note_links(name: str) -> str:
        """Get all WikiLinks from a specific note.

        Args:
            name: The name of the note to analyze

        Returns:
            List of WikiLinks found in the note
        """
        note_path = cache.find_note(name)
        if not note_path:
            return f"Note '{name}' not found in vault"

        data = read_note(note_path, vault_path)
        if 'error' in data:
            return f"Error reading note: {data['error']}"

        links = extract_wikilinks(data['content'])
        if not links:
            return f"No WikiLinks found in '{name}'"

        return (
            f"WikiLinks in '{name}':\n"
            + "\n".join(f"- [[{link}]]" for link in sorted(links))
        )

    @mcp.tool()
    def validate_wikilinks(name: str) -> str:
        """Check if all WikiLinks in a note point to existing notes.

        Args:
            name: The name of the note to validate

        Returns:
            Validation report showing valid and broken links
        """
        note_path = cache.find_note(name)
        if not note_path:
            return f"Note '{name}' not found in vault"

        data = read_note(note_path, vault_path)
        if 'error' in data:
            return f"Error reading note: {data['error']}"

        links = extract_wikilinks(data['content'])
        if not links:
            return f"No WikiLinks to validate in '{name}'"

        # O(1) lookup per link using cache instead of scanning all notes
        all_names = cache.get_all_note_names()

        valid = []
        broken = []
        for link in links:
            if link.lower() in all_names:
                valid.append(link)
            else:
                broken.append(link)

        result = f"WikiLink validation for '{name}':\n\n"
        result += f"**Valid links ({len(valid)}):**\n"
        result += "\n".join(f"- [[{link}]]" for link in sorted(valid)) or "None"
        result += f"\n\n**Broken links ({len(broken)}):**\n"
        result += "\n".join(f"- [[{link}]]" for link in sorted(broken)) or "None"

        return result
