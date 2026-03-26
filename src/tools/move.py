"""
Move tool: move_note with automatic backlink updates.
"""

import re
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from src.cache import VaultCache
from src.utils import safe_resolve


def register(mcp: FastMCP, cache: VaultCache, vault_path: Path) -> None:
    """Register the move_note tool on the MCP server."""

    @mcp.tool()
    def move_note(name: str, destination_folder: str) -> str:
        """Move a note to a different folder within the vault.

        This tool will:
        - Move the note to the specified folder
        - Create the destination folder if it doesn't exist
        - Update WikiLinks in other notes that reference this note

        IMPORTANT: Before calling this tool, you MUST:
        1. Tell the user which note will be moved and where
        2. Ask for explicit confirmation
        3. Only call this tool after the user confirms

        Args:
            name: The name of the note to move (without .md extension)
            destination_folder: The folder path to move to (e.g., "Archive" or "Projects/2024").
                               Use "" (empty string) to move to vault root.

        Returns:
            Confirmation message with details of the move and any updated WikiLinks
        """
        note_path = cache.find_note(name)
        if not note_path:
            return f"Note '{name}' not found in vault"

        old_relative_path = note_path.relative_to(vault_path)

        # Validate and resolve destination
        try:
            if destination_folder:
                dest_dir = safe_resolve(destination_folder, vault_path)
            else:
                dest_dir = vault_path
        except ValueError as e:
            return f"Error: {e}"

        new_path = dest_dir / f"{note_path.stem}.md"

        if note_path == new_path:
            return f"Note '{name}' is already in '{destination_folder or 'vault root'}'"

        if new_path.exists():
            return f"Error: A note named '{name}' already exists in '{destination_folder or 'vault root'}'"

        try:
            dest_dir.mkdir(parents=True, exist_ok=True)
            note_path.rename(new_path)

            # Update WikiLinks in other notes
            old_name = note_path.stem
            updated_notes = []

            for other_note in cache.get_all_notes():
                if other_note == new_path:
                    continue

                try:
                    with open(other_note, 'r', encoding='utf-8') as f:
                        content = f.read()

                    # Patterns for full-path links that need updating
                    patterns = [
                        (
                            rf'\[\[{re.escape(str(old_relative_path.with_suffix("")))}\]\]',
                            f'[[{old_name}]]',
                        ),
                        (
                            rf'\[\[{re.escape(str(old_relative_path.with_suffix("")))}\|([^\]]+)\]\]',
                            f'[[{old_name}|\\1]]',
                        ),
                    ]

                    modified = False
                    new_content = content

                    for pattern, replacement in patterns:
                        if re.search(pattern, new_content):
                            new_content = re.sub(pattern, replacement, new_content)
                            modified = True

                    if modified:
                        with open(other_note, 'w', encoding='utf-8') as f:
                            f.write(new_content)
                        updated_notes.append(other_note.stem)

                except Exception:
                    continue

            result = (
                f"Successfully moved '{name}' from '{old_relative_path.parent}' "
                f"to '{destination_folder or 'vault root'}'"
            )

            if updated_notes:
                result += f"\n\nUpdated WikiLinks in {len(updated_notes)} note(s):"
                for note_name in updated_notes[:10]:
                    result += f"\n  - {note_name}"
                if len(updated_notes) > 10:
                    result += f"\n  ... and {len(updated_notes) - 10} more"

            return result

        except Exception as e:
            return f"Error moving note: {e}"
