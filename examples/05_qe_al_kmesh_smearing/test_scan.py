"""Tests first: parse QE logs and avoid mixing k and smearing error criteria."""
import unittest
from collect_results import parse_scf, summarize, validate_input

SAMPLE = """
Program PWSCF v.7.5 starts on 3Oct2026
number of Kohn-Sham states= 6
number of k points= 60 Marzari-Vanderbilt smearing, width (Ry)= 0.0200
! total energy = -39.50305990 Ry
the Fermi energy is 7.8173 ev
estimated scf accuracy < 2.3D-11 Ry
smearing contrib. (-TS) = 0.00004080 Ry
internal energy E=F+TS = -39.50310070 Ry
convergence has been achieved in 5 iterations
total stress (Ry/bohr**3) (kbar) P= -8.13
JOB DONE.
"""
THRESHOLDS = {"energy_meV_per_atom": 0.1, "pressure_kbar": 0.1, "fermi_eV": 0.005}


def rows():
    # Different sigma planes have different baselines; only same-sigma deltas count.
    return [{"id": f"{k}_{sigma}", "k_mesh": k, "degauss_Ry": sigma,
             "energy_Ry": base+diff, "internal_energy_Ry": base+diff,
             "pressure_kbar": -8, "fermi_eV": 7.8}
            for sigma, base in [(0.02, -39), (0.01, -40)]
            for k, diff in [(8, 0.001), (12, 0.000001), (16, 0.0)]]


class ScanChecks(unittest.TestCase):
    def test_parse_energy_definitions_and_units(self):
        r = parse_scf(SAMPLE)
        self.assertEqual(r["n_irreducible_k"], 60)
        self.assertEqual(r["nbnd"], 6)
        self.assertEqual(r["iterations"], 5)
        self.assertAlmostEqual(r["scf_accuracy_Ry"], 2.3e-11)
        self.assertAlmostEqual(r["internal_energy_Ry"], r["energy_Ry"]-r["minus_TS_Ry"])

    def test_fail_closed_on_incomplete_or_inconsistent_log(self):
        for s in [SAMPLE.replace("JOB DONE.", ""),
                  SAMPLE.replace("convergence has been achieved", "no convergence"),
                  SAMPLE.replace("-39.50310070", "-39.6")]:
            with self.assertRaises(ValueError):
                parse_scf(s)

    def test_compare_only_within_sigma_and_require_higher_points(self):
        report = summarize(rows(), THRESHOLDS)
        self.assertEqual([s["lowest_joint_acceptable_k"] for s in report["sigma_summaries"]], [12, 12])
        self.assertEqual(report["common_tested_k"], 12)
        self.assertLess(report["rows"][1]["abs_energy_difference_meV_per_atom"], 0.1)
        self.assertGreater(report["sigma_sensitivity_at_max_k"]["energy_span_meV_per_atom"], 10000)

    def test_pressure_can_fail_even_when_energy_passes(self):
        data = rows()
        for r in data:
            if r["k_mesh"] == 12:
                r["pressure_kbar"] = -7.5
        report = summarize(data, THRESHOLDS)
        self.assertTrue(all(s["lowest_joint_acceptable_k"] is None for s in report["sigma_summaries"]))
        self.assertIsNone(report["common_tested_k"])

    def test_nonmonotonic_higher_point_is_not_ignored(self):
        data = rows()
        for r in data:
            if r["k_mesh"] == 8:
                r["energy_Ry"] -= 0.001
            if r["k_mesh"] == 12:
                r["energy_Ry"] += 0.01
        self.assertIsNone(summarize(data, THRESHOLDS)["common_tested_k"])

    def test_missing_duplicate_nonfinite_and_bad_thresholds(self):
        for data in [rows()[:-1], rows()+[rows()[0]], [{**r, "energy_Ry": float("nan")} for r in rows()]]:
            with self.assertRaises(ValueError):
                summarize(data, THRESHOLDS)
        with self.assertRaises(ValueError):
            summarize(rows(), {**THRESHOLDS, "pressure_kbar": -1})

    def test_input_contract_rejects_changed_fixed_parameters(self):
        source = """calculation='scf', ibrav=2, celldm(1)=7.65339, nat=1, ntyp=1,
ecutwfc=60, ecutrho=640, nbnd=6, occupations='smearing', smearing='mv', degauss=0.02
conv_thr=1.0d-10, mixing_beta=0.5, prefix='al', outdir='./scratch'
Al 26.9815385 Al.pbe-n-kjpaw_psl.1.0.0.UPF
ATOMIC_POSITIONS crystal
Al 0 0 0
K_POINTS automatic
8 8 8 1 1 1
"""
        case = {"k_mesh": 8, "degauss_Ry": 0.02}
        validate_input(source, case)
        for bad in [source.replace("ecutrho=640", "ecutrho=320"),
                    source.replace("8 8 8 1 1 1", "8 8 8 0 0 0"),
                    source.replace("degauss=0.02", "degauss=0.01")]:
            with self.assertRaises(ValueError):
                validate_input(bad, case)

    def test_intermediate_band_warnings_recorded_but_final_ones_rejected(self):
        warning = "c_bands: 1 eigenvalues not converged\n"
        intermediate = SAMPLE.replace("! total energy", "iteration # 4\n"+warning+"iteration # 5\n! total energy")
        result = parse_scf(intermediate)
        self.assertEqual(result["band_warning_messages_total"], 1)
        self.assertEqual(result["band_warning_messages_final_iteration"], 0)
        final = SAMPLE.replace("! total energy", "iteration # 5\n"+warning+"! total energy")
        with self.assertRaises(ValueError):
            parse_scf(final)


if __name__ == "__main__":
    unittest.main()
