"""Security tests: path traversal, input validation, edge cases."""

import json
from src.utils import safe_resolve
from pathlib import Path
import pytest


class TestSafeResolve:
    def test_rejects_dotdot(self):
        vault = Path("/tmp/vault")
        with pytest.raises(ValueError, match="cannot contain"):
            safe_resolve("../etc/passwd", vault)

    def test_rejects_nested_dotdot(self):
        vault = Path("/tmp/vault")
        with pytest.raises(ValueError, match="cannot contain"):
            safe_resolve("notes/../../etc/passwd", vault)

    def test_accepts_valid_path(self):
        vault = Path("/tmp/vault")
        vault.mkdir(exist_ok=True)
        result = safe_resolve("notes/hello.md", vault)
        assert str(result).startswith(str(vault.resolve()))

    def test_accepts_simple_name(self):
        vault = Path("/tmp/vault")
        vault.mkdir(exist_ok=True)
        result = safe_resolve("test", vault)
        assert str(result).startswith(str(vault.resolve()))


class TestPathTraversalOnTools:
    """Ensure every tool that accepts paths rejects traversal."""

    def test_create_note_traversal(self, tools):
        result = tools["create_note"](name="x", content="x", folder="../../etc")
        assert "Error" in result

    def test_create_folder_traversal(self, tools):
        result = tools["create_folder"](path="../../../tmp/evil")
        assert "Error" in result

    def test_move_note_traversal(self, tools):
        result = tools["move_note"](name="Alpha", destination_folder="../../tmp")
        assert "Error" in result


class TestEdgeCases:
    def test_empty_vault(self, tools, vault_path, cache):
        """Tools should handle an empty vault gracefully."""
        import shutil
        # Remove all notes
        for f in vault_path.glob("*.md"):
            f.unlink()
        shutil.rmtree(vault_path / "Projects")
        cache.refresh()

        result = tools["list_notes"](limit=50)
        assert "Found 0 notes" in result

        result = tools["search_notes"](query="anything", limit=10)
        assert "No notes found" in result

    def test_unicode_note_name(self, tools, vault_path, cache):
        result = tools["create_note"](name="日本語ノート", content="Unicode content", folder="")
        assert "Successfully created" in result
        cache.refresh()
        result = tools["read_note_by_name"](name="日本語ノート")
        assert "Unicode content" in result

    def test_bulk_edit_empty_array(self, tools):
        result = tools["bulk_edit"](edits="[]")
        assert "No edits provided" in result

    def test_bulk_edit_not_array(self, tools):
        result = tools["bulk_edit"](edits='{"op": "insert"}')
        assert "must be a JSON array" in result

    def test_delete_without_confirm(self, tools, vault_path):
        """Ensure delete safety check prevents accidental deletion."""
        result = tools["delete_note"](name="Alpha", confirm=False)
        assert "Safety check" in result
        assert (vault_path / "Alpha.md").exists()  # Still there
