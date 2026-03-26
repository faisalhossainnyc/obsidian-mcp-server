"""
Graph analysis tools: vault_graph, find_orphans, find_hubs, find_backlinks.

Builds a link graph from WikiLinks across all notes and derives
structural insights — no external dependencies (no NetworkX needed).
"""

from pathlib import Path

from mcp.server.fastmcp import FastMCP

from src.cache import VaultCache
from src.utils import extract_wikilinks


def _build_graph(cache: VaultCache) -> tuple[
    dict[str, list[str]],   # outgoing: note -> [notes it links to]
    dict[str, list[str]],   # incoming: note -> [notes that link to it]
    set[str],               # all known note names (lowercase)
]:
    """Build directed link graph from all notes in the vault.

    Returns outgoing links, incoming links (backlinks), and the set
    of all note names. All keys/values are lowercase stems.
    """
    outgoing: dict[str, list[str]] = {}
    incoming: dict[str, list[str]] = {}
    all_names = cache.get_all_note_names()

    # Initialize empty lists for every known note
    for name in all_names:
        outgoing[name] = []
        incoming[name] = []

    for note_path in cache.get_all_notes():
        source = note_path.stem.lower()
        try:
            with open(note_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception:
            continue

        links = extract_wikilinks(content)
        for link in links:
            target = link.lower()
            if target in all_names:
                outgoing[source].append(target)
                incoming[target].append(source)

    return outgoing, incoming, all_names


def register(mcp: FastMCP, cache: VaultCache, vault_path: Path) -> None:
    """Register graph analysis tools on the MCP server."""

    @mcp.tool()
    def vault_graph(name: str = "") -> str:
        """Analyze the link structure of the vault or a specific note.

        When called without a name, returns a high-level summary of the
        vault's link graph. When called with a note name, shows that
        note's connections (outgoing links, backlinks, and suggested
        related notes).

        Args:
            name: Optional note name. If empty, returns vault-wide summary.

        Returns:
            Graph analysis results
        """
        outgoing, incoming, all_names = _build_graph(cache)

        if name:
            key = name.lower()
            if key not in all_names:
                return f"Note '{name}' not found in vault"

            out_links = outgoing.get(key, [])
            back_links = incoming.get(key, [])

            # Find related notes (notes that share links with this note)
            related: dict[str, int] = {}
            for linked in out_links:
                for neighbor in outgoing.get(linked, []):
                    if neighbor != key and neighbor not in out_links:
                        related[neighbor] = related.get(neighbor, 0) + 1
            for linker in back_links:
                for neighbor in outgoing.get(linker, []):
                    if neighbor != key and neighbor not in out_links:
                        related[neighbor] = related.get(neighbor, 0) + 1

            result = f"**Graph analysis for '{name}':**\n\n"

            result += f"**Outgoing links ({len(out_links)}):**\n"
            if out_links:
                for link in sorted(set(out_links)):
                    result += f"- [[{link}]]\n"
            else:
                result += "- None\n"

            result += f"\n**Backlinks ({len(set(back_links))}):**\n"
            if back_links:
                for link in sorted(set(back_links)):
                    result += f"- [[{link}]]\n"
            else:
                result += "- None (this is an orphan note)\n"

            if related:
                top_related = sorted(related.items(), key=lambda x: -x[1])[:10]
                result += f"\n**Related notes (by shared connections):**\n"
                for rel_name, score in top_related:
                    result += f"- [[{rel_name}]] (score: {score})\n"

            return result.rstrip()

        # Vault-wide summary
        total = len(all_names)
        orphans = [n for n in all_names if not incoming[n] and not outgoing[n]]
        islands = [n for n in all_names if not incoming[n] and outgoing[n]]
        dead_ends = [n for n in all_names if incoming[n] and not outgoing[n]]

        # Top hubs by total connections
        connectivity = {
            n: len(set(outgoing[n])) + len(set(incoming[n]))
            for n in all_names
        }
        top_hubs = sorted(connectivity.items(), key=lambda x: -x[1])[:10]

        total_edges = sum(len(v) for v in outgoing.values())

        result = f"**Vault Graph Summary** ({total} notes, {total_edges} links):\n\n"

        result += f"**Top connected notes (hubs):**\n"
        for hub_name, conn in top_hubs:
            out_c = len(set(outgoing[hub_name]))
            in_c = len(set(incoming[hub_name]))
            result += f"- [[{hub_name}]] — {out_c} outgoing, {in_c} backlinks\n"

        result += f"\n**Orphan notes ({len(orphans)})** — no links in or out:\n"
        if orphans:
            for o in sorted(orphans)[:20]:
                result += f"- [[{o}]]\n"
            if len(orphans) > 20:
                result += f"- ... and {len(orphans) - 20} more\n"
        else:
            result += "- None! Every note is connected.\n"

        result += f"\n**Island notes ({len(islands)})** — link out but nothing links to them:\n"
        if islands:
            for i in sorted(islands)[:15]:
                result += f"- [[{i}]]\n"
            if len(islands) > 15:
                result += f"- ... and {len(islands) - 15} more\n"
        else:
            result += "- None\n"

        result += f"\n**Dead-end notes ({len(dead_ends)})** — linked to but contain no outgoing links:\n"
        if dead_ends:
            for d in sorted(dead_ends)[:15]:
                result += f"- [[{d}]]\n"
            if len(dead_ends) > 15:
                result += f"- ... and {len(dead_ends) - 15} more\n"
        else:
            result += "- None\n"

        return result.rstrip()

    @mcp.tool()
    def find_orphans() -> str:
        """Find notes with no incoming or outgoing WikiLinks.

        These are isolated notes that aren't connected to anything else
        in the vault — candidates for linking, archiving, or deletion.

        Returns:
            List of orphan notes
        """
        outgoing, incoming, all_names = _build_graph(cache)

        orphans = sorted(
            n for n in all_names
            if not incoming[n] and not outgoing[n]
        )

        if not orphans:
            return "No orphan notes found — every note has at least one link."

        result = f"**Orphan notes ({len(orphans)})** — no links in or out:\n"
        for name in orphans:
            note_path = cache.find_note(name)
            if note_path:
                rel = note_path.relative_to(vault_path)
                result += f"- {note_path.stem} ({rel})\n"
            else:
                result += f"- {name}\n"

        return result.rstrip()

    @mcp.tool()
    def find_hubs(limit: int = 10) -> str:
        """Find the most connected notes in the vault.

        Hub notes have the most combined incoming and outgoing links,
        making them central to the vault's knowledge structure.

        Args:
            limit: Number of top hubs to return (default 10)

        Returns:
            Top hub notes ranked by total connections
        """
        outgoing, incoming, all_names = _build_graph(cache)

        connectivity = []
        for name in all_names:
            out_c = len(set(outgoing[name]))
            in_c = len(set(incoming[name]))
            if out_c + in_c > 0:
                connectivity.append((name, out_c, in_c))

        connectivity.sort(key=lambda x: -(x[1] + x[2]))
        top = connectivity[:limit]

        if not top:
            return "No connected notes found in the vault."

        result = f"**Top {len(top)} hub notes:**\n"
        for i, (name, out_c, in_c) in enumerate(top, 1):
            total = out_c + in_c
            result += f"{i}. [[{name}]] — {total} connections ({out_c} outgoing, {in_c} backlinks)\n"

        return result.rstrip()

    @mcp.tool()
    def find_backlinks(name: str) -> str:
        """Find all notes that link TO a specific note.

        Args:
            name: The note name to find backlinks for

        Returns:
            List of notes that contain WikiLinks to this note
        """
        key = name.lower()
        if key not in cache.get_all_note_names():
            return f"Note '{name}' not found in vault"

        _, incoming, _ = _build_graph(cache)
        backlinks = sorted(set(incoming.get(key, [])))

        if not backlinks:
            return f"No notes link to '{name}'. It has zero backlinks."

        result = f"**Backlinks to '{name}' ({len(backlinks)}):**\n"
        for bl in backlinks:
            note_path = cache.find_note(bl)
            if note_path:
                result += f"- [[{note_path.stem}]] ({note_path.relative_to(vault_path)})\n"
            else:
                result += f"- [[{bl}]]\n"

        return result.rstrip()
