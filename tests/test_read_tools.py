"""Tests for read-only tools: list, read, search, stats."""


class TestListNotes:
    def test_returns_all_notes(self, tools):
        result = tools["list_notes"](limit=50)
        assert "Found 4 notes" in result

    def test_respects_limit(self, tools):
        result = tools["list_notes"](limit=2)
        assert "Showing first 2" in result

    def test_contains_note_names(self, tools):
        result = tools["list_notes"](limit=50)
        assert "Alpha" in result
        assert "Delta" in result


class TestReadNoteByName:
    def test_reads_existing_note(self, tools):
        result = tools["read_note_by_name"](name="Alpha")
        assert "Alpha note content" in result

    def test_shows_frontmatter(self, tools):
        result = tools["read_note_by_name"](name="Alpha")
        assert "tags:" in result or "aws" in result

    def test_case_insensitive(self, tools):
        result = tools["read_note_by_name"](name="alpha")
        assert "Alpha note content" in result

    def test_missing_note(self, tools):
        result = tools["read_note_by_name"](name="NoSuchNote")
        assert "not found" in result

    def test_note_without_frontmatter(self, tools):
        result = tools["read_note_by_name"](name="Gamma")
        assert "Gamma has no frontmatter" in result


class TestSearchNotes:
    def test_finds_matching_content(self, tools):
        result = tools["search_notes"](query="Beta note content", limit=10)
        assert "Beta" in result

    def test_no_results(self, tools):
        result = tools["search_notes"](query="xyzzy_nonexistent_term", limit=10)
        assert "No notes found" in result

    def test_respects_limit(self, tools):
        # All 4 notes contain "note" in content
        result = tools["search_notes"](query="note", limit=2)
        # Should show 2 results with pagination info
        assert "showing 1-2" in result

    def test_case_insensitive_search(self, tools):
        result = tools["search_notes"](query="ALPHA NOTE", limit=10)
        assert "Alpha" in result


class TestGetVaultStats:
    def test_returns_correct_count(self, tools):
        result = tools["get_vault_stats"]()
        assert "Total notes: 4" in result

    def test_counts_wikilinks(self, tools):
        result = tools["get_vault_stats"]()
        assert "Total WikiLinks:" in result

    def test_counts_words(self, tools):
        result = tools["get_vault_stats"]()
        assert "Total words:" in result
