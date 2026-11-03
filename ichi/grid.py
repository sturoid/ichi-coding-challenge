"""HTML table -> rectangular grid with rowspan/colspan expanded.

OCR'd and scraped tables are messy: headers may be <td> rather than <th>, spans
appear on body cells, colspan="" means 1, footnote markers sit in <sup>, and
words are split across lines. This module keeps all of that out of the rules.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from html.parser import HTMLParser


@dataclass
class Cell:
    text: str                      # visible text, <sup> excluded, whitespace collapsed
    footnotes: list[str] = field(default_factory=list)
    rowspan: int = 1
    colspan: int = 1
    is_th: bool = False
    row: int = 0                   # source <tr> index of the originating cell
    col: int = 0                   # grid column where it starts

    @property
    def compact(self) -> str:
        """Text with all whitespace removed, upper-cased. OCR splits words ('SCREE N')."""
        return re.sub(r"\s+", "", self.text).upper()


def _span(value: str | None) -> int:
    try:
        return max(1, int(value)) if value not in (None, "") else 1
    except ValueError:
        return 1


class _TableParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.rows: list[list[Cell]] = []
        self._cell: Cell | None = None
        self._buf: list[str] = []
        self._sup: list[str] | None = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "tr":
            self.rows.append([])
        elif tag in ("td", "th"):
            self._cell = Cell("", rowspan=_span(a.get("rowspan")), colspan=_span(a.get("colspan")),
                              is_th=(tag == "th"), row=len(self.rows) - 1)
            self._buf = []
        elif tag == "sup" and self._cell is not None:
            self._sup = []
        elif tag == "br" and self._cell is not None:
            self._buf.append(" ")

    def handle_endtag(self, tag):
        if tag == "sup" and self._sup is not None and self._cell is not None:
            marks = [m.strip() for m in "".join(self._sup).split(",") if m.strip()]
            self._cell.footnotes.extend(marks)
            self._sup = None
        elif tag in ("td", "th") and self._cell is not None:
            self._cell.text = re.sub(r"\s+", " ", "".join(self._buf)).strip()
            self.rows[-1].append(self._cell)
            self._cell = None

    def handle_data(self, data):
        if self._cell is None:
            return
        (self._sup if self._sup is not None else self._buf).append(data)


@dataclass
class Grid:
    cells: list[list[Cell | None]]   # grid[r][c] -> originating Cell (shared across its span)
    header_rows: int

    @property
    def width(self) -> int:
        return max((len(r) for r in self.cells), default=0)

    def header_path(self, c: int) -> list[str]:
        """Header texts above column c, top to bottom; blanks skipped, repeats collapsed."""
        path: list[str] = []
        for r in range(self.header_rows):
            cell = self.cells[r][c] if c < len(self.cells[r]) else None
            if cell and cell.text and (not path or path[-1] != cell.text):
                path.append(cell.text)
        return path

    def body(self) -> list[list[Cell | None]]:
        return self.cells[self.header_rows:]


def parse_rows(html: str) -> list[list[Cell]]:
    p = _TableParser()
    p.feed(html)
    return p.rows


def build_grid(html: str, header_rows: int | None = None) -> Grid:
    """Expand spans into a rectangular grid and drop rows that are entirely empty.

    Header depth defaults to the largest rowspan in the first row. Table 504.3 has
    no <th> at all (its headers are bold <td>), so <th> can't be relied on.
    """
    rows = parse_rows(html)
    occupied: dict[tuple[int, int], Cell] = {}
    for r, row in enumerate(rows):
        c = 0
        for cell in row:
            while (r, c) in occupied:      # skip slots filled by a rowspan from above
                c += 1
            cell.col = c
            for dr in range(cell.rowspan):
                for dc in range(cell.colspan):
                    occupied[(r + dr, c + dc)] = cell
            c += cell.colspan
    width = max((c for _, c in occupied), default=-1) + 1
    grid: list[list[Cell | None]] = [[occupied.get((r, c)) for c in range(width)] for r in range(len(rows))]

    if header_rows is None:
        header_rows = max((cell.rowspan for cell in rows[0]), default=1) if rows else 0
    # Drop all-empty body rows (e.g. a colspan="14" separator that would become a phantom window).
    head, body = grid[:header_rows], grid[header_rows:]
    body = [r for r in body if any(cell and cell.text for cell in r)]
    w = max((len(r) for r in head + body), default=0)
    for r in head + body:
        r.extend([None] * (w - len(r)))
    return Grid(head + body, header_rows)
