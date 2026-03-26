"""Tests for move_note tool."""


class TestMoveNote:
    def test_moves_to_new_folder(self, tools, vault_path, cache):
        result = tools["move_note"](name="Gamma", destination_folder="Archive")
        assert "Successfully moved" in result
        assert (vault_path / "Archive" / "Gamma.md").exists()
        assert not (vault_path / "Gamma.md").exists()

    def test_moves_to_vault_root(self, tools, vault_path, cache):
        result = tools["move_note"](name="Delta", destination_folder="")
        assert "Successfully moved" in result
        assert (vault_path / "Delta.md").exists()

    def test_already_in_destination(self, tools):
        result = tools["move_note"](name="Delta", destination_folder="Projects")
        assert "already in" in result

    def test_name_conflict(self, tools, vault_path):
        # Create a note with the same name in the destination
        (vault_path / "Projects" / "Alpha.md").write_text("conflict")
        result = tools["move_note"](name="Alpha", destination_folder="Projects")
        assert "already exists" in result

    def test_missing_note(self, tools):
        result = tools["move_note"](name="NoSuchNote", destination_folder="Archive")
        assert "not found" in result

    def test_rejects_path_traversal(self, tools):
        result = tools["move_note"](name="Gamma", destination_folder="../../tmp")
        assert "Error" in result

    def test_updates_fullpath_backlinks(self, tools, vault_path, cache):
        """When a note uses a full-path WikiLink, moving should simplify it."""
        # Create a note with a full-path link to Delta
        (vault_path / "Linker.md").write_text("See [[Projects/Delta]] for details.\n")
        cache.refresh()

        result = tools["move_note"](name="Delta", destination_folder="Archive")
        assert "Successfully moved" in result

        # The full-path link should have been simplified
        linker_content = (vault_path / "Linker.md").read_text()
        assert "[[Delta]]" in linker_content
        assert "[[Projects/Delta]]" not in linker_content
