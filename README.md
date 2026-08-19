# payment-terms-parser

A lightweight CLI for parsing and standardizing supplier payment terms.

Built as a small procurement utility for identifying buyer prepayment exposure and commercial risk.

## Features

- Parse common supplier payment terms
- Detect advance payments
- Detect payments before shipment
- Detect payments after delivery
- Parse Net payment terms
- Calculate buyer pre-delivery exposure
- Assign a simple LOW / MEDIUM / HIGH risk level
- No third-party Python packages required

## Usage

```bash
python main.py "30% advance, 70% before shipment"