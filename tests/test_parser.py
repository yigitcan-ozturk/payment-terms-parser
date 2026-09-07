import json
import tempfile
import unittest
from pathlib import Path

from main import format_percent, parse_payment_terms, write_json


class PaymentTermsParserTests(unittest.TestCase):
    def test_net_terms_are_normalized_as_low_risk(self):
        result = parse_payment_terms("Net 45 days")

        self.assertEqual(result["type"], "net_terms")
        self.assertEqual(result["net_days"], 45)
        self.assertEqual(result["buyer_exposure"], 0)
        self.assertEqual(result["commercial_risk"], 0)
        self.assertEqual(result["risk"], "LOW")
        self.assertTrue(result["supported"])
        self.assertFalse(result["review_required"])

    def test_advance_and_before_shipment_create_high_exposure(self):
        result = parse_payment_terms("30% advance, 70% before shipment")

        self.assertEqual(result["advance_percent"], 30)
        self.assertEqual(result["before_shipment_percent"], 70)
        self.assertEqual(result["buyer_exposure"], 100)
        self.assertEqual(result["commercial_risk"], 100)
        self.assertEqual(result["risk"], "HIGH")
        self.assertFalse(result["review_required"])

    def test_after_delivery_amount_is_not_counted_as_pre_delivery_exposure(self):
        result = parse_payment_terms("20% advance, 80% after delivery")

        self.assertEqual(result["advance_percent"], 20)
        self.assertEqual(result["after_delivery_percent"], 80)
        self.assertEqual(result["buyer_exposure"], 20)
        self.assertEqual(result["risk"], "MEDIUM")

    def test_reversed_component_order_keeps_percentages_attached_to_phrases(self):
        result = parse_payment_terms("70% before shipment, 30% advance")

        self.assertEqual(result["advance_percent"], 30)
        self.assertEqual(result["before_shipment_percent"], 70)
        self.assertEqual(result["buyer_exposure"], 100)
        self.assertEqual(result["risk"], "HIGH")

    def test_incomplete_with_po_split_requires_review(self):
        result = parse_payment_terms("50% with PO")

        self.assertIsNone(result["buyer_exposure"])
        self.assertIsNone(result["commercial_risk"])
        self.assertEqual(result["risk"], "REVIEW")
        self.assertTrue(result["review_required"])
        self.assertEqual(result["review_reason"], "payment_split_does_not_total_100")

    def test_before_shipment_only_can_be_high_risk(self):
        result = parse_payment_terms("100% before shipment")

        self.assertEqual(result["before_shipment_percent"], 100)
        self.assertEqual(result["buyer_exposure"], 100)
        self.assertEqual(result["risk"], "HIGH")

    def test_unsupported_terms_do_not_become_false_low_risk(self):
        result = parse_payment_terms("Cash against documents")

        self.assertEqual(result["risk"], "REVIEW")
        self.assertIsNone(result["buyer_exposure"])
        self.assertIsNone(result["commercial_risk"])
        self.assertFalse(result["supported"])
        self.assertTrue(result["review_required"])

    def test_deposit_is_treated_as_advance_payment(self):
        result = parse_payment_terms("50% deposit, 50% before shipment")

        self.assertEqual(result["advance_percent"], 50)
        self.assertEqual(result["before_shipment_percent"], 50)
        self.assertEqual(result["buyer_exposure"], 100)
        self.assertEqual(result["risk"], "HIGH")

    def test_payment_on_placing_order_is_treated_as_advance(self):
        result = parse_payment_terms(
            "100% payment would need to be made on placing the order before the order is acknowledged"
        )

        self.assertEqual(result["advance_percent"], 100)
        self.assertEqual(result["buyer_exposure"], 100)
        self.assertEqual(result["risk"], "HIGH")
        self.assertFalse(result["review_required"])

    def test_proforma_alone_remains_review_required(self):
        result = parse_payment_terms("Payment terms would be proforma")

        self.assertEqual(result["risk"], "REVIEW")
        self.assertEqual(result["review_reason"], "unsupported_or_ambiguous_terms")
        self.assertIsNone(result["commercial_risk"])

    def test_mixed_upfront_and_net_eom_terms_fail_closed_until_modeled(self):
        result = parse_payment_terms(
            "50% paid with order on a proforma, upfront payment. "
            "Then the 50% balance will be due within net 30 day, end of month account "
            "from invoice date."
        )

        self.assertEqual(result["advance_percent"], 50)
        self.assertEqual(result["risk"], "REVIEW")
        self.assertEqual(result["review_reason"], "unclassified_percentage_component")
        self.assertIsNone(result["commercial_risk"])

    def test_proforma_then_payment_before_processing_remains_review_required(self):
        result = parse_payment_terms(
            "Once your order is confirmed, we will prepare a proforma invoice. "
            "Your order will be processed after you make the payment."
        )

        self.assertEqual(result["risk"], "REVIEW")
        self.assertEqual(result["review_reason"], "unsupported_or_ambiguous_terms")
        self.assertIsNone(result["commercial_risk"])

    def test_down_payment_without_percentage_remains_review_required(self):
        result = parse_payment_terms(
            "Lead times are after purchase order, down-payment, and approval of drawings."
        )

        self.assertEqual(result["risk"], "REVIEW")
        self.assertEqual(result["review_reason"], "unsupported_or_ambiguous_terms")
        self.assertIsNone(result["commercial_risk"])

    def test_split_over_100_requires_review(self):
        result = parse_payment_terms("60% advance, 60% before shipment")

        self.assertEqual(result["risk"], "REVIEW")
        self.assertEqual(result["review_reason"], "payment_split_does_not_total_100")

    def test_full_post_delivery_is_low_risk(self):
        result = parse_payment_terms("100% after delivery")

        self.assertEqual(result["after_delivery_percent"], 100)
        self.assertEqual(result["buyer_exposure"], 0)
        self.assertEqual(result["commercial_risk"], 0)
        self.assertEqual(result["risk"], "LOW")

    def test_format_percent_removes_unnecessary_decimal(self):
        self.assertEqual(format_percent(30.0), "30%")
        self.assertEqual(format_percent(12.5), "12.5%")
        self.assertEqual(format_percent(None), "N/A")

    def test_supplier_is_embedded_for_pipeline_matching(self):
        result = parse_payment_terms(
            "Net 30",
            supplier="Supplier A",
        )

        self.assertEqual(result["supplier"], "Supplier A")
        self.assertEqual(result["tool"], "payment-terms-parser")
        self.assertEqual(result["version"], "0.4")

    def test_empty_supplier_is_rejected(self):
        with self.assertRaises(ValueError):
            parse_payment_terms("Net 30", supplier="   ")

    def test_write_json_round_trip(self):
        result = parse_payment_terms(
            "30% advance, 70% before shipment",
            supplier="Supplier A",
        )

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "payment.json"
            write_json(result, path)
            reloaded = json.loads(path.read_text(encoding="utf-8"))

        self.assertEqual(reloaded["supplier"], "Supplier A")
        self.assertEqual(reloaded["commercial_risk"], 100)

    def test_review_state_round_trips_as_null_risk(self):
        result = parse_payment_terms(
            "Cash against documents",
            supplier="Supplier A",
        )

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "payment.json"
            write_json(result, path)
            reloaded = json.loads(path.read_text(encoding="utf-8"))

        self.assertTrue(reloaded["review_required"])
        self.assertIsNone(reloaded["commercial_risk"])


if __name__ == "__main__":
    unittest.main()
