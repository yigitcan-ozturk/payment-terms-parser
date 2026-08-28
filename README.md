# payment-terms-parser

**Structured commercial-risk signals from supplier payment terms.**

[![Tests](https://github.com/yigitcan-ozturk/payment-terms-parser/actions/workflows/tests.yml/badge.svg)](https://github.com/yigitcan-ozturk/payment-terms-parser/actions/workflows/tests.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

`payment-terms-parser` converts free-text supplier payment terms into explicit buyer-exposure and commercial-risk signals that can be reviewed independently and consumed by `supplier-scorecard`.

## Why payment-terms-parser

Supplier payment terms are often written as free text: `Net 45`, `30% advance, 70% before shipment`, or similar variations. That makes buyer exposure difficult to compare consistently.

This tool keeps the commercial interpretation separate from quotation scoring, supplier-risk scoring and technical compliance. It turns supported payment phrases into a structured contract rather than hiding that logic inside a composite recommendation.

## Decision boundary

`payment-terms-parser` is responsible for **supported payment-term interpretation and buyer-exposure signaling**.

It does:

- parse supported supplier payment phrases;
- detect advance, pre-shipment and post-delivery payment components;
- parse supported Net terms;
- validate that percentage-based payment splits total 100%;
- calculate pre-delivery buyer exposure;
- expose a structured `commercial_risk` signal;
- explicitly flag unsupported or incomplete terms for human review;
- attach supplier identity for cross-tool matching.

It intentionally does **not**:

- interpret arbitrary contract language;
- provide legal, tax or accounting advice;
- infer unsupported payment semantics;
- compare supplier prices;
- determine technical compliance;
- approve contractual terms on behalf of a buyer.

Unsupported, ambiguous or incomplete commercial language remains a human review item rather than being forced into a false structured interpretation.

## Features

- Parse common supplier payment terms
- Detect advance payments
- Detect payments before shipment
- Detect payments after delivery
- Parse Net payment terms
- Validate percentage splits before scoring
- Calculate buyer pre-delivery exposure
- Expose `commercial_risk` on a 0–100 scale for supported terms
- Fail closed to `REVIEW` with null exposure/risk for unsupported or incomplete terms
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

Example supported contract:

```json
{
  "tool": "payment-terms-parser",
  "version": "0.3",
  "supplier": "Supplier A",
  "buyer_exposure": 100.0,
  "commercial_risk": 100.0,
  "risk": "HIGH",
  "supported": true,
  "review_required": false,
  "review_reason": null
}
```

Example review contract:

```json
{
  "tool": "payment-terms-parser",
  "version": "0.3",
  "supplier": "Supplier A",
  "buyer_exposure": null,
  "commercial_risk": null,
  "risk": "REVIEW",
  "supported": false,
  "review_required": true,
  "review_reason": "unsupported_or_ambiguous_terms"
}
```

The full payload also contains parsed payment components and normalized term metadata.

## Risk model

| Pre-delivery exposure | Risk |
| ---: | --- |
| 0%–19.99% | LOW |
| 20%–79.99% | MEDIUM |
| 80%+ | HIGH |
| Unsupported / incomplete | REVIEW |

For supported terms, `commercial_risk` equals buyer exposure before delivery. For review-required terms, `buyer_exposure` and `commercial_risk` are `null` so downstream tools cannot silently treat unknown commercial language as low risk.

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

[`supplier-scorecard`](https://github.com/yigitcan-ozturk/supplier-scorecard) reads `commercial_risk` from this JSON output and validates the supplier name when one is supplied. Consumers should stop automatic scoring when `review_required` is `true`.

## Quality gates

GitHub Actions runs the unit-test suite on Python 3.11, 3.12 and 3.13 for pushes to `main` and pull requests.

Local verification:

```bash
python -m unittest discover -s tests -v
```

## Engineering principles

- **Structured where supported** — only recognized payment semantics become automatic signals.
- **Explicit buyer exposure** — commercial risk is tied to observable pre-delivery payment exposure.
- **Fail closed on uncertainty** — unsupported or incomplete payment language cannot become a false low-risk score.
- **No invented contract meaning** — unsupported language stays outside automatic interpretation.
- **Separation of concerns** — payment exposure remains independent from quotation and technical scoring.
- **Review before authority** — the output informs commercial review; it does not accept terms.

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
- Configurable risk thresholds
- Structured batch input
- Supplier payment-term history
- Stronger cross-tool review-state enforcement

## Status

Early-stage project, currently at **v0.3**. This version hardens the commercial-risk contract by validating percentage splits and making unsupported or incomplete payment language explicitly review-required instead of silently low risk.

## License

MIT License. See [`LICENSE`](LICENSE).
