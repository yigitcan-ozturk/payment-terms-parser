import unittest

from main import format_percent, parse_payment_terms


class PaymentTermsParserTests(unittest.TestCase):
    def test_net_terms_are_normalized_as_low_risk(self):
        result = parse_payment_terms("Net 45 days")

        self.assertEqual(result["type"], "net_terms")
        self.assertEqual(result["net_days"], 45)
        self.assertEqual(result["buyer_exposure"], 0)
        self.assertEqual(result["risk"], "LOW")

    def test_advance_and_before_shipment_create_high_exposure(self):
        result = parse_payment_terms("30% advance, 70% before shipment")

        self.assertEqual(result["advance_percent"], 30)
        self.assertEqual(result["before_shipment_percent"], 70)
        self.assertEqual(result["buyer_exposure"], 100)
        self.assertEqual(result["risk"], "HIGH")

    def test_after_delivery_amount_is_not_counted_as_pre_delivery_exposure(self):
        result = parse_payment_terms("20% advance, 80% after delivery")

        self.assertEqual(result["advance_percent"], 20)
        self.assertEqual(result["after_delivery_percent"], 80)
        self.assertEqual(result["buyer_exposure"], 20)
        self.assertEqual(result["risk"], "MEDIUM")

    def test_with_po_is_treated_as_advance_payment(self):
        result = parse_payment_terms("50% with PO")

        self.assertEqual(result["advance_percent"], 50)
        self.assertEqual(result["buyer_exposure"], 50)
        self.assertEqual(result["risk"], "MEDIUM")

    def test_before_shipment_only_can_be_high_risk(self):
        result = parse_payment_terms("100% before shipment")

        self.assertEqual(result["before_shipment_percent"], 100)
        self.assertEqual(result["buyer_exposure"], 100)
        self.assertEqual(result["risk"], "HIGH")

    def test_format_percent_removes_unnecessary_decimal(self):
        self.assertEqual(format_percent(30.0), "30%")
        self.assertEqual(format_percent(12.5), "12.5%")


if __name__ == "__main__":
    unittest.main()
