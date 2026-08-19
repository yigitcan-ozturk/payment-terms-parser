# payment-terms-parser

A lightweight Python CLI for parsing supplier payment terms into structured commercial-risk signals.

[![Tests](https://github.com/yigitcan-ozturk/payment-terms-parser/actions/workflows/tests.yml/badge.svg)](https://github.com/yigitcan-ozturk/payment-terms-parser/actions/workflows/tests.yml)

## Why payment-terms-parser

Supplier payment terms are often written as free text: `Net 45`, `30% advance, 70% before shipment`, or similar variations. That makes it harder to compare commercial exposure consistently across quotations.

`payment-terms-parser` converts common payment-term phrases into a small structured result with pre-delivery buyer exposure and a simple risk classification.

The goal is not to replace commercial judgment. It is to make payment-term comparison faster, more consistent and easier to review.

## Features

- Parse common supplier payment terms
- Detect advance payments
- Detect payments before shipment
- Detect payments after delivery
- Parse Net payment terms
- Calculate buyer pre-delivery exposure
- Assign a LOW / MEDIUM / HIGH risk level
- Run with Python only — no third-party runtime dependencies

## Quick start

### Requirements

- Python 3.11+

### Run

```bash
python main.py "30% advance, 70% before shipment"
```

Example output:

```text
PAYMENT TERMS PARSER v0.1
----------------------------------------------
Original terms     : 30% advance, 70% before shipment
Advance payment    : 30%
Before shipment    : 70%
After delivery     : 0%
Buyer exposure     : 100% before delivery
Risk level         : HIGH
```

Net terms are also normalized:

```bash
python main.py "Net 45 days"
```

```text
PAYMENT TERMS PARSER v0.1
----------------------------------------------
Original terms     : Net 45 days
Standardized       : Net 45 days
Buyer prepayment   : 0%
Risk level         : LOW
```

## Risk model

The current model uses buyer exposure before delivery:

| Pre-delivery exposure | Risk |
| ---: | --- |
| 0%–19.99% | LOW |
| 20%–79.99% | MEDIUM |
| 80%+ | HIGH |

The model is intentionally simple and visible in the code so the result can be reviewed instead of treated as a black box.

## Tests

Run the test suite locally with:

```bash
python -m unittest discover -s tests -v
```

GitHub Actions runs the same suite automatically on supported Python versions.

## Procurement tooling suite

`payment-terms-parser` is part of a small set of transparent Python tools for supplier and procurement decision support:

| Tool | Role |
| --- | --- |
| [`rfqdiff`](https://github.com/yigitcan-ozturk/rfqdiff) | Compare and score supplier quotations |
| [`currency-normalizer`](https://github.com/yigitcan-ozturk/currency-normalizer) | Normalize quotation values across currencies |
| **[`payment-terms-parser`](https://github.com/yigitcan-ozturk/payment-terms-parser)** | Convert payment terms into commercial-risk signals |
| [`vendor-risk-engine`](https://github.com/yigitcan-ozturk/vendor-risk-engine) | Score operational, commercial, compliance and dependency risk |

A typical decision flow is:

```text
currency-normalizer -> payment-terms-parser -> rfqdiff -> vendor-risk-engine
```

Each tool can run independently. The suite roadmap is to combine their outputs into a composite supplier scorecard.

## Roadmap

- Broader phrase and synonym coverage
- Split-payment validation
- Configurable risk thresholds
- Structured JSON output
- Integration with `rfqdiff`
- Composite supplier scorecard integration

## Status

Early-stage project, currently at **v0.1**. The parser supports common payment-term patterns and a transparent pre-delivery exposure model.

## License

MIT License. See [`LICENSE`](LICENSE).
