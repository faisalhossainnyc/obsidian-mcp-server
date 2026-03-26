"""Tests for tag tools: list_tags, search_by_tag."""


class TestListTags:
    def test_finds_frontmatter_tags(self, tools):
        result = tools["list_tags"](limit=50)
        assert "#aws" in result or "#networking" in result or "#security" in result

    def test_counts_tags(self, tools):
        """Each tag should have a count in parentheses."""
        result = tools["list_tags"](limit=50)
        assert "(" in result and ")" in result

    def test_respects_limit(self, tools):
        result = tools["list_tags"](limit=2)
        assert "showing top 2" in result

    def test_handles_inline_tags(self, tools, vault_path, cache):
        """Inline #hashtag style tags should be detected."""
        (vault_path / "Tagged.md").write_text("Some content with #python and #devops inline.\n")
        cache.refresh()
        result = tools["list_tags"](limit=50)
        assert "#python" in result
        assert "#devops" in result


class TestSearchByTag:
    def test_finds_notes_with_frontmatter_tag(self, tools):
        result = tools["search_by_tag"](tag="aws")
        assert "Alpha" in result

    def test_finds_with_hash_prefix(self, tools):
        """Should work whether user passes #aws or aws."""
        result = tools["search_by_tag"](tag="#aws")
        assert "Alpha" in result

    def test_case_insensitive(self, tools):
        result = tools["search_by_tag"](tag="AWS")
        assert "Alpha" in result

    def test_no_results(self, tools):
        result = tools["search_by_tag"](tag="nonexistenttag")
        assert "No notes found" in result

    def test_finds_inline_tag(self, tools, vault_path, cache):
        (vault_path / "Inline.md").write_text("This note has #golang inline.\n")
        cache.refresh()
        result = tools["search_by_tag"](tag="golang")
        assert "Inline" in result
