"""Tests for enhanced search (regex, path filter, pagination) and recent_notes."""

import time


class TestSearchRegex:
    def test_regex_search(self, tools):
        result = tools["search_notes"](query=r"Links?\s+to", use_regex=True)
        assert "Alpha" in result

    def test_invalid_regex(self, tools):
        result = tools["search_notes"](query="[invalid", use_regex=True)
        assert "Invalid regex" in result

    def test_regex_case_insensitive(self, tools):
        result = tools["search_notes"](query=r"ALPHA\s+NOTE", use_regex=True)
        assert "Alpha" in result


class TestSearchPathFilter:
    def test_filter_by_folder(self, tools):
        result = tools["search_notes"](query="Delta", path_filter="Projects")
        assert "Delta" in result

    def test_filter_excludes_other_folders(self, tools):
        # "Gamma has no frontmatter" only exists in root Gamma.md, not in Projects/
        result = tools["search_notes"](query="Gamma has no frontmatter", path_filter="Projects")
        assert "No notes found" in result


class TestSearchPagination:
    def test_offset(self, tools):
        # First get all results
        all_results = tools["search_notes"](query="note", limit=50, offset=0)
        # Then get page 2
        page2 = tools["search_notes"](query="note", limit=2, offset=2)
        assert "showing" in page2.lower() or "of" in page2

    def test_offset_beyond_results(self, tools):
        result = tools["search_notes"](query="note", limit=10, offset=999)
        assert "No more results" in result


class TestRecentNotes:
    def test_finds_recently_modified(self, tools, vault_path):
        # All test notes were just created, so they should be "recent"
        result = tools["recent_notes"](days=1, limit=10)
        assert "Alpha" in result or "Beta" in result

    def test_respects_limit(self, tools):
        result = tools["recent_notes"](days=365, limit=2)
        assert "showing 2" in result

    def test_no_recent_notes(self, tools, vault_path):
        # Set all notes to an old mtime
        import os
        old_time = time.time() - (400 * 86400)  # 400 days ago
        for md in vault_path.rglob("*.md"):
            os.utime(md, (old_time, old_time))
        result = tools["recent_notes"](days=7, limit=10)
        assert "No notes modified" in result
