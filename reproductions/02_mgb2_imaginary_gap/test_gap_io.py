"""Original synthetic tests: no author reference points are manufactured."""
import unittest
import numpy as np
try:
    import gap_io as io
except ModuleNotFoundError as exc:
    if exc.name != 'gap_io':
        raise
    io = None


TEXT = '''# Synthetic formatting fixture, NOT MgB2 results
0.002707 0.000 1.5 0.006 1.4
0.002707 -0.050 1.3 -0.002 1.2
0.008122 0.010 1.4 0.004 1.3
'''


class GapTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(io, 'gap_io feature is not implemented yet')

    def test_eV_conversion_all_three_energy_columns(self):
        r = io.parse_legacy_five(TEXT, energy_unit='eV')
        np.testing.assert_allclose(r.frequency_meV, [2.707, 2.707, 8.122])
        np.testing.assert_allclose(r.xi_meV, [0, -50, 10])
        np.testing.assert_allclose(r.gap_meV, [6, -2, 4])
        np.testing.assert_allclose(r.Z, [1.5, 1.3, 1.4])
        np.testing.assert_allclose(r.Z_normal, [1.4, 1.2, 1.3])

    def test_explicit_meV_no_rescale(self):
        r = io.parse_legacy_five('2.7 10 1.5 -2 1.4', energy_unit='meV')
        self.assertEqual(r.gap_meV.tolist(), [-2])

    def test_unknown_unit_rejected(self):
        with self.assertRaisesRegex(ValueError, 'unit'):
            io.parse_legacy_five(TEXT, energy_unit='guess')

    def test_unit_cannot_be_omitted(self):
        with self.assertRaises(TypeError):
            io.parse_legacy_five(TEXT)

    def test_fortran_exponents_comments_blanks(self):
        r = io.parse_legacy_five('\n! header\n2.7D-3 0 1.5 6d-3 1.4 # row\n', energy_unit='eV')
        self.assertAlmostEqual(r.frequency_meV[0], 2.7)

    def test_two_columns_not_inferred(self):
        with self.assertRaisesRegex(ValueError, 'line 1.*5 columns'):
            io.parse_legacy_five('2.7 6.0', energy_unit='meV')

    def test_extra_columns_not_silently_discarded(self):
        with self.assertRaisesRegex(ValueError, '5 columns'):
            io.parse_legacy_five('2.7 0 1.5 6 1.4 99', energy_unit='meV')

    def test_non_numeric_line_reports_location(self):
        with self.assertRaisesRegex(ValueError, 'line 2'):
            io.parse_legacy_five('# h\nword 0 1.5 6 1.4', energy_unit='meV')

    def test_non_finite_all_columns(self):
        for col in range(5):
            for bad in ['nan', 'inf', '-inf']:
                cells = ['2.7', '0', '1.5', '6', '1.4']
                cells[col] = bad
                with self.subTest(col=col, bad=bad), self.assertRaisesRegex(ValueError, 'finite'):
                    io.parse_legacy_five(' '.join(cells), energy_unit='meV')

    def test_empty_rejected(self):
        with self.assertRaisesRegex(ValueError, 'no data'):
            io.parse_legacy_five('# no rows\n', energy_unit='eV')

    def test_zero_negative_frequency_rejected(self):
        for w in ['0', '-2.7']:
            with self.subTest(w=w), self.assertRaisesRegex(ValueError, 'positive'):
                io.parse_legacy_five(f'{w} 0 1.5 6 1.4', energy_unit='meV')

    def test_rows_order_duplicates_and_negative_gaps_preserved(self):
        r = io.parse_legacy_five(TEXT+TEXT.splitlines()[1]+'\n', energy_unit='eV')
        self.assertEqual(r.gap_meV.tolist(), [6, -2, 4, 6])

    def test_window_inclusive_and_energy_filter_explicit(self):
        r = io.parse_legacy_five(TEXT, energy_unit='eV')
        s = io.window_report(r, max_frequency_meV=2.707, max_abs_xi_meV=50)
        self.assertEqual(s['retained_rows'], 2)
        self.assertEqual(s['gap_range_meV'], [-2, 6])
        self.assertFalse(s['has_band_labels'])
        self.assertFalse(s['has_DOS_weights'])
        self.assertFalse(s['is_paper_reproduction'])
        self.assertNotIn('weighted_mean', s)

    def test_empty_window_and_bad_bounds_rejected(self):
        r = io.parse_legacy_five(TEXT, energy_unit='eV')
        for v in [0, -1, float('nan'), float('inf'), 1]:
            with self.subTest(v=v), self.assertRaises(ValueError):
                io.window_report(r, max_frequency_meV=v)
        with self.assertRaises(ValueError):
            io.window_report(r, max_abs_xi_meV=-1)

    def test_matsubara_temperature_check_printing_tolerance(self):
        r = io.parse_legacy_five(TEXT, energy_unit='eV')
        self.assertLess(io.check_matsubara(r, 10), .001)

    def test_wrong_temperature_and_cyclic_frequency_fail(self):
        r = io.parse_legacy_five(TEXT, energy_unit='eV')
        with self.assertRaisesRegex(ValueError, 'Matsubara'):
            io.check_matsubara(r, 20)
        r2 = io.parse_legacy_five('2.7 0 1.5 6 1.4', energy_unit='meV')
        with self.assertRaisesRegex(ValueError, 'Matsubara'):
            io.check_matsubara(r2, 10)

    def test_bad_temperature_and_tolerance(self):
        r = io.parse_legacy_five(TEXT, energy_unit='eV')
        for v in [0, -1, float('nan'), float('inf')]:
            with self.subTest(T=v), self.assertRaises(ValueError):
                io.check_matsubara(r, v)
        with self.assertRaises(ValueError):
            io.check_matsubara(r, 10, atol_meV=-.1)

    def test_extreme_grid_arithmetic_cannot_return_nan(self):
        r = io.parse_legacy_five(TEXT, energy_unit='eV')
        with self.assertRaises(ValueError):
            io.check_matsubara(r, 5e-324)
        huge = io.parse_legacy_five('1e307 0 1.5 6 1.4', energy_unit='meV')
        with self.assertRaises(ValueError):
            io.check_matsubara(huge, 10)


if __name__ == '__main__':
    unittest.main()
