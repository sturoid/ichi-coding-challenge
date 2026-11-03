"""Table 504.3 cell lookups. Expected values read off instructions/fixtures/code/table-504.3.html
by hand (and the README's picture of the table), not from the parser.

The README cells (B/NS/II-B=55, I-4/NS/III-B=55) can't tell a wrong-row read apart because
every NS row repeats 55 in those columns; the R sub-rows and the merged I-1/H-1 cells can.
"""
import itertools
import unittest

from ichi.rules.height import Table504

from helpers import TABLE_HTML, permute_R_subrows, swap_tr_blocks

ROW_ABEFMSU = "A, B, E, F, M, S, U"
ROW_H1 = "H-1, H-2, H-3, H-5"
ROW_H4 = "H-4"
ROW_I1C1 = "I-1 Condition 1, I-3"
ROW_I1C2 = "I-1 Condition 2, I-2"
ROW_I4 = "I-4"
ROW_R = "R"

# (row label, sub-row, (major, minor), expected value, merged?)
CELLS = [
    # The fixture building and its neighbours in row R: the only row with 4 sub-rows.
    (ROW_R, "S13D", ("V", "B"), "40", False),
    (ROW_R, "S13R", ("V", "B"), "60", False),
    (ROW_R, "S", ("V", "B"), "60", False),
    (ROW_R, "NS", ("V", "B"), "40", False),
    (ROW_R, "S13D", ("V", "A"), "50", False),
    (ROW_R, "S13R", ("V", "A"), "60", False),
    (ROW_R, "S13D", ("I", "A"), "60", False),
    (ROW_R, "S", ("I", "A"), "UL", False),
    (ROW_R, "S13D", ("IV", "HT"), "60", False),
    (ROW_R, "S", ("IV", "HT"), "85", False),
    # I-1 Condition 2 / I-2: only I-A, I-B and II-A have separate S values; the rest are one
    # cell spanning both sub-rows (merged whichever sub-row you ask from).
    (ROW_I1C2, "S", ("II", "A"), "85", False),
    (ROW_I1C2, "NS", ("II", "A"), "65", False),
    (ROW_I1C2, "S", ("II", "B"), "55", True),
    (ROW_I1C2, "NS", ("II", "B"), "55", True),
    (ROW_I1C2, "S", ("V", "B"), "40", True),
    (ROW_I1C2, "S", ("I", "B"), "180", False),
    # H-1 group: the whole S sub-row is merged with NS.
    (ROW_H1, "S", ("II", "B"), "55", True),
    (ROW_H1, "S", ("I", "A"), "UL", True),
    (ROW_H1, "NS", ("II", "B"), "55", True),
    # H-4 has its own, unmerged S row (75, not 55): a wrong-row read of H-4 as H-1 shows here.
    (ROW_H4, "S", ("II", "B"), "75", False),
    (ROW_H4, "NS", ("II", "B"), "55", False),
    # README worked example and README question.
    (ROW_ABEFMSU, "NS", ("II", "B"), "55", False),
    (ROW_ABEFMSU, "S", ("II", "B"), "75", False),
    (ROW_ABEFMSU, "NS", ("I", "A"), "UL", False),
    (ROW_ABEFMSU, "S", ("I", "B"), "180", False),
    (ROW_I4, "NS", ("III", "B"), "55", False),
    (ROW_I4, "S", ("III", "B"), "75", False),
    (ROW_I1C1, "S", ("IV", "HT"), "85", False),
    (ROW_I1C1, "NS", ("V", "A"), "50", False),
]


class TestTable504Cells(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.table = Table504(TABLE_HTML)

    def test_discriminating_cells(self):
        for row, sub, col, expected, merged in CELLS:
            with self.subTest(row=row, sub=sub, col=col):
                hit = self.table.lookup(row, sub, col)
                self.assertIsNotNone(hit, f"no cell for {row}/{sub}/{col}")
                self.assertEqual(hit.value, expected)
                self.assertEqual(hit.merged, merged, "merged flag")

    def test_row_labels_are_as_printed(self):
        labels = self.table.row_labels()
        for want in (ROW_ABEFMSU, ROW_H1, ROW_H4, ROW_I1C1, ROW_I1C2, ROW_I4, ROW_R):
            self.assertIn(want, labels)
        # The footnote letter on R<sup>h</sup> must not leak into the label.
        self.assertNotIn("Rh", labels)
        self.assertNotIn("R h", labels)

    def test_r_row_has_four_subrows(self):
        for sub in ("NS", "S13D", "S13R", "S"):
            self.assertIsNotNone(self.table.lookup(ROW_R, sub, ("V", "B")), sub)
        # No other row has S13D/S13R.
        self.assertIsNone(self.table.lookup(ROW_ABEFMSU, "S13D", ("V", "B")))
        self.assertIsNone(self.table.lookup(ROW_I4, "S13R", ("V", "B")))

    def test_unknown_row_or_column_is_none(self):
        self.assertIsNone(self.table.lookup("R-3", "S13D", ("V", "B")))
        self.assertIsNone(self.table.lookup(ROW_R, "S13D", ("VI", "B")))
        self.assertIsNone(self.table.lookup(ROW_R, "S13D", ("V", "HT")))

    def test_subrow_footnotes_separate_from_label(self):
        hit = self.table.lookup(ROW_R, "NS", ("V", "B"))
        self.assertEqual(hit.subrow, "NS")
        self.assertIn("d", hit.subrow_footnotes)
        self.assertIn("h", hit.row_footnotes)
        hit = self.table.lookup(ROW_H1, "NS", ("V", "B"))
        self.assertEqual(sorted(x.strip() for x in hit.subrow_footnotes), ["c", "d"])


class TestTable504SubrowOrder(unittest.TestCase):
    """PLAN section 5: reordering 504.3 sub-rows must not change a lookup. The three
    sprinklered sub-rows of row R hold no rowspan label cell, so permuting them is a pure
    reordering of the same table."""

    def _check(self, html):
        t = Table504(html)
        self.assertEqual(t.lookup(ROW_R, "S13D", ("V", "B")).value, "40")
        self.assertEqual(t.lookup(ROW_R, "S13R", ("V", "B")).value, "60")
        self.assertEqual(t.lookup(ROW_R, "S", ("V", "B")).value, "60")
        self.assertEqual(t.lookup(ROW_R, "S13D", ("V", "A")).value, "50")
        self.assertEqual(t.lookup(ROW_R, "S", ("V", "A")).value, "70")
        self.assertEqual(t.lookup(ROW_R, "NS", ("V", "B")).value, "40")
        self.assertEqual(t.lookup(ROW_R, "S13R", ("I", "A")).value, "60")
        self.assertEqual(t.lookup(ROW_R, "S", ("I", "A")).value, "UL")

    def test_original_order_sanity(self):
        self.assertEqual(permute_R_subrows(TABLE_HTML, ("S13D", "S13R", "S")), TABLE_HTML)
        self._check(TABLE_HTML)

    def test_s13d_and_s13r_swapped(self):
        html = swap_tr_blocks(TABLE_HTML, ">S13D<", ">S13R<")
        self.assertNotEqual(html, TABLE_HTML)
        self._check(html)

    def test_every_permutation(self):
        for order in itertools.permutations(("S13D", "S13R", "S")):
            with self.subTest(order=order):
                self._check(permute_R_subrows(TABLE_HTML, order))


if __name__ == "__main__":
    unittest.main()
