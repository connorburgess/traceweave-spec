"""Prove the checker rejects wrong arithmetic, not just that fixtures self-agree."""
import json
import unittest
from pathlib import Path
from unittest.mock import patch

import arithmetic
import build_fixtures
import check


class CheckerTests(unittest.TestCase):
    def test_oracle_regeneration_is_byte_identical(self):
        want = Path(__file__).with_name('fixtures.json').read_bytes()
        actual = (json.dumps(build_fixtures.make(),indent=2)+'\n').encode()
        self.assertEqual(want,actual)

    def test_wrong_pass_order_fails_checker(self):
        self.reject('wrong-order')

    def test_final_only_rounding_fails_checker(self):
        self.reject('final-only')

    def reject(self, mutation):
        original = arithmetic.resize
        def broken(a, ignored=None):
            return original(a,mutation)
        with patch.object(arithmetic,'resize',broken):
            report = check.check()
        self.assertFalse(report['ok'])
        self.assertTrue(any(c['ordinaryDifferentBytes'] for c in report['cases']))


if __name__=='__main__':
    unittest.main()
