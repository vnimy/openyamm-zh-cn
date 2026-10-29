"""Tab separated table I/O that matches engine/TextTable.cpp exactly.

The game stores its text tables as tab separated rows where a cell may be quoted; inside quotes a doubled quote is a
literal quote and tabs and newlines are data. Everything the localization patch writes must parse back to the same
cells the engine would read, so this module mirrors that parser instead of using the csv module.
"""

from __future__ import annotations

from typing import Iterable, List


def has_closing_quote_before_tab(contents: str, index: int) -> bool:
    """True when a closing quote comes before the next tab, as TextTable.cpp decides whether a cell is quoted."""
    while index < len(contents):
        if contents[index] == "\t":
            return False
        if contents[index] == '"':
            if index + 1 < len(contents) and contents[index + 1] == '"':
                index += 1
                continue
            return True
        index += 1
    return False


def parse(contents: str) -> List[List[str]]:
    rows: List[List[str]] = []
    row: List[str] = []
    cell: List[str] = []
    inside_quotes = False
    index = 0

    while index < len(contents):
        character = contents[index]

        if character == '"':
            if inside_quotes and index + 1 < len(contents) and contents[index + 1] == '"':
                cell.append('"')
                index += 1
            elif inside_quotes:
                inside_quotes = False
            elif not cell and has_closing_quote_before_tab(contents, index + 1):
                inside_quotes = True
            else:
                cell.append(character)
            index += 1
            continue

        if character == "\r":
            index += 1
            continue

        if character == "\t" and not inside_quotes:
            row.append("".join(cell))
            cell = []
            index += 1
            continue

        if character == "\n" and not inside_quotes:
            row.append("".join(cell))
            cell = []
            rows.append(row)
            row = []
            index += 1
            continue

        cell.append(character)
        index += 1

    if inside_quotes:
        raise ValueError("unterminated quoted cell")

    if row or cell:
        row.append("".join(cell))
        rows.append(row)

    return rows


def _format_cell(value: str) -> str:
    # A quote in the middle of a cell is literal to the parser; only a leading quote would start quoted mode, and only
    # tabs and newlines need quoting to stay in the cell.
    if "\t" in value or "\n" in value or value.startswith('"'):
        return '"' + value.replace('"', '""') + '"'

    return value


def serialize(rows: Iterable[List[str]], trailing_newline: bool = True) -> str:
    lines = ["\t".join(_format_cell(cell) for cell in row) for row in rows]
    text = "\n".join(lines)

    return text + "\n" if trailing_newline else text
