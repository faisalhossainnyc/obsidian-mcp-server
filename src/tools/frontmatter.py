"""
Frontmatter tools: get_frontmatter, set_frontmatter, delete_frontmatter.

Provides dedicated YAML property operations without full-note rewrites.
"""

from pathlib import Path

import frontmatter as fm
from mcp.server.fastmcp import FastMCP

from src.cache import VaultCache


def register(mcp: FastMCP, cache: VaultCache, vault_path: Path) -> None:
    """Register frontmatter tools on the MCP server."""

    @mcp.tool()
    def get_frontmatter(name: str, key: str = "") -> str:
        """Get frontmatter properties from a note.

        Args:
            name: The note name (without .md)
            key: Optional specific key to retrieve. If empty, returns all properties.

        Returns:
            The requested property value(s) or an error message
        """
        note_path = cache.find_note(name)
        if not note_path:
            return f"Note '{name}' not found in vault"

        try:
            with open(note_path, 'r', encoding='utf-8') as f:
                post = fm.load(f)
        except Exception as e:
            return f"Error reading note: {e}"

        if not post.metadata:
            return f"Note '{name}' has no frontmatter"

        if key:
            if key in post.metadata:
                value = post.metadata[key]
                return f"**{name}** → `{key}`: {value}"
            else:
                available = ", ".join(post.metadata.keys())
                return f"Key '{key}' not found in '{name}'. Available keys: {available}"

        # Return all properties
        lines = [f"**Frontmatter for '{name}':**"]
        for k, v in post.metadata.items():
            lines.append(f"- {k}: {v}")
        return "\n".join(lines)

    @mcp.tool()
    def set_frontmatter(name: str, key: str, value: str) -> str:
        """Set a frontmatter property on a note. Creates frontmatter if none exists.

        IMPORTANT: Before calling this tool, you MUST:
        1. Show the user which property will be set and to what value
        2. Ask for explicit confirmation
        3. Only call this tool after the user confirms

        Args:
            name: The note name (without .md)
            key: The frontmatter key to set (e.g., "tags", "status", "module")
            value: The value to set. For lists, use comma-separated format
                   (e.g., "aws, networking, vpc") which will be stored as a YAML list.

        Returns:
            Confirmation message or error
        """
        note_path = cache.find_note(name)
        if not note_path:
            return f"Note '{name}' not found in vault"

        try:
            with open(note_path, 'r', encoding='utf-8') as f:
                post = fm.load(f)
        except Exception as e:
            return f"Error reading note: {e}"

        # Auto-detect list values (comma-separated)
        parsed_value: object
        if ',' in value:
            parsed_value = [v.strip() for v in value.split(',')]
        else:
            # Try numeric conversion
            try:
                parsed_value = int(value)
            except ValueError:
                try:
                    parsed_value = float(value)
                except ValueError:
                    # Boolean detection
                    if value.lower() in ('true', 'yes'):
                        parsed_value = True
                    elif value.lower() in ('false', 'no'):
                        parsed_value = False
                    else:
                        parsed_value = value

        old_value = post.metadata.get(key, "<not set>")
        post.metadata[key] = parsed_value

        try:
            with open(note_path, 'w', encoding='utf-8') as f:
                f.write(fm.dumps(post))
            return (
                f"Successfully set `{key}` on '{name}':\n"
                f"  Old: {old_value}\n"
                f"  New: {parsed_value}"
            )
        except Exception as e:
            return f"Error writing note: {e}"

    @mcp.tool()
    def delete_frontmatter(name: str, key: str) -> str:
        """Remove a frontmatter property from a note.

        IMPORTANT: Before calling this tool, you MUST:
        1. Show the user which property will be removed
        2. Ask for explicit confirmation
        3. Only call this tool after the user confirms

        Args:
            name: The note name (without .md)
            key: The frontmatter key to remove

        Returns:
            Confirmation message or error
        """
        note_path = cache.find_note(name)
        if not note_path:
            return f"Note '{name}' not found in vault"

        try:
            with open(note_path, 'r', encoding='utf-8') as f:
                post = fm.load(f)
        except Exception as e:
            return f"Error reading note: {e}"

        if not post.metadata or key not in post.metadata:
            return f"Key '{key}' not found in frontmatter of '{name}'"

        old_value = post.metadata.pop(key)

        try:
            with open(note_path, 'w', encoding='utf-8') as f:
                f.write(fm.dumps(post))
            return f"Successfully removed `{key}` (was: {old_value}) from '{name}'"
        except Exception as e:
            return f"Error writing note: {e}"
