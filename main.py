import argparse
import json
import re
from pathlib import Path


VERSION = "0.2"


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
        "buyer_exposure": 0,
        "commercial_risk": 0,
        "risk": "REVIEW",
    }

    if supplier is not None:
        supplier = str(supplier).strip()
        if not supplier:
            raise ValueError("supplier name cannot be empty.")
        result["supplier"] = supplier

    net_match = re.search(r"net\s*(\d+)", text_lower)

    if net_match:
        days = int(net_match.group(1))

        result["type"] = "net_terms"
        result["net_days"] = days
        result["buyer_exposure"] = 0
        result["commercial_risk"] = 0
        result["risk"] = "LOW"

        return result

    percentages = re.findall(r"(\d+(?:\.\d+)?)\s*%", text_lower)
    percentages = [float(value) for value in percentages]

    if "advance" in text_lower or "with po" in text_lower:
        if percentages:
            result["advance_percent"] = percentages[0]

    if "before shipment" in text_lower:
        result["type"] = "pre_shipment"

        if len(percentages) >= 2:
            result["before_shipment_percent"] = percentages[1]
        elif percentages:
            result["before_shipment_percent"] = percentages[0]

    if "after delivery" in text_lower:
        result["type"] = "post_delivery"

        if len(percentages) >= 2:
            result["after_delivery_percent"] = percentages[1]

    pre_delivery_exposure = (
        result["advance_percent"]
        + result["before_shipment_percent"]
    )

    result["buyer_exposure"] = pre_delivery_exposure
    result["commercial_risk"] = pre_delivery_exposure

    if pre_delivery_exposure >= 80:
        result["risk"] = "HIGH"
    elif pre_delivery_exposure >= 20:
        result["risk"] = "MEDIUM"
    else:
        result["risk"] = "LOW"

    return result


def format_percent(value):
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
