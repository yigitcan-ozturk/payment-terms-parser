import argparse
import re


def parse_payment_terms(text):
    text_lower = text.lower().strip()

    result = {
        "original": text,
        "type": "unknown",
        "advance_percent": 0,
        "before_shipment_percent": 0,
        "after_delivery_percent": 0,
        "net_days": None,
        "buyer_exposure": 0,
        "risk": "REVIEW",
    }

    # Example: Net 45 days
    net_match = re.search(r"net\s*(\d+)", text_lower)

    if net_match:
        days = int(net_match.group(1))

        result["type"] = "net_terms"
        result["net_days"] = days
        result["buyer_exposure"] = 0
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
    print("PAYMENT TERMS PARSER v0.1")
    print("-" * 46)

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

    print(f"Risk level         : {result['risk']}")


def main():
    parser = argparse.ArgumentParser(
        description="Parse and standardize supplier payment terms."
    )

    parser.add_argument(
        "terms",
        help="Supplier payment terms enclosed in quotes.",
    )

    args = parser.parse_args()

    result = parse_payment_terms(args.terms)

    print_report(result)


if __name__ == "__main__":
    main()