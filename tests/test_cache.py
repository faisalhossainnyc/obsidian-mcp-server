"""Tests for VaultCache — the core performance layer."""


class TestCacheIndex:
    def test_finds_all_visible_notes(self, cache):
        assert cache.note_count() == 4  # Alpha, Beta, Gamma, Delta

    def test_ignores_hidden_folders(self, cache):
        """Notes inside .obsidian should not appear."""
        assert cache.find_note("config") is None

    def test_find_note_case_insensitive(self, cache):
        assert cache.find_note("alpha") is not None
        assert cache.find_note("ALPHA") is not None
        assert cache.find_note("Alpha") is not None

    def test_find_note_returns_none_for_missing(self, cache):
        assert cache.find_note("does_not_exist") is None

    def test_find_note_in_subfolder(self, cache):
        path = cache.find_note("Delta")
        assert path is not None
        assert "Projects" in str(path)

    def test_get_all_notes_respects_limit(self, cache):
        assert len(cache.get_all_notes(limit=2)) == 2

    def test_get_all_note_names(self, cache):
        names = cache.get_all_note_names()
        assert {"alpha", "beta", "gamma", "delta"} == names

    def test_refresh_rebuilds_index(self, cache, vault_path):
        """After adding a file, refresh should pick it up."""
        (vault_path / "Epsilon.md").write_text("New note.\n")
        cache.refresh()
        assert cache.find_note("Epsilon") is not None
        assert cache.note_count() == 5
