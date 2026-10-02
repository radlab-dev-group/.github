---
title: "PII Masker"
subtitle: "Multi-tier PII anonymization and privacy protection engine for AI pipelines"
slug: "pii-masker"
description: "PII Masker is an advanced data privacy engine combining deterministic checksum validation (FastMasker) and machine learning NER token classification (anonymizer-model). It reliably detects and masks sensitive personal data before prompts reach external language models."
icon: "shield"
status: "Open Source · Apache-2.0"
version: "v1.1"
tags: ["PII Masking", "Data Privacy", "NER Model", "FastMasker", "GDPR / Privacy", "LLM Security"]
actions:
  - {label: "Online Tester (masker.apps)", href: "https://masker.apps.radlab.dev/anonymize/", style: primary}
  - {label: "GitHub: anonymizer-model", href: "https://github.com/radlab-dev-group/anonymizer-model", style: quiet}
  - {label: "GitHub: fast_masker plugin", href: "https://github.com/radlab-dev-group/llm-router-plugins/tree/main/llm_router_plugins/maskers/fast_masker", style: quiet}
---

## Why PII Protection is Critical in AI Workflows

Sending user queries, enterprise documents, and customer tickets to public cloud LLMs creates significant risks of **data leakage, confidentiality breaches, and GDPR/compliance violations**.

Traditional regex solutions struggle with high false-positive rates or miss non-standard formatting, while pure deep-learning models often fail to strictly validate digital identifiers that follow formal checksum algorithms.

**PII Masker** addresses both challenges through a **hybrid two-tier architecture**: it couples high-certainty deterministic checksum rules with specialized Named Entity Recognition (NER) models for unstructured Polish and multilingual text.

---

## Two-Tier Hybrid Architecture

<div class="product-flow">
  <div class="product-flow-endpoint">Raw text with sensitive information</div>
  <ol class="product-flow-steps">
    <li>
      <h3>1. FastMasker</h3>
      <p>Deterministic rules and checksum validation: PESEL, NIP, REGON, IBAN, credit cards and VIN. Format rules: email, IPv4/IPv6, URLs, phone numbers and postcodes.</p>
    </li>
    <li>
      <h3>2. Anonymizer Model</h3>
      <p>Transformer NER token classification: personal names, organizations and roles, as well as addresses, locations and contextual entities.</p>
    </li>
  </ol>
  <div class="product-flow-endpoint">Anonymized text with structured placeholders, e.g. <code>{{PESEL}}</code>, <code>{{CREDIT_CARD}}</code></div>
</div>

---

## Core Components

### 1. FastMasker: Ultra-Fast Rule Engine

The `fast_masker` plugin applies validation rules in strict precedence order — from **highest certainty (checksum-verified identifiers)** down to generalized patterns:

* **Checksum-Validated Identifiers:**
  * **Credit Cards (`CreditCardRule`):** Luhn algorithm checksum verification (13–19 digits) → `{{CREDIT_CARD}}`
  * **Vehicle Identification Numbers (`VinRule`):** ISO 3779 checksum (position 9) → `{{VIN}}`
  * **Polish PESEL (`PeselTaggedRule`, `PeselRule`):** Formal checksum calculation and birthdate sanity check → `{{PESEL}}`
  * **Polish Tax (NIP) & Business (REGON) IDs:** Weighted checksum validators → `{{NIP}}`, `{{REGON}}`
  * **Bank Accounts (`IbanRule`, `NrbRule`):** Polish NRB (26 digits) and international IBAN (modulo 97) → `{{IBAN}}`
  * **Identity Documents:** Polish National ID (`IdCardNumberRule`) and Passport numbers (`PassportNumberRule`) → `{{ID_CARD}}`, `{{PASSPORT}}`
  * **System Credentials:** MAC addresses, SIM ICCIDs, SSL serials, and JWT tokens → `{{MAC_ADDRESS}}`, `{{JWT}}`
* **Pattern-Based Identifiers:**
  * Email addresses → `{{EMAIL}}`
  * IPv4 and IPv6 addresses → `{{IP_ADDRESS}}`
  * URLs and domains → `{{URL}}`
  * Polish and international telephone numbers → `{{PHONE}}`
  * Postal codes, license plates, monetary amounts, and dates

### 2. Anonymizer Model: ML NER for Polish Text

For unstructured entities without deterministic checksums (first and last names, street names, organization roles), we provide the **`anonymizer-model`**:

* **Architecture:** RoBERTa-based `AutoModelForTokenClassification` tuned specifically for Polish syntax.
* **Trained on Curated Datasets:** Built on annotated corpora such as `clarin-pl/kpwr-ner` with generalized entity taxonomies.
* **Advanced Post-Processing:** Sub-token boundary stitching, punctuation preservation, and exact entity boundary alignment.
* **Low-Resource Deployment:** Dynamic quantization (ONNX / INT8) enables fast CPU inference without requiring dedicated GPUs.

---

## LLM Router Integration

PII Masker integrates seamlessly into **LLM Router**:

1. **Pre-Inference:** Replaces all confidential identifiers in the prompt with structured placeholders.
2. **Inference:** Cloud or local models generate responses based on sanitized data.
3. **Post-Inference (Optional):** Restores original entities into the response before delivering text back to the authorized user.

---

## Python Quickstart

```python
from llm_router_plugins.maskers.fast_masker import FastMasker, ALL_RULES

# Initialize the masker with all built-in rules
masker = FastMasker(rules=ALL_RULES)

text = (
    "Customer John Doe, PESEL: 44051401359, paid the invoice using card "
    "4532 1234 5678 9010 for 1,250.00 USD. "
    "Contact: john.doe@company.com or +48 601 234 567."
)

masked_text = masker.mask(text)
print(masked_text)
# Output:
# Customer John Doe, {{PESEL_TAGGED}}, paid the invoice using card
# {{CREDIT_CARD}} for {{MONEY}}.
# Contact: {{EMAIL}} or {{PHONE}}.
```

---

## Resources & Repositories

* **Online Tester:** [masker.apps.radlab.dev/anonymize/](https://masker.apps.radlab.dev/anonymize/)
* **NER Model Repository:** [radlab-dev-group/anonymizer-model](https://github.com/radlab-dev-group/anonymizer-model)
* **Rule Engine Plugin:** [radlab-dev-group/llm-router-plugins](https://github.com/radlab-dev-group/llm-router-plugins)
* **License:** Apache 2.0 (Open Source)
