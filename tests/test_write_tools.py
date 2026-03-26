"""Tests for write tools: create, update, append, delete."""


class TestCreateNote:
    def test_creates_new_note(self, tools, vault_path):
        result = tools["create_note"](name="NewNote", content="Hello world", folder="")
        assert "Successfully created" in result
        assert (vault_path / "NewNote.md").exists()
        assert (vault_path / "NewNote.md").read_text() == "Hello world"

    def test_creates_in_subfolder(self, tools, vault_path):
        result = tools["create_note"](name="Sub", content="In folder", folder="TestFolder")
        assert "Successfully created" in result
        assert (vault_path / "TestFolder" / "Sub.md").exists()

    def test_rejects_duplicate(self, tools):
        result = tools["create_note"](name="Alpha", content="dup", folder="")
        assert "already exists" in result

    def test_rejects_path_traversal(self, tools):
        result = tools["create_note"](name="evil", content="bad", folder="../../etc")
        assert "Error" in result


class TestUpdateNote:
    def test_replaces_content(self, tools, vault_path):
        result = tools["update_note"](name="Gamma", content="Completely new content")
        assert "Successfully updated" in result
        assert (vault_path / "Gamma.md").read_text() == "Completely new content"

    def test_missing_note(self, tools):
        result = tools["update_note"](name="NoSuchNote", content="x")
        assert "not found" in result


class TestAppendToNote:
    def test_appends_content(self, tools, vault_path):
        result = tools["append_to_note"](name="Gamma", content="Appended text")
        assert "Successfully appended" in result
        content = (vault_path / "Gamma.md").read_text()
        assert content.endswith("Appended text")

    def test_missing_note(self, tools):
        result = tools["append_to_note"](name="NoSuchNote", content="x")
        assert "not found" in result


class TestDeleteNote:
    def test_safety_check_without_confirm(self, tools):
        result = tools["delete_note"](name="Gamma", confirm=False)
        assert "Safety check" in result

    def test_deletes_with_confirm(self, tools, vault_path):
        assert (vault_path / "Gamma.md").exists()
        result = tools["delete_note"](name="Gamma", confirm=True)
        assert "Successfully deleted" in result
        assert not (vault_path / "Gamma.md").exists()

    def test_missing_note(self, tools):
        result = tools["delete_note"](name="NoSuchNote", confirm=True)
        assert "not found" in result
