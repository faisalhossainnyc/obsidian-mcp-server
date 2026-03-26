"""Tests for line-editing tools: read_lines, insert, replace, delete, bulk_edit."""

import json


class TestReadNoteLines:
    def test_shows_line_numbers(self, tools):
        result = tools["read_note_lines"](name="Alpha", start_line=1, end_line=None)
        assert "1 |" in result  # First line has line number

    def test_range_selection(self, tools):
        result = tools["read_note_lines"](name="Alpha", start_line=2, end_line=4)
        assert "lines 2-4" in result

    def test_missing_note(self, tools):
        result = tools["read_note_lines"](name="NoSuchNote", start_line=1, end_line=None)
        assert "not found" in result


class TestInsertLines:
    def test_inserts_after_line(self, tools, vault_path):
        result = tools["insert_lines"](name="Gamma", after_line=1, content="Inserted line")
        assert "Successfully inserted" in result
        lines = (vault_path / "Gamma.md").read_text().splitlines()
        assert lines[1] == "Inserted line"

    def test_inserts_at_beginning(self, tools, vault_path):
        result = tools["insert_lines"](name="Gamma", after_line=0, content="First line")
        assert "Successfully inserted" in result
        lines = (vault_path / "Gamma.md").read_text().splitlines()
        assert lines[0] == "First line"

    def test_out_of_range(self, tools):
        result = tools["insert_lines"](name="Gamma", after_line=999, content="x")
        assert "out of range" in result

    def test_missing_note(self, tools):
        result = tools["insert_lines"](name="NoSuchNote", after_line=1, content="x")
        assert "not found" in result


class TestReplaceLines:
    def test_replaces_single_line(self, tools, vault_path):
        result = tools["replace_lines"](name="Gamma", start_line=1, end_line=1, content="Replaced")
        assert "Successfully replaced" in result
        lines = (vault_path / "Gamma.md").read_text().splitlines()
        assert lines[0] == "Replaced"

    def test_replaces_range(self, tools, vault_path):
        result = tools["replace_lines"](name="Gamma", start_line=1, end_line=2, content="Single line")
        assert "Successfully replaced" in result
        lines = (vault_path / "Gamma.md").read_text().splitlines()
        assert lines[0] == "Single line"
        assert len(lines) == 1

    def test_invalid_range(self, tools):
        result = tools["replace_lines"](name="Gamma", start_line=5, end_line=3, content="x")
        assert "Error" in result

    def test_missing_note(self, tools):
        result = tools["replace_lines"](name="NoSuchNote", start_line=1, end_line=1, content="x")
        assert "not found" in result


class TestDeleteLines:
    def test_deletes_single_line(self, tools, vault_path):
        original = (vault_path / "Gamma.md").read_text().splitlines()
        result = tools["delete_lines"](name="Gamma", start_line=1, end_line=1)
        assert "Successfully deleted" in result
        remaining = (vault_path / "Gamma.md").read_text().splitlines()
        assert len(remaining) == len(original) - 1

    def test_invalid_range(self, tools):
        result = tools["delete_lines"](name="Gamma", start_line=0, end_line=1)
        assert "Error" in result

    def test_missing_note(self, tools):
        result = tools["delete_lines"](name="NoSuchNote", start_line=1, end_line=1)
        assert "not found" in result


class TestBulkEdit:
    def test_single_insert(self, tools):
        edits = json.dumps([
            {"name": "Gamma", "op": "insert", "after_line": 0, "content": "# Header"}
        ])
        result = tools["bulk_edit"](edits=edits)
        assert "Successfully applied 1 edit" in result

    def test_multiple_edits_same_note(self, tools, vault_path):
        """Edits applied bottom-to-top should preserve line numbers."""
        edits = json.dumps([
            {"name": "Alpha", "op": "insert", "after_line": 1, "content": "After line 1"},
            {"name": "Alpha", "op": "delete", "start_line": 8, "end_line": 8},
        ])
        result = tools["bulk_edit"](edits=edits)
        assert "Successfully applied 2 edit" in result

    def test_multiple_notes(self, tools):
        edits = json.dumps([
            {"name": "Alpha", "op": "insert", "after_line": 0, "content": "A header"},
            {"name": "Beta", "op": "insert", "after_line": 0, "content": "B header"},
        ])
        result = tools["bulk_edit"](edits=edits)
        assert "2 note(s)" in result

    def test_invalid_json(self, tools):
        result = tools["bulk_edit"](edits="not json")
        assert "Error parsing" in result

    def test_missing_note_in_batch(self, tools):
        edits = json.dumps([
            {"name": "NoSuchNote", "op": "insert", "after_line": 0, "content": "x"}
        ])
        result = tools["bulk_edit"](edits=edits)
        assert "not found" in result

    def test_invalid_operation(self, tools):
        edits = json.dumps([
            {"name": "Alpha", "op": "explode", "start_line": 1, "end_line": 1}
        ])
        result = tools["bulk_edit"](edits=edits)
        assert "invalid 'op'" in result
