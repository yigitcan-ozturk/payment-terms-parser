# payment-terms-parser

**Structured commercial-risk signals from supplier payment terms.**

[![Tests](https://github.com/yigitcan-ozturk/payment-terms-parser/actions/workflows/tests.yml/badge.svg)](https://github.com/yigitcan-ozturk/payment-terms-parser/actions/workflows/tests.yml)

`payment-terms-parser` converts free-text supplier payment terms into explicit buyer-exposure and commercial-risk signals that can be reviewed independently and consumed by `supplier-scorecard`.

## Why payment-terms-parser

Supplier payment terms are often written as free text: `Net 45`, `30% advance, 70% before shipment`, or similar variations. That makes buyer exposure difficult to compare consistently.

This tool keeps the commercial interpretation separate from quotation scoring, supplier-risk scoring and technical compliance. It turns supported payment phrases into a structured contract rather than hiding that logic inside a composite recommendation.

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

`payment-terms-parser` owns the commercial payment-exposure signal. Engineering compliance remains independently owned by `bidlint`.

```text
currency-normalizer ──> rfqdiff ────────────────┐
                                                 │
payment-terms-parser ───────────────────────────┼──> supplier-scorecard
                                                 │
vendor-risk-engine ─────────────────────────────┤
                                                 │
bidlint ──> technical compliance ───────────────┘
```

`supplier-scorecard` reads `commercial_risk` directly from this JSON output and validates the supplier name when one is supplied.

## Tests

```bash
python -m unittest discover -s tests -v
```

GitHub Actions runs the same suite automatically on supported Python versions.

## Engineering procurement toolchain

| Tool | Role |
| --- | --- |
| [`currency-normalizer`](https://github.com/yigitcan-ozturk/currency-normalizer) | Normalize quotation currencies with explicit FX provenance |
| [`rfqdiff`](https://github.com/yigitcan-ozturk/rfqdiff) | Compare and score normalized quotations |
| **[`payment-terms-parser`](https://github.com/yigitcan-ozturk/payment-terms-parser)** | Convert payment terms into commercial-risk signals |
| [`vendor-risk-engine`](https://github.com/yigitcan-ozturk/vendor-risk-engine) | Score delivery, quality, commercial, compliance and dependency risk |
| [`bidlint`](https://github.com/yigitcan-ozturk/bidlint) | Produce evidence-backed technical-compliance findings |
| [`supplier-scorecard`](https://github.com/yigitcan-ozturk/supplier-scorecard) | Combine commercial, risk and technical signals into an explainable supplier decision |

## Roadmap

- Broader phrase and synonym coverage
- Split-payment validation
- Configurable risk thresholds
- Structured batch input
- Supplier payment-term history

## Status

Early-stage project, currently at **v0.2**. This version provides a stable commercial-risk JSON contract and supplier identity metadata for direct integration with `supplier-scorecard`.

## License

MIT License. See [`LICENSE`](LICENSE).
