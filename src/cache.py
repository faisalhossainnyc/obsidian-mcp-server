"""
Vault Cache — In-memory index of all notes with file-watcher refresh.

Eliminates the O(n) full-vault scan that previously ran on every tool call.
Uses watchdog (already in requirements) to detect file changes and update
the index automatically.
"""

import threading
import time
from pathlib import Path

from watchdog.events import FileSystemEventHandler, FileSystemEvent
from watchdog.observers import Observer


class VaultCache:
    """Thread-safe in-memory index of vault notes.

    Provides O(1) lookups by note name and maintains freshness via
    filesystem watching. Falls back to a full rescan if the watcher
    is unavailable.
    """

    def __init__(self, vault_path: Path) -> None:
        self.vault_path = vault_path
        self._lock = threading.Lock()

        # Primary index: lowercase stem -> Path
        self._name_index: dict[str, Path] = {}
        # All note paths, sorted by mtime (most recent first)
        self._all_notes: list[Path] = []

        self._observer: Observer | None = None
        self._build_index()
        self._start_watcher()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_all_notes(self, limit: int | None = None) -> list[Path]:
        """Return notes sorted by modification time (most recent first)."""
        with self._lock:
            if limit:
                return self._all_notes[:limit]
            return list(self._all_notes)

    def find_note(self, name: str) -> Path | None:
        """O(1) lookup by note name (case-insensitive, without .md)."""
        with self._lock:
            return self._name_index.get(name.lower())

    def get_all_note_names(self) -> set[str]:
        """Return set of all lowercase note stems for membership checks."""
        with self._lock:
            return set(self._name_index.keys())

    def note_count(self) -> int:
        with self._lock:
            return len(self._all_notes)

    def refresh(self) -> None:
        """Force a full index rebuild."""
        self._build_index()

    def shutdown(self) -> None:
        """Stop the file watcher cleanly."""
        if self._observer and self._observer.is_alive():
            self._observer.stop()
            self._observer.join(timeout=5)

    # ------------------------------------------------------------------
    # Index management
    # ------------------------------------------------------------------

    def _build_index(self) -> None:
        """Full scan of vault — runs once at startup and on fallback."""
        name_index: dict[str, Path] = {}
        all_notes: list[Path] = []

        if not self.vault_path.exists():
            with self._lock:
                self._name_index = name_index
                self._all_notes = all_notes
            return

        for md_file in self.vault_path.rglob("*.md"):
            # Skip hidden folders (e.g., .obsidian, .trash)
            if any(part.startswith('.') for part in md_file.relative_to(self.vault_path).parts):
                continue
            all_notes.append(md_file)
            name_index[md_file.stem.lower()] = md_file

        # Sort by modification time, most recent first
        all_notes.sort(key=lambda p: p.stat().st_mtime, reverse=True)

        with self._lock:
            self._name_index = name_index
            self._all_notes = all_notes

    def _add_note(self, path: Path) -> None:
        """Add or update a single note in the index."""
        if not path.suffix == '.md':
            return
        if any(part.startswith('.') for part in path.relative_to(self.vault_path).parts):
            return

        with self._lock:
            stem_lower = path.stem.lower()
            # Remove old entry if name changed (rename case)
            self._name_index[stem_lower] = path
            # Update all_notes list
            self._all_notes = [p for p in self._all_notes if p != path]
            self._all_notes.insert(0, path)  # Most recently modified goes first

    def _remove_note(self, path: Path) -> None:
        """Remove a note from the index."""
        with self._lock:
            stem_lower = path.stem.lower()
            if stem_lower in self._name_index and self._name_index[stem_lower] == path:
                del self._name_index[stem_lower]
            self._all_notes = [p for p in self._all_notes if p != path]

    # ------------------------------------------------------------------
    # File watcher
    # ------------------------------------------------------------------

    def _start_watcher(self) -> None:
        """Start watchdog observer to keep index fresh."""
        if not self.vault_path.exists():
            return

        try:
            handler = _VaultEventHandler(self)
            self._observer = Observer()
            self._observer.schedule(handler, str(self.vault_path), recursive=True)
            self._observer.daemon = True
            self._observer.start()
        except Exception:
            # If watcher fails, cache still works — just won't auto-refresh.
            # Users can call refresh() manually.
            self._observer = None


class _VaultEventHandler(FileSystemEventHandler):
    """Handles filesystem events to keep the cache up to date."""

    def __init__(self, cache: VaultCache) -> None:
        self.cache = cache
        # Debounce: avoid rapid-fire rebuilds during bulk operations
        self._last_event_time = 0.0
        self._debounce_seconds = 0.5

    def _should_process(self, path: str) -> bool:
        """Only process .md files outside hidden directories."""
        p = Path(path)
        if p.suffix != '.md':
            return False
        try:
            rel = p.relative_to(self.cache.vault_path)
            if any(part.startswith('.') for part in rel.parts):
                return False
        except ValueError:
            return False
        return True

    def on_created(self, event: FileSystemEvent) -> None:
        if not event.is_directory and self._should_process(event.src_path):
            self.cache._add_note(Path(event.src_path))

    def on_deleted(self, event: FileSystemEvent) -> None:
        if not event.is_directory and self._should_process(event.src_path):
            self.cache._remove_note(Path(event.src_path))

    def on_modified(self, event: FileSystemEvent) -> None:
        if not event.is_directory and self._should_process(event.src_path):
            self.cache._add_note(Path(event.src_path))

    def on_moved(self, event: FileSystemEvent) -> None:
        if not event.is_directory:
            if self._should_process(event.src_path):
                self.cache._remove_note(Path(event.src_path))
            if self._should_process(event.dest_path):
                self.cache._add_note(Path(event.dest_path))
