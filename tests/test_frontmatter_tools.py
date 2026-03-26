"""Tests for frontmatter tools: get, set, delete."""


class TestGetFrontmatter:
    def test_gets_all_properties(self, tools):
        result = tools["get_frontmatter"](name="Alpha", key="")
        assert "tags:" in result or "aws" in result
        assert "module:" in result or "1" in result

    def test_gets_specific_key(self, tools):
        result = tools["get_frontmatter"](name="Alpha", key="module")
        assert "1" in result

    def test_missing_key(self, tools):
        result = tools["get_frontmatter"](name="Alpha", key="nonexistent")
        assert "not found" in result.lower() or "Available keys" in result

    def test_no_frontmatter(self, tools):
        result = tools["get_frontmatter"](name="Gamma", key="")
        assert "no frontmatter" in result.lower()

    def test_missing_note(self, tools):
        result = tools["get_frontmatter"](name="NoSuchNote", key="")
        assert "not found" in result


class TestSetFrontmatter:
    def test_sets_string_value(self, tools, vault_path):
        result = tools["set_frontmatter"](name="Alpha", key="status", value="active")
        assert "Successfully set" in result
        assert "active" in result

    def test_sets_numeric_value(self, tools):
        result = tools["set_frontmatter"](name="Alpha", key="priority", value="42")
        assert "Successfully set" in result
        assert "42" in result

    def test_sets_boolean_value(self, tools):
        result = tools["set_frontmatter"](name="Alpha", key="draft", value="true")
        assert "Successfully set" in result

    def test_sets_list_value(self, tools):
        result = tools["set_frontmatter"](name="Alpha", key="categories", value="cloud, devops, aws")
        assert "Successfully set" in result

    def test_overwrites_existing_key(self, tools):
        result = tools["set_frontmatter"](name="Alpha", key="module", value="99")
        assert "Old: 1" in result
        assert "New: 99" in result

    def test_creates_frontmatter_on_bare_note(self, tools, vault_path, cache):
        """Setting a property on a note with no frontmatter should add it."""
        result = tools["set_frontmatter"](name="Gamma", key="status", value="new")
        assert "Successfully set" in result
        content = (vault_path / "Gamma.md").read_text()
        assert "status:" in content

    def test_missing_note(self, tools):
        result = tools["set_frontmatter"](name="NoSuchNote", key="x", value="y")
        assert "not found" in result


class TestDeleteFrontmatter:
    def test_deletes_existing_key(self, tools, vault_path):
        result = tools["delete_frontmatter"](name="Alpha", key="module")
        assert "Successfully removed" in result
        assert "module" in result

    def test_missing_key(self, tools):
        result = tools["delete_frontmatter"](name="Alpha", key="nonexistent")
        assert "not found" in result.lower()

    def test_missing_note(self, tools):
        result = tools["delete_frontmatter"](name="NoSuchNote", key="x")
        assert "not found" in result
