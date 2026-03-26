"""
Line-based editing tools: read_note_lines, insert_lines, replace_lines,
delete_lines, bulk_edit.
"""

import json
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from src.cache import VaultCache
from src.utils import prepare_lines


def register(mcp: FastMCP, cache: VaultCache, vault_path: Path) -> None:
    """Register all line-editing tools on the MCP server."""

    @mcp.tool()
    def read_note_lines(name: str, start_line: int = 1, end_line: int | None = None) -> str:
        """Read a note with line numbers displayed, optionally reading only a range.

        Use this before making line-based edits to see exact line numbers.

        Args:
            name: The name of the note to read
            start_line: First line to show (1-indexed, default: 1)
            end_line: Last line to show (inclusive, default: all lines)

        Returns:
            Note content with line numbers prefixed to each line
        """
        note_path = cache.find_note(name)
        if not note_path:
            return f"Note '{name}' not found in vault"

        try:
            with open(note_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            total_lines = len(lines)
            start_idx = max(0, start_line - 1)
            end_idx = end_line if end_line else total_lines

            max_line_num = min(end_idx, total_lines)
            padding = len(str(max_line_num))

            result_lines = []
            for i in range(start_idx, min(end_idx, total_lines)):
                line_num = str(i + 1).rjust(padding)
                line_content = lines[i].rstrip('\n')
                result_lines.append(f"{line_num} | {line_content}")

            header = f"**{name}** (lines {start_idx + 1}-{min(end_idx, total_lines)} of {total_lines})\n\n"
            return header + "\n".join(result_lines)

        except Exception as e:
            return f"Error reading note: {e}"

    @mcp.tool()
    def insert_lines(name: str, after_line: int, content: str) -> str:
        """Insert new lines after a specific line number.

        IMPORTANT: Before calling this tool, you MUST:
        1. Use read_note_lines to see the current content with line numbers
        2. Show the user what will be inserted and where
        3. Ask for explicit confirmation
        4. Only call this tool after the user confirms

        Args:
            name: The name of the note to edit
            after_line: Insert after this line number (0 = insert at beginning)
            content: The content to insert (can be multiple lines)

        Returns:
            Confirmation message with updated line count
        """
        note_path = cache.find_note(name)
        if not note_path:
            return f"Note '{name}' not found in vault"

        try:
            with open(note_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            if after_line < 0 or after_line > len(lines):
                return f"Error: Line {after_line} is out of range. Note has {len(lines)} lines (use 0-{len(lines)})."

            new_lines = prepare_lines(content)

            for i, new_line in enumerate(new_lines):
                lines.insert(after_line + i, new_line)

            with open(note_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)

            return (
                f"Successfully inserted {len(new_lines)} line(s) after line {after_line} "
                f"in '{name}'. Note now has {len(lines)} lines."
            )

        except Exception as e:
            return f"Error inserting lines: {e}"

    @mcp.tool()
    def replace_lines(name: str, start_line: int, end_line: int, content: str) -> str:
        """Replace a range of lines with new content.

        IMPORTANT: Before calling this tool, you MUST:
        1. Use read_note_lines to see the current content with line numbers
        2. Show the user what lines will be replaced and with what
        3. Ask for explicit confirmation
        4. Only call this tool after the user confirms

        Args:
            name: The name of the note to edit
            start_line: First line to replace (1-indexed)
            end_line: Last line to replace (inclusive)
            content: The new content to replace with (can be different number of lines)

        Returns:
            Confirmation message with line count changes
        """
        note_path = cache.find_note(name)
        if not note_path:
            return f"Note '{name}' not found in vault"

        try:
            with open(note_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            if start_line < 1 or start_line > len(lines):
                return f"Error: Start line {start_line} is out of range. Note has {len(lines)} lines."
            if end_line < start_line or end_line > len(lines):
                return f"Error: End line {end_line} is invalid. Must be >= {start_line} and <= {len(lines)}."

            start_idx = start_line - 1
            end_idx = end_line

            new_lines = prepare_lines(content)

            old_count = end_idx - start_idx
            lines[start_idx:end_idx] = new_lines

            with open(note_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)

            return (
                f"Successfully replaced lines {start_line}-{end_line} ({old_count} lines) "
                f"with {len(new_lines)} line(s) in '{name}'. Note now has {len(lines)} lines."
            )

        except Exception as e:
            return f"Error replacing lines: {e}"

    @mcp.tool()
    def delete_lines(name: str, start_line: int, end_line: int) -> str:
        """Delete a range of lines from a note.

        IMPORTANT: Before calling this tool, you MUST:
        1. Use read_note_lines to see the current content with line numbers
        2. Show the user which lines will be deleted
        3. Ask for explicit confirmation
        4. Only call this tool after the user confirms

        Args:
            name: The name of the note to edit
            start_line: First line to delete (1-indexed)
            end_line: Last line to delete (inclusive)

        Returns:
            Confirmation message with deleted line count
        """
        note_path = cache.find_note(name)
        if not note_path:
            return f"Note '{name}' not found in vault"

        try:
            with open(note_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            if start_line < 1 or start_line > len(lines):
                return f"Error: Start line {start_line} is out of range. Note has {len(lines)} lines."
            if end_line < start_line or end_line > len(lines):
                return f"Error: End line {end_line} is invalid. Must be >= {start_line} and <= {len(lines)}."

            start_idx = start_line - 1
            end_idx = end_line

            deleted_count = end_idx - start_idx
            original_count = len(lines)

            del lines[start_idx:end_idx]

            with open(note_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)

            return (
                f"Successfully deleted lines {start_line}-{end_line} ({deleted_count} lines) "
                f"from '{name}'. Note now has {len(lines)} lines (was {original_count})."
            )

        except Exception as e:
            return f"Error deleting lines: {e}"

    @mcp.tool()
    def bulk_edit(edits: str) -> str:
        """Apply multiple line edits across one or more notes in a single operation.

        IMPORTANT: Before calling this tool, you MUST:
        1. Use read_note_lines for each note to see current content with line numbers
        2. Show the user ALL planned edits with before/after context
        3. Ask for explicit confirmation
        4. Only call this tool after the user confirms

        CRITICAL - Line Number Handling:
        - Edits are grouped by note, then sorted and applied BOTTOM-TO-TOP within each note
        - This ensures line numbers remain valid as edits are applied
        - You should specify line numbers based on the ORIGINAL document
        - Do NOT try to calculate shifted line numbers yourself

        Args:
            edits: JSON string containing an array of edit operations.
                Each operation is an object with:
                - "name": The note name (required for each edit)
                - "op": One of "insert", "replace", or "delete"
                - For "insert": {"name": "Note", "op": "insert", "after_line": N, "content": "text"}
                - For "replace": {"name": "Note", "op": "replace", "start_line": N, "end_line": M, "content": "text"}
                - For "delete": {"name": "Note", "op": "delete", "start_line": N, "end_line": M}

        Returns:
            Summary of all edits applied or error message
        """
        # Parse edits JSON
        try:
            edit_list = json.loads(edits)
            if not isinstance(edit_list, list):
                return "Error: edits must be a JSON array of edit operations"
        except json.JSONDecodeError as e:
            return f"Error parsing edits JSON: {e}"

        if not edit_list:
            return "Error: No edits provided"

        # Group edits by note name
        edits_by_note: dict[str, list[tuple[int, dict]]] = {}
        for i, edit in enumerate(edit_list):
            if not isinstance(edit, dict):
                return f"Error: Edit {i + 1} must be an object"
            name = edit.get('name')
            if not name:
                return f"Error: Edit {i + 1} missing 'name' field"
            if name not in edits_by_note:
                edits_by_note[name] = []
            edits_by_note[name].append((i, edit))

        # Load all target files and store backups for rollback
        note_data: dict[str, dict] = {}
        backups: dict[str, list[str]] = {}  # name -> original lines for rollback

        for name in edits_by_note:
            note_path = cache.find_note(name)
            if not note_path:
                return f"Note '{name}' not found in vault"
            try:
                with open(note_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                note_data[name] = {
                    'path': note_path,
                    'lines': lines,
                    'original_count': len(lines),
                }
                backups[name] = list(lines)  # Copy for rollback
            except Exception as e:
                return f"Error reading note '{name}': {e}"

        # Validate all edits before applying any
        for name, indexed_edits in edits_by_note.items():
            lines = note_data[name]['lines']
            for i, edit in indexed_edits:
                op = edit.get('op')
                if op not in ('insert', 'replace', 'delete'):
                    return f"Error: Edit {i + 1} has invalid 'op': {op}. Must be 'insert', 'replace', or 'delete'"

                if op == 'insert':
                    if 'after_line' not in edit:
                        return f"Error: Edit {i + 1} (insert) missing 'after_line'"
                    if 'content' not in edit:
                        return f"Error: Edit {i + 1} (insert) missing 'content'"
                    after_line = edit['after_line']
                    if not isinstance(after_line, int) or after_line < 0 or after_line > len(lines):
                        return (
                            f"Error: Edit {i + 1} has invalid after_line: {after_line}. "
                            f"'{name}' has {len(lines)} lines (use 0-{len(lines)})"
                        )

                elif op in ('replace', 'delete'):
                    if 'start_line' not in edit or 'end_line' not in edit:
                        return f"Error: Edit {i + 1} ({op}) missing 'start_line' or 'end_line'"
                    start = edit['start_line']
                    end = edit['end_line']
                    if not isinstance(start, int) or start < 1 or start > len(lines):
                        return f"Error: Edit {i + 1} has invalid start_line: {start}. '{name}' has {len(lines)} lines"
                    if not isinstance(end, int) or end < start or end > len(lines):
                        return f"Error: Edit {i + 1} has invalid end_line: {end}. Must be {start}-{len(lines)}"
                    if op == 'replace' and 'content' not in edit:
                        return f"Error: Edit {i + 1} (replace) missing 'content'"

        # Apply edits (with rollback on failure)
        all_results = []
        written_notes: list[str] = []  # Track which notes have been written for rollback

        try:
            for name, indexed_edits in edits_by_note.items():
                lines = note_data[name]['lines']
                original_count = note_data[name]['original_count']

                # Sort edits bottom-to-top to preserve line numbers
                def get_sort_key(indexed_edit: tuple[int, dict]) -> int:
                    _, edit = indexed_edit
                    if edit['op'] == 'insert':
                        return edit['after_line']
                    return edit['start_line']

                sorted_edits = sorted(indexed_edits, key=get_sort_key, reverse=True)

                note_results = []
                for _, edit in sorted_edits:
                    op = edit['op']

                    if op == 'insert':
                        after_line = edit['after_line']
                        new_lines = prepare_lines(edit['content'])
                        for j, new_line in enumerate(new_lines):
                            lines.insert(after_line + j, new_line)
                        note_results.append(f"Inserted {len(new_lines)} line(s) after line {after_line}")

                    elif op == 'replace':
                        start = edit['start_line']
                        end = edit['end_line']
                        new_lines = prepare_lines(edit['content'])
                        old_count = end - start + 1
                        lines[start - 1:end] = new_lines
                        note_results.append(
                            f"Replaced lines {start}-{end} ({old_count} lines) with {len(new_lines)} line(s)"
                        )

                    elif op == 'delete':
                        start = edit['start_line']
                        end = edit['end_line']
                        deleted_count = end - start + 1
                        del lines[start - 1:end]
                        note_results.append(f"Deleted lines {start}-{end} ({deleted_count} lines)")

                # Write modified content
                with open(note_data[name]['path'], 'w', encoding='utf-8') as f:
                    f.writelines(lines)
                written_notes.append(name)

                all_results.append({
                    'name': name,
                    'edits': list(reversed(note_results)),
                    'original_count': original_count,
                    'new_count': len(lines),
                })

        except Exception as e:
            # Rollback all written notes to their original state
            for written_name in written_notes:
                try:
                    with open(note_data[written_name]['path'], 'w', encoding='utf-8') as f:
                        f.writelines(backups[written_name])
                except Exception:
                    pass  # Best-effort rollback
            return f"Error during bulk edit (all changes rolled back): {e}"

        # Build summary
        total_edits = len(edit_list)
        summary = f"Successfully applied {total_edits} edit(s) across {len(all_results)} note(s):\n\n"

        for result in all_results:
            summary += f"**{result['name']}** ({result['original_count']} → {result['new_count']} lines):\n"
            for edit_desc in result['edits']:
                summary += f"  - {edit_desc}\n"
            summary += "\n"

        return summary.strip()
