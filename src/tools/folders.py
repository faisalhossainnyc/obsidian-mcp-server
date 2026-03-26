"""
Folder management tools: find_folder, create_folder.
"""

from pathlib import Path

from mcp.server.fastmcp import FastMCP

from src.cache import VaultCache
from src.utils import safe_resolve


def register(mcp: FastMCP, cache: VaultCache, vault_path: Path) -> None:
    """Register folder management tools on the MCP server."""

    @mcp.tool()
    def find_folder(query: str) -> str:
        """Search for folders in the vault by name or partial match.

        Args:
            query: The folder name or partial name to search for (case-insensitive)

        Returns:
            List of matching folder paths with note counts, or message if none found
        """
        if not vault_path.exists():
            return "Vault path does not exist"

        matches = []
        query_lower = query.lower()

        for item in vault_path.rglob("*"):
            if item.is_dir() and not any(part.startswith('.') for part in item.relative_to(vault_path).parts):
                if query_lower in item.name.lower():
                    rel_path = item.relative_to(vault_path)
                    note_count = len([f for f in item.glob("*.md") if f.is_file()])
                    matches.append((str(rel_path), note_count))

        if not matches:
            return f"No folders found matching '{query}'"

        matches.sort()

        result = f"Found {len(matches)} folder(s) matching '{query}':\n"
        for path, count in matches:
            result += f"- {path} ({count} notes)\n"

        return result.rstrip()

    @mcp.tool()
    def create_folder(path: str) -> str:
        """Create a new folder in the vault.

        This will create all parent folders automatically if they don't exist.
        For example, creating "Projects/2024/AWS" will create Projects, then 2024, then AWS.

        Args:
            path: The folder path to create, relative to vault root
                  (e.g., "Archive" or "Projects/2024/AWS")

        Returns:
            Confirmation message or error
        """
        if not path or path.strip() == "":
            return "Error: Folder path cannot be empty"

        try:
            folder_path = safe_resolve(path, vault_path)
        except ValueError as e:
            return f"Error: {e}"

        if folder_path.exists():
            if folder_path.is_dir():
                return f"Folder '{path}' already exists"
            else:
                return f"Error: '{path}' exists but is not a folder"

        try:
            folder_path.mkdir(parents=True, exist_ok=True)

            created_parts = []
            check_path = folder_path
            while check_path != vault_path:
                if check_path.exists():
                    created_parts.insert(0, check_path.relative_to(vault_path))
                check_path = check_path.parent

            if len(created_parts) > 1:
                return f"Successfully created folder hierarchy: {' → '.join(str(p) for p in created_parts)}"
            else:
                return f"Successfully created folder: {path}"

        except Exception as e:
            return f"Error creating folder: {e}"
