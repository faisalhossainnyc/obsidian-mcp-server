"""
Write tools: create_note, update_note, append_to_note, delete_note.
"""

from pathlib import Path

from mcp.server.fastmcp import FastMCP

from src.cache import VaultCache
from src.utils import safe_resolve


def register(mcp: FastMCP, cache: VaultCache, vault_path: Path) -> None:
    """Register all write tools on the MCP server."""

    @mcp.tool()
    def create_note(name: str, content: str, folder: str = "") -> str:
        """Create a new note in the Obsidian vault.

        IMPORTANT: Before calling this tool, you MUST:
        1. Show the user the complete note content you plan to write
        2. Ask for explicit confirmation (e.g., "Should I create this note?")
        3. Only call this tool after the user confirms

        Args:
            name: The name for the new note (without .md extension)
            content: The full markdown content for the note
            folder: Optional subfolder path (e.g., "AWS" or "Projects/2024")

        Returns:
            Confirmation message or error
        """
        try:
            if folder:
                note_dir = safe_resolve(folder, vault_path)
            else:
                note_dir = vault_path

            note_path = note_dir / f"{name}.md"

            # Verify the final path is within the vault
            safe_resolve(str(note_path.relative_to(vault_path)), vault_path)
        except ValueError as e:
            return f"Error: {e}"

        if note_path.exists():
            return (
                f"Error: Note '{name}' already exists at "
                f"{note_path.relative_to(vault_path)}. Use update_note to modify it."
            )

        try:
            note_dir.mkdir(parents=True, exist_ok=True)
            with open(note_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return f"Successfully created note: {note_path.relative_to(vault_path)}"
        except Exception as e:
            return f"Error creating note: {e}"

    @mcp.tool()
    def update_note(name: str, content: str) -> str:
        """Replace the entire content of an existing note.

        NOTE: For partial edits, prefer the more efficient line-based tools:
        - insert_lines: Add content at a specific location
        - replace_lines: Change specific lines
        - delete_lines: Remove specific lines
        Only use update_note when restructuring the entire document.

        IMPORTANT: Before calling this tool, you MUST:
        1. First read the current note content using read_note_by_name
        2. Show the user the proposed changes (ideally as a diff or before/after)
        3. Ask for explicit confirmation (e.g., "Should I update this note?")
        4. Only call this tool after the user confirms

        Args:
            name: The name of the note to update (without .md extension)
            content: The new full markdown content for the note

        Returns:
            Confirmation message or error
        """
        note_path = cache.find_note(name)
        if not note_path:
            return f"Note '{name}' not found in vault. Use create_note to create a new note."

        try:
            with open(note_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return f"Successfully updated note: {note_path.relative_to(vault_path)}"
        except Exception as e:
            return f"Error updating note: {e}"

    @mcp.tool()
    def append_to_note(name: str, content: str) -> str:
        """Append content to the end of an existing note.

        IMPORTANT: Before calling this tool, you MUST:
        1. Show the user the exact content you plan to append
        2. Ask for explicit confirmation (e.g., "Should I append this to the note?")
        3. Only call this tool after the user confirms

        Args:
            name: The name of the note to append to (without .md extension)
            content: The content to append (will be added after two newlines)

        Returns:
            Confirmation message or error
        """
        note_path = cache.find_note(name)
        if not note_path:
            return f"Note '{name}' not found in vault."

        try:
            with open(note_path, 'a', encoding='utf-8') as f:
                f.write(f"\n\n{content}")
            return f"Successfully appended to note: {note_path.relative_to(vault_path)}"
        except Exception as e:
            return f"Error appending to note: {e}"

    @mcp.tool()
    def delete_note(name: str, confirm: bool = False) -> str:
        """Delete a note from the Obsidian vault.

        IMPORTANT: Before calling this tool, you MUST:
        1. Warn the user that this action is irreversible
        2. Ask for explicit confirmation (e.g., "Are you sure you want to delete this note?")
        3. Only call this tool with confirm=True after the user explicitly confirms

        Args:
            name: The name of the note to delete (without .md extension)
            confirm: Must be set to True to actually delete (safety measure)

        Returns:
            Confirmation message or error
        """
        if not confirm:
            return "Safety check: You must set confirm=True to delete a note. Please confirm with the user first."

        note_path = cache.find_note(name)
        if not note_path:
            return f"Note '{name}' not found in vault."

        try:
            note_path.unlink()
            return f"Successfully deleted note: {name}"
        except Exception as e:
            return f"Error deleting note: {e}"
