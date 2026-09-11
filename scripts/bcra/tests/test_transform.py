from __future__ import annotations

import unittest

from ..transform import is_extreme_change, pct_change


class TransformTests(unittest.TestCase):
    def test_pct_change_basic(self):
        self.assertAlmostEqual(pct_change(100, 110), 10.0)
        self.assertAlmostEqual(pct_change(100, 90), -10.0)

    def test_pct_change_zero_previous(self):
        self.assertIsNone(pct_change(0, 100))

    def test_not_enough_history_never_flags(self):
        flagged, reason = is_extreme_change([1, 2, 3], 1000)
        self.assertFalse(flagged)
        self.assertIsNone(reason)

    def test_stable_series_no_flag(self):
        history = [100 + i for i in range(30)]  # +1 por día, muy estable
        flagged, _ = is_extreme_change(history, history[-1] + 1)
        self.assertFalse(flagged)

    def test_sudden_jump_flagged(self):
        history = [100 + i for i in range(30)]  # variación diaria constante ~1
        flagged, reason = is_extreme_change(history, history[-1] + 5000)
        self.assertTrue(flagged)
        self.assertIsNotNone(reason)


if __name__ == "__main__":
    unittest.main()
