## 1. Structured data

- [x] 1.1 Rename the SLR branch's second subsection in `shared/structure.json` to "Quality Assessment and Extracted Information" / "Qualitätsbewertung und extrahierte Informationen".

## 2. Guidance prose

- [x] 2.1 Update the canonical subsection table in `shared/guidelines/guidelines.md` to the new title (drift test requires verbatim match).
- [x] 2.2 Rewrite the SLR content contract: quality assessment coverage and use, extraction depth, Synthesis declares meta-analysis or narrative, review type declared with mapping-style omission stated in the quality-assessment subsection, PICOC recommended for framing the question and deriving search terms.
- [x] 2.3 Extend the Prototype contract's Evaluation bullet: name the empirical form (benchmark, controlled experiment, case study, simulation) and compare against alternatives or state why impractical, with the clause that naming the form is not a second methodology.
- [x] 2.4 Add the method-fit opening rule to the Methodology Content section: every methodology section opens with one or two sentences on why this methodology answers these research questions.
- [x] 2.5 Add the secondary-data advisory block beside the human-participants one: provenance, license or terms, personal data in the dataset, redistribution of derived data.

## 3. Fixtures

- [x] 3.1 Retitle the subsection heading in `tests/fixtures/f05-slr-interviews` and `tests/fixtures/f13-pure-slr`; their verdicts stay unchanged.
- [x] 3.2 Leave `tests/fixtures/f09-llm-compliance-docs` on the old heading and extend its `expected.json` with the `methodology-subsection-missing` error naming the new subsection title.
- [x] 3.3 Re-run the check script against all three fixtures and confirm each `expected.json` matches its actual output.

## 4. Sync and verify

- [x] 4.1 Run `python3 scripts/sync_shared.py`.
- [x] 4.2 `uv run poe test` green.
- [x] 4.3 `openspec validate --all --strict` green.
