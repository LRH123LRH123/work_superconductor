from pathlib import Path
import importlib.util
import unittest

FILE = Path(__file__).parent/"cluster/pb_regression/validate_epw.py"
module = None
if FILE.exists():
    spec = importlib.util.spec_from_file_location("epw_status", FILE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)


class EPWStatusChecks(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(module, "EPW-specific completion checker is missing")

    def test_normal_epw_footer_does_not_require_pw_marker(self):
        log = "Program EPW v.6.0\n lambda : 0.1608797\nTotal program execution\n EPW : 1s WALL\n"
        self.assertEqual(module.check_log(log), 0.1608797)
        self.assertNotIn("JOB DONE", log)

    def test_truncation_errors_and_nonfinite_values_are_rejected(self):
        base = "Program EPW\nTotal program execution\nlambda : 0.1\n"
        for log in ["Program EPW\n lambda : 0.1", base.replace("0.1", "NaN"),
                    base+"Error in routine readin", base+"Infinity"]:
            with self.assertRaises(ValueError):
                module.check_log(log)

    def test_spectrum_is_checked_not_just_file_presence(self):
        self.assertEqual(module.check_table("1 0 0\n2 0.2 0.3\n"), 2)
        for table in ["", "1 NaN\n2 1\n", "2 .1\n1 .2\n", "1 .1\n2 -.2\n", "1 .1\n2 .2 .3\n"]:
            with self.assertRaises(ValueError):
                module.check_table(table)

    def test_real_legacy_footer_is_explicitly_validated(self):
        text = ("# test\n1 0.1 0.2\n2 0.2 0.3\n Integrated el-ph coupling\n"
                " # 0.3 0.4\n Phonon smearing (meV)\n # 0.05 0.1\n"
                " Electron smearing (eV) 0.1\n Fermi window (eV) 6\n"
                " Summed el-ph coupling 0.3\n")
        self.assertEqual(module.check_table(text, file_format="epw_legacy"), 2)
        for broken in [text.replace("Summed el-ph coupling", "unknown footer"),
                       text.replace("# 0.3 0.4", "# NaN 0.4"),
                       text.replace("# 0.05 0.1", "# 0.05"), text+"3 .1 .2\n"]:
            with self.assertRaises(ValueError):
                module.check_table(broken, file_format="epw_legacy")
        with self.assertRaises(ValueError):
            module.check_table(text)


if __name__ == "__main__":
    unittest.main()
