"""Tests for graph analysis tools: vault_graph, find_orphans, find_hubs, find_backlinks."""


class TestVaultGraph:
    def test_vault_wide_summary(self, tools):
        result = tools["vault_graph"](name="")
        assert "Vault Graph Summary" in result
        assert "4 notes" in result
        assert "hub" in result.lower()

    def test_single_note_analysis(self, tools):
        result = tools["vault_graph"](name="Alpha")
        assert "Graph analysis for 'Alpha'" in result
        assert "Outgoing links" in result
        assert "Backlinks" in result

    def test_well_connected_note(self, tools):
        """Alpha links to Beta and Gamma, and is linked from Beta and Delta."""
        result = tools["vault_graph"](name="Alpha")
        assert "beta" in result.lower()
        assert "gamma" in result.lower()

    def test_missing_note(self, tools):
        result = tools["vault_graph"](name="NoSuchNote")
        assert "not found" in result

    def test_shows_orphan_section(self, tools):
        result = tools["vault_graph"](name="")
        assert "Orphan notes" in result

    def test_shows_island_section(self, tools):
        result = tools["vault_graph"](name="")
        assert "Island notes" in result


class TestFindOrphans:
    def test_detects_orphan(self, tools, vault_path, cache):
        """A note with no links in or out should be detected."""
        (vault_path / "Lonely.md").write_text("No links here at all.\n")
        cache.refresh()
        result = tools["find_orphans"]()
        assert "Lonely" in result

    def test_connected_notes_not_orphans(self, tools):
        """Alpha has links — it should NOT be an orphan."""
        result = tools["find_orphans"]()
        assert "alpha" not in result.lower() or "No orphan" in result


class TestFindHubs:
    def test_returns_ranked_list(self, tools):
        result = tools["find_hubs"](limit=5)
        assert "hub notes" in result.lower()
        assert "1." in result  # Numbered ranking

    def test_alpha_is_a_hub(self, tools):
        """Alpha has the most connections (links to 2, linked from 2)."""
        result = tools["find_hubs"](limit=3)
        assert "alpha" in result.lower()

    def test_respects_limit(self, tools):
        result = tools["find_hubs"](limit=2)
        assert "Top 2" in result


class TestFindBacklinks:
    def test_finds_backlinks(self, tools):
        """Beta and Delta both link to Alpha."""
        result = tools["find_backlinks"](name="Alpha")
        assert "beta" in result.lower()
        assert "delta" in result.lower()

    def test_no_backlinks(self, tools):
        """Gamma has no frontmatter and nothing links to it by name...
        Actually Alpha links to Gamma, so it should have backlinks."""
        result = tools["find_backlinks"](name="Gamma")
        assert "alpha" in result.lower()

    def test_missing_note(self, tools):
        result = tools["find_backlinks"](name="NoSuchNote")
        assert "not found" in result

    def test_note_with_zero_backlinks(self, tools, vault_path, cache):
        (vault_path / "Isolated.md").write_text("Links to [[Alpha]] but nobody links here.\n")
        cache.refresh()
        result = tools["find_backlinks"](name="Isolated")
        assert "zero backlinks" in result.lower() or "No notes link" in result
