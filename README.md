# payment-terms-parser

A lightweight Python CLI for parsing supplier payment terms into structured commercial-risk signals.

[![Tests](https://github.com/yigitcan-ozturk/payment-terms-parser/actions/workflows/tests.yml/badge.svg)](https://github.com/yigitcan-ozturk/payment-terms-parser/actions/workflows/tests.yml)

## Why payment-terms-parser

Supplier payment terms are often written as free text: `Net 45`, `30% advance, 70% before shipment`, or similar variations. That makes buyer exposure difficult to compare consistently.

`payment-terms-parser` turns those phrases into a structured commercial-risk signal that can be consumed directly by `supplier-scorecard`.

## Features

- Parse common supplier payment terms
- Detect advance payments
- Detect payments before shipment
- Detect payments after delivery
- Parse Net payment terms
- Calculate buyer pre-delivery exposure
- Expose `commercial_risk` on a 0–100 scale
- Embed an optional supplier name for cross-tool matching
- Return/write structured JSON
- Run with Python only — no third-party runtime dependencies

## Quick start

### Requirements

- Python 3.11+

### Text output

```bash
python main.py "30% advance, 70% before shipment"
```

### Pipeline JSON

```bash
python main.py \
  "30% advance, 70% before shipment" \
  --supplier "Supplier A" \
  --json
```

Write the result to a file:

```bash
python main.py \
  "30% advance, 70% before shipment" \
  --supplier "Supplier A" \
  --output payment.json
```

Example contract:

```json
{
  "tool": "payment-terms-parser",
  "version": "0.2",
  "supplier": "Supplier A",
  "buyer_exposure": 100.0,
  "commercial_risk": 100.0,
  "risk": "HIGH"
}
```

The full payload also contains parsed payment components and normalized term metadata.

## Risk model

| Pre-delivery exposure | Risk |
| ---: | --- |
| 0%–19.99% | LOW |
| 20%–79.99% | MEDIUM |
| 80%+ | HIGH |

For the pipeline, `commercial_risk` equals buyer exposure before delivery.

## Pipeline role

```text
currency-normalizer ──> rfqdiff ───────────────┐
                                               │
payment-terms-parser ──────────────────────────┼─> supplier-scorecard
                                               │
vendor-risk-engine ────────────────────────────┘
```

`supplier-scorecard` reads `commercial_risk` directly from this JSON output and validates the supplier name when one is supplied.

## Tests

```bash
python -m unittest discover -s tests -v
```

GitHub Actions runs the same suite automatically on supported Python versions.

## Procurement tooling suite

| Tool | Role |
| --- | --- |
| [`currency-normalizer`](https://github.com/yigitcan-ozturk/currency-normalizer) | Normalize quotation values across currencies |
| [`rfqdiff`](https://github.com/yigitcan-ozturk/rfqdiff) | Compare and score normalized quotations |
| **[`payment-terms-parser`](https://github.com/yigitcan-ozturk/payment-terms-parser)** | Convert payment terms into commercial-risk signals |
| [`vendor-risk-engine`](https://github.com/yigitcan-ozturk/vendor-risk-engine) | Score operational, quality, compliance and dependency risk |
| [`supplier-scorecard`](https://github.com/yigitcan-ozturk/supplier-scorecard) | Combine upstream signals into one supplier recommendation |

## Roadmap

- Broader phrase and synonym coverage
- Split-payment validation
- Configurable risk thresholds
- Structured batch input
- Supplier payment-term history

## Status

Early-stage project, currently at **v0.2**. This version adds a stable commercial-risk JSON contract and supplier identity metadata for direct integration with `supplier-scorecard`.

## License

MIT License. See [`LICENSE`](LICENSE).
