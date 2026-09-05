import argparse
import json
import re
from pathlib import Path


VERSION = "0.4"

_PERCENT = r"(\d+(?:\.\d+)?)"

_COMPONENT_PATTERNS = {
    "advance_percent": (
        rf"{_PERCENT}\s*%\s*(?:as\s+)?advance\b",
        rf"{_PERCENT}\s*%\s*with\s+(?:the\s+)?po\b",
    ),
    "before_shipment_percent": (
        rf"{_PERCENT}\s*%\s*before\s+shipment\b",
    ),
    "after_delivery_percent": (
        rf"{_PERCENT}\s*%\s*after\s+delivery\b",
    ),
}


def _review_result(result, reason):
    result["buyer_exposure"] = None
    result["commercial_risk"] = None
    result["risk"] = "REVIEW"
    result["supported"] = False
    result["review_required"] = True
    result["review_reason"] = reason
    return result


def _extract_components(text_lower):
    components = {}
    matched_values = []

    for field, patterns in _COMPONENT_PATTERNS.items():
        values = []
        for pattern in patterns:
            values.extend(float(value) for value in re.findall(pattern, text_lower))
        components[field] = sum(values)
        matched_values.extend(values)

    return components, matched_values


def parse_payment_terms(text, supplier=None):
    text = str(text)
    text_lower = text.lower().strip()

    result = {
        "tool": "payment-terms-parser",
        "version": VERSION,
        "original": text,
        "type": "unknown",
        "advance_percent": 0,
        "before_shipment_percent": 0,
        "after_delivery_percent": 0,
        "net_days": None,
        "buyer_exposure": None,
        "commercial_risk": None,
        "risk": "REVIEW",
        "supported": False,
        "review_required": True,
        "review_reason": "unsupported_or_ambiguous_terms",
    }

    if supplier is not None:
        supplier = str(supplier).strip()
        if not supplier:
            raise ValueError("supplier name cannot be empty.")
        result["supplier"] = supplier

    net_match = re.fullmatch(r"net\s*(\d+)(?:\s*days?)?", text_lower)

    if net_match:
        days = int(net_match.group(1))

        result["type"] = "net_terms"
        result["net_days"] = days
        result["buyer_exposure"] = 0
        result["commercial_risk"] = 0
        result["risk"] = "LOW"
        result["supported"] = True
        result["review_required"] = False
        result["review_reason"] = None

        return result

    percentages = [float(value) for value in re.findall(rf"{_PERCENT}\s*%", text_lower)]
    components, matched_values = _extract_components(text_lower)

    result.update(components)

    if not matched_values:
        return _review_result(result, "unsupported_or_ambiguous_terms")

    if len(percentages) != len(matched_values):
        return _review_result(result, "unclassified_percentage_component")

    total_percent = sum(percentages)
    if abs(total_percent - 100.0) > 1e-9:
        return _review_result(result, "payment_split_does_not_total_100")

    if result["advance_percent"] and result["before_shipment_percent"]:
        result["type"] = "split_pre_delivery"
    elif sum(value > 0 for value in components.values()) > 1:
        result["type"] = "split_payment"
    elif result["advance_percent"]:
        result["type"] = "advance"
    elif result["before_shipment_percent"]:
        result["type"] = "pre_shipment"
    elif result["after_delivery_percent"]:
        result["type"] = "post_delivery"

    pre_delivery_exposure = (
        result["advance_percent"]
        + result["before_shipment_percent"]
    )

    result["buyer_exposure"] = pre_delivery_exposure
    result["commercial_risk"] = pre_delivery_exposure
    result["supported"] = True
    result["review_required"] = False
    result["review_reason"] = None

    if pre_delivery_exposure >= 80:
        result["risk"] = "HIGH"
    elif pre_delivery_exposure >= 20:
        result["risk"] = "MEDIUM"
    else:
        result["risk"] = "LOW"

    return result


def format_percent(value):
    if value is None:
        return "N/A"

    if value == int(value):
        return f"{int(value)}%"

    return f"{value}%"


def print_report(result):
    print()
    print(f"PAYMENT TERMS PARSER v{VERSION}")
    print("-" * 46)

    if "supplier" in result:
        print(f"Supplier           : {result['supplier']}")

    print(f"Original terms     : {result['original']}")

    if result["net_days"] is not None:
        print(f"Standardized       : Net {result['net_days']} days")
        print("Buyer prepayment   : 0%")

    elif result["review_required"]:
        print("Standardized       : Human review required")
        print(f"Review reason      : {result['review_reason']}")

    else:
        print(
            f"Advance payment    : "
            f"{format_percent(result['advance_percent'])}"
        )

        print(
            f"Before shipment    : "
            f"{format_percent(result['before_shipment_percent'])}"
        )

        print(
            f"After delivery     : "
            f"{format_percent(result['after_delivery_percent'])}"
        )

        print(
            f"Buyer exposure     : "
            f"{format_percent(result['buyer_exposure'])} before delivery"
        )

    print(f"Commercial risk    : {format_percent(result['commercial_risk'])}")
    print(f"Risk level         : {result['risk']}")


def write_json(payload, path):
    Path(path).write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def build_parser():
    parser = argparse.ArgumentParser(
        description="Parse and standardize supplier payment terms."
    )

    parser.add_argument(
        "terms",
        help="Supplier payment terms enclosed in quotes.",
    )
    parser.add_argument(
        "--supplier",
        help="Optional supplier name embedded in the structured result.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Return structured JSON instead of the text report.",
    )
    parser.add_argument(
        "--output",
        help="Write the structured result to a JSON file.",
    )

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    try:
        result = parse_payment_terms(
            args.terms,
            supplier=args.supplier,
        )
    except ValueError as exc:
        parser.error(str(exc))

    if args.output:
        write_json(result, args.output)

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print_report(result)


if __name__ == "__main__":
    main()
