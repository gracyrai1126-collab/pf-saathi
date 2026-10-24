"""
PF Saathi pure-logic regression tests.
Run from the project folder:
    python -m unittest -v test_pf_saathi.py

This test file extracts only pure helper functions from app.py, so Streamlit
does not launch during tests. It does not contact EPFO or use real account data.
"""
import ast
import re
import unittest
from pathlib import Path

import pandas as pd


APP_PATH = Path(__file__).with_name("app.py")
TREE = ast.parse(APP_PATH.read_text(encoding="utf-8"))

FUNCTIONS_TO_LOAD = {"get_demo_data", "analyze_ledger", "generate_query", "detect_scam"}
selected = [
    node for node in TREE.body
    if isinstance(node, ast.FunctionDef) and node.name in FUNCTIONS_TO_LOAD
]
missing = FUNCTIONS_TO_LOAD - {node.name for node in selected}
if missing:
    raise RuntimeError(f"Expected helper functions missing from app.py: {sorted(missing)}")

namespace = {"pd": pd, "re": re}
exec(compile(ast.Module(body=selected, type_ignores=[]), str(APP_PATH), "exec"), namespace)

get_demo_data = namespace["get_demo_data"]
analyze_ledger = namespace["analyze_ledger"]
generate_query = namespace["generate_query"]
detect_scam = namespace["detect_scam"]


class TestPFSaathi(unittest.TestCase):
    def setUp(self):
        self.demo = get_demo_data()
        self.analysed = analyze_ledger(self.demo)

    def test_01_demo_dataset_has_eight_months(self):
        self.assertEqual(len(self.demo), 8)

    def test_02_demo_data_has_required_columns(self):
        for col in ["Month", "Employer", "Expected_PF", "Posted_PF", "Posting_Status"]:
            self.assertIn(col, self.demo.columns)

    def test_03_demo_data_is_synthetic_company_labels(self):
        self.assertTrue(self.demo["Employer"].str.startswith("Company ").all())

    def test_04_difference_is_expected_minus_posted(self):
        row = self.analysed[self.analysed["Month"] == "2026-08"].iloc[0]
        self.assertEqual(row["Difference"], 500)

    def test_05_equal_month_is_classified_as_match(self):
        row = self.analysed[self.analysed["Month"] == "2026-01"].iloc[0]
        self.assertEqual(row["Classification"], "Amounts match")
        self.assertEqual(row["Confidence"], "High")

    def test_06_zero_posted_marked_potential_missing_when_status_says_not_found(self):
        row = self.analysed[self.analysed["Month"] == "2026-03"].iloc[0]
        self.assertEqual(row["Classification"], "Potential missing contribution")
        self.assertEqual(row["Confidence"], "Medium")

    def test_07_partial_difference_classified_cautiously(self):
        row = self.analysed[self.analysed["Month"] == "2026-08"].iloc[0]
        self.assertEqual(row["Classification"], "Amount difference")
        self.assertEqual(row["Confidence"], "Medium")

    def test_08_analysis_does_not_mutate_input(self):
        self.assertNotIn("Difference", self.demo.columns)

    def test_09_every_analysed_row_has_explanation(self):
        self.assertTrue(self.analysed["Explanation"].notna().all())
        self.assertTrue((self.analysed["Explanation"].str.len() > 10).all())

    def test_10_explanation_does_not_accuse_employer(self):
        text = " ".join(self.analysed["Explanation"].astype(str)).lower()
        self.assertNotIn("violated the law", text)
        self.assertNotIn("guilty", text)

    def test_11_query_contains_month_and_amounts(self):
        row = self.analysed[self.analysed["Month"] == "2026-08"].iloc[0]
        draft = generate_query(row)
        self.assertIn("2026-08", draft)
        self.assertIn("2,000.00", draft)
        self.assertIn("1,500.00", draft)

    def test_12_query_is_neutral(self):
        row = self.analysed[self.analysed["Month"] == "2026-08"].iloc[0]
        draft = generate_query(row).lower()
        self.assertIn("please help me verify", draft)
        self.assertNotIn("you stole", draft)
        self.assertNotIn("fraud", draft)

    def test_13_otp_message_is_high_risk(self):
        level, reason, advice, redacted = detect_scam(
            "Your PF claim will speed up. Share your OTP immediately."
        )
        self.assertEqual(level, "HIGH RISK")
        self.assertTrue(reason)
        self.assertIn("Never share", advice)

    def test_14_password_message_is_high_risk(self):
        self.assertEqual(detect_scam("Send your password now")[0], "HIGH RISK")

    def test_15_urgency_without_credential_is_caution(self):
        self.assertEqual(
            detect_scam("URGENT: your claim will be blocked unless you act immediately")[0],
            "CAUTION",
        )

    def test_16_benign_portal_reminder_is_not_claimed_safe(self):
        level, reason, advice, _ = detect_scam(
            "Please check your claim status on the official portal."
        )
        self.assertEqual(level, "NO WARNING TRIGGERED")
        self.assertIn("not proof", advice.lower())

    def test_17_digit_sequence_redacted_in_preview(self):
        _, _, _, preview = detect_scam("Test message with OTP 123456")
        self.assertNotIn("123456", preview)
        self.assertIn("[REDACTED NUMBER]", preview)

    def test_18_detector_returns_four_values(self):
        self.assertEqual(len(detect_scam("sample message")), 4)

    def test_19_no_database_or_file_write_in_detector_source(self):
        source = ast.get_source_segment(APP_PATH.read_text(encoding="utf-8"), next(
            node for node in TREE.body
            if isinstance(node, ast.FunctionDef) and node.name == "detect_scam"
        ))
        self.assertNotIn("open(", source)
        self.assertNotIn("to_csv(", source)
        self.assertNotIn("to_sql(", source)

    def test_20_ledger_totals_reconcile_with_visible_demo(self):
        self.assertEqual(int(self.demo["Expected_PF"].sum()), 15000)
        self.assertEqual(int(self.demo["Posted_PF"].sum()), 12700)
        self.assertEqual(
            int(self.demo["Expected_PF"].sum() - self.demo["Posted_PF"].sum()),
            2300,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
