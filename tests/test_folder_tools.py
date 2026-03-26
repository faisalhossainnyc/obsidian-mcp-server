"""Tests for folder tools: find_folder, create_folder."""


class TestFindFolder:
    def test_finds_existing_folder(self, tools):
        result = tools["find_folder"](query="Projects")
        assert "Projects" in result

    def test_case_insensitive(self, tools):
        result = tools["find_folder"](query="projects")
        assert "Projects" in result

    def test_no_match(self, tools):
        result = tools["find_folder"](query="xyzzy_nonexistent")
        assert "No folders found" in result

    def test_ignores_hidden_folders(self, tools):
        result = tools["find_folder"](query="obsidian")
        assert "No folders found" in result


class TestCreateFolder:
    def test_creates_folder(self, tools, vault_path):
        result = tools["create_folder"](path="Archive")
        assert "Successfully created" in result
        assert (vault_path / "Archive").is_dir()

    def test_creates_nested_folders(self, tools, vault_path):
        result = tools["create_folder"](path="Archive/2024/Q1")
        assert "Successfully created" in result
        assert (vault_path / "Archive" / "2024" / "Q1").is_dir()

    def test_existing_folder(self, tools):
        result = tools["create_folder"](path="Projects")
        assert "already exists" in result

    def test_empty_path(self, tools):
        result = tools["create_folder"](path="")
        assert "Error" in result

    def test_rejects_path_traversal(self, tools):
        result = tools["create_folder"](path="../../../tmp/evil")
        assert "Error" in result
