# Obsidian MCP Server

This project is a high-performance [Model Context Protocol](https://modelcontextprotocol.io/) server for [Obsidian](https://obsidian.md) vaults. It gives AI assistants like Claude, Gemini, and Cursor ability to manage your Obsidian vault programmatically. It provides **28 tools** organized into categories: read, write, edit, frontmatter, tags, links, graph analysis, and organization.

**Key design principles:**
- **Simple setup.** Works directly with vault files on disk. No Obsidian plugins, no REST API, no Obsidian running in the background.
- **Performance.** In-memory cache + real-time file watching (watchdog) enables speedy 0(1) note lookups.
- **Flexible.** 28 tools covering reading, writing, line-by-line editing, bulk editing, graph analysis, and more.
- **Safety.** Path traversal protection, atomic bulk operations with rollback, comprehensive test suite (139 tests).

This server is compatible with any MCP client: Claude, Gemini, Cursor, or any applications that support the MCP protocol.

## Tools

| Category | Tool | Description |
|---|---|---|
| Read | `list_notes` | List all notes in the vault (paginated) |
| Read | `read_note_by_name` | Read a note by name (no .md extension needed) |
| Read | `search_notes` | Full-text search with regex support, path filtering, and pagination |
| Read | `get_vault_stats` | Vault-wide statistics (note count, total links, folder breakdown) |
| Read | `recent_notes` | Notes modified within the last N days |
| Write | `create_note` | Create a new note, optionally in a subfolder |
| Write | `update_note` | Replace a note's entire content |
| Write | `append_to_note` | Append content to the end of a note |
| Write | `delete_note` | Delete a note (requires confirmation flag) |
| Edit | `read_note_lines` | Read a note with line numbers (supports ranges) |
| Edit | `insert_lines` | Insert content after a specific line |
| Edit | `replace_lines` | Replace a range of lines |
| Edit | `delete_lines` | Delete a range of lines |
| Edit | `bulk_edit` | Apply multiple edits across multiple notes atomically, with automatic rollback on failure |
| Frontmatter | `get_frontmatter` | Read all YAML frontmatter or a specific property |
| Frontmatter | `set_frontmatter` | Set a frontmatter property (auto-detects types: lists, ints, bools) |
| Frontmatter | `delete_frontmatter` | Remove a frontmatter property |
| Tags | `list_tags` | All tags across the vault with occurrence counts (frontmatter + inline #hashtags) |
| Tags | `search_by_tag` | Find notes by tag (case-insensitive) |
| Links | `get_note_links` | Extract all WikiLinks from a note |
| Links | `validate_wikilinks` | Check which links in a note point to existing vs. missing notes |
| Graph Analysis | `vault_graph` | Vault-wide link structure summary, or per-note analysis with related note suggestions |
| Graph Analysis | `find_orphans` | Notes with zero connections (no incoming or outgoing links) |
| Graph Analysis | `find_hubs` | Most connected notes, ranked by total link count |
| Graph Analysis | `find_backlinks` | All notes linking to a given note |
| Organization | `move_note` | Move a note to a different folder with automatic backlink updates across the vault |
| Organization | `find_folder` | Search for folders by name or partial match |
| Organization | `create_folder` | Create a new folder |

## Setup

### Prerequisites

- Python 3.10+
- An Obsidian vault

### Install

Clone the repo and set up a Python virtual environment:

```bash
git clone https://github.com/faisalhossainnyc/obsidian-mcp-server.git
cd obsidian-mcp-server
python -m venv venv
```

**Activate the virtual environment:**

- **macOS/Linux:** `source venv/bin/activate`
- **Windows:** `venv\Scripts\activate`

Then install dependencies:

```bash
pip install -r requirements.txt
```

### Configure

Copy the example environment file and set your vault path:

```bash
cp .env.example .env
```

Edit `.env` and set `VAULT_PATH` to your vault directory (replace `you` with your actual username and adjust the path as needed):

- **macOS:** `VAULT_PATH="/Users/you/Documents/My Obsidian Vault"`
- **Linux:** `VAULT_PATH="/home/you/Documents/My Obsidian Vault"`
- **Windows:** `VAULT_PATH="C:\Users\you\Documents\My Obsidian Vault"`

### Start the Server

All MCP clients (Claude Desktop, Cursor, Gemini CLI, etc.) launch the server process for you based on the config below, so you don't need to start it manually. The `command` field in the config tells the client how to start it.

If you want to run the server manually (e.g., to test it or debug):

```bash
source venv/bin/activate        # Windows: venv\Scripts\activate
python -m src.server
```

You should see output confirming the vault cache has loaded and the server is listening.

### Connect to an MCP Client

This server uses the standard `mcpServers` configuration format supported by all major MCP clients. Add the following to your client's config file, replacing the three placeholders with your actual paths:

- `command` — full path to the Python binary inside your venv (e.g. `/Users/you/Projects/obsidian-mcp-server/venv/bin/python` on macOS/Linux, or `C:\Projects\obsidian-mcp-server\venv\Scripts\python.exe` on Windows)
- `cwd` — full path to the cloned repo folder (e.g. `/Users/you/Projects/obsidian-mcp-server`)
- `VAULT_PATH` — full path to your Obsidian vault folder

```json
{
  "mcpServers": {
    "obsidian": {
      "command": "/path/to/obsidian-mcp-server/venv/bin/python",
      "args": ["-m", "src.server"],
      "cwd": "/path/to/obsidian-mcp-server",
      "env": {
        "VAULT_PATH": "/path/to/your/vault"
      }
    }
  }
}
```

Find your config file based on your client:

| Client | Config File |
|---|---|
| Claude Desktop (macOS) | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| Claude Desktop (Linux) | `~/.config/Claude/claude_desktop_config.json` |
| Claude Desktop (Windows) | `%APPDATA%\Claude\claude_desktop_config.json` |
| Gemini CLI | `~/.gemini/settings.json` |
| Cursor | `.cursor/mcp.json` in your project root |
| Claude Code | `~/.claude/claude_code_config.json` |


This server implements the **Model Context Protocol (MCP)**, an open standard adopted by Claude, Gemini CLI, ChatGPT, Cursor, VS Code, and more. If your client isn't listed above, check its documentation for the MCP config file location. The JSON format above should work universally.

## Architecture

```
src/
├── server.py          # Entry point — initializes FastMCP + vault cache, registers tools
├── cache.py           # VaultCache: in-memory index with watchdog file watcher (O(1) lookups)
├── utils.py           # Shared utilities: safe_resolve(), read_note(), extract_wikilinks()
└── tools/
    ├── read.py        # 5 tools — list, read, search, stats, recent
    ├── write.py       # 4 tools — create, update, append, delete
    ├── edit.py        # 5 tools — line-level editing with bulk edit + rollback
    ├── frontmatter.py # 3 tools — YAML frontmatter get/set/delete
    ├── tags.py        # 2 tools — tag listing and search
    ├── links.py       # 2 tools — WikiLink extraction and validation
    ├── graph.py       # 4 tools — vault graph analysis (orphans, hubs, backlinks)
    ├── move.py        # 1 tool  — move with backlink updates
    └── folders.py     # 2 tools — folder search and creation
```

On startup **VaultCache** builds an in-memory `{name → Path}` index of every `.md` file in the vault. A `watchdog` file observer keeps this index in sync as files are created, deleted, moved, or renamed. every tool call does an O(1) dict lookup instead of scanning the filesystem.

All path-accepting tools use `safe_resolve()` to prevent path traversal attacks (e.g., `../../etc/passwd` is rejected).

The `bulk_edit` tool reads all target files into memory before applying changes. If any write fails mid-operation, it restores every file from the in-memory backup with no partial writes.

## Running Tests

```bash
./run_tests.sh
```

Or directly:

```bash
PYTHONPATH=. python -m pytest tests/ -v
```

The test suite uses a temporary vault fixture that rebuilds from scratch before each test, so tests are fully isolated and don't touch your real vault.

## License

MIT
