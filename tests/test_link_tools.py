"""Tests for link tools: get_note_links, validate_wikilinks."""


class TestGetNoteLinks:
    def test_extracts_simple_links(self, tools):
        result = tools["get_note_links"](name="Alpha")
        assert "[[Beta]]" in result

    def test_extracts_aliased_links(self, tools):
        """[[Gamma|see Gamma]] should extract as Gamma."""
        result = tools["get_note_links"](name="Alpha")
        assert "[[Gamma]]" in result

    def test_no_links(self, tools):
        result = tools["get_note_links"](name="Gamma")
        assert "No WikiLinks" in result

    def test_missing_note(self, tools):
        result = tools["get_note_links"](name="NoSuchNote")
        assert "not found" in result


class TestValidateWikilinks:
    def test_identifies_valid_links(self, tools):
        result = tools["validate_wikilinks"](name="Alpha")
        assert "Valid links" in result
        assert "Beta" in result

    def test_identifies_broken_links(self, tools):
        result = tools["validate_wikilinks"](name="Delta")
        assert "Broken links" in result
        assert "Nonexistent Note" in result

    def test_no_links_to_validate(self, tools):
        result = tools["validate_wikilinks"](name="Gamma")
        assert "No WikiLinks to validate" in result

    def test_missing_note(self, tools):
        result = tools["validate_wikilinks"](name="NoSuchNote")
        assert "not found" in result
