"""Check parser and conservative finite-reference convergence rules."""
import unittest
from collect_results import parse_scf, summarize


SAMPLE = """
Program PWSCF v.7.5 starts on 3Oct2026
! total energy = -39.50303902 Ry
the Fermi energy is 7.8174 ev
estimated scf accuracy < 1.5E-11 Ry
convergence has been achieved in 5 iterations
total stress (Ry/bohr**3) P= -0.20
JOB DONE.
"""


class ScanChecks(unittest.TestCase):
    def test_parse_complete_scf(self):
        r = parse_scf(SAMPLE)
        self.assertEqual(r["iterations"], 5)
        self.assertAlmostEqual(r["energy_Ry"], -39.50303902)
        self.assertAlmostEqual(r["fermi_eV"], 7.8174)
        self.assertAlmostEqual(r["pressure_kbar"], -0.20)

    def test_fail_closed_for_incomplete_or_unconverged_logs(self):
        for text in [SAMPLE.replace("JOB DONE.", ""), SAMPLE.replace("convergence has been achieved", "no convergence")]:
            with self.assertRaises(ValueError):
                parse_scf(text)

    def test_finite_reference_and_all_higher_cases(self):
        rows = [{"ecutwfc_Ry": e, "energy_Ry": energy, "fermi_eV": 7.8,
                 "pressure_kbar": 0.0, "iterations": 5}
                for e, energy in [(30, -1.0), (40, -1.00009), (50, -1.00020), (80, -1.00021)]]
        result = summarize(rows, 1.0)
        self.assertEqual(result["reference_ecutwfc_Ry"], 80)
        self.assertEqual(result["lowest_tested_acceptable_Ry"], 50)
        self.assertAlmostEqual(result["rows"][0]["abs_difference_meV_per_atom"], 2.857195555829,
                               places=7)

    def test_unsorted_or_duplicate_scan_rejected(self):
        row = {"ecutwfc_Ry": 40, "energy_Ry": -1.0}
        with self.assertRaises(ValueError):
            summarize([row, row], 1.0)


if __name__ == "__main__":
    unittest.main()
