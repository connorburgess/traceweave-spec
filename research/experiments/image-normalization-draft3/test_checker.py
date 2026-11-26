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

    def test_exact_grey_half_tie_and_reject_ties_even(self):
        # Integer derivation, independent of the oracle and Pillow.
        numerator = 19595*1 + 38470*53 + 7471*185
        self.assertEqual(numerator,3440640)
        self.assertEqual(divmod(numerator,65536),(52,32768))
        self.assertEqual(arithmetic.grey([[(1,53,185)]]),[[53]])
        def ties_even(rgb):
            out=[]
            for row in rgb:
                values=[]
                for r,g,b in row:
                    q,rem=divmod(19595*r+38470*g+7471*b,65536)
                    values.append(q+(rem>32768 or (rem==32768 and q%2==1)))
                out.append(values)
            return out
        self.assertEqual(ties_even([[(1,53,185)]]),[[52]])
        with patch.object(arithmetic,'grey',ties_even):
            report=check.check()
        self.assertFalse(report['ok'])
        half=next(c for c in report['cases'] if c['id']=='grey-half-tie')
        self.assertEqual(half['ordinaryDifferentBytes'],1024)

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
