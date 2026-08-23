## 1. Citation scanning excludes code

- [x] 1.1 Add `mask_code` to `check.py`: blank fenced blocks and inline code spans, preserving line count and column offsets.
- [x] 1.2 Scan citations over the masked body instead of the raw one.
- [x] 1.3 Add `\\` to the citation regex lookbehind so `\@Override` is not a key.
- [x] 1.4 Name both escapes in the `citation-undefined` message.

## 2. Prose-pattern warnings become dismissible

- [x] 2.1 Add an `at()` helper returning `(line N)` for a match, and use it on the first-person, email, matriculation and confidentiality warnings.
- [x] 2.2 Quote the matched token in the matriculation warning.
- [x] 2.3 Blank `<Capitalised word> I` before the first-person scan so `Type I error` is not a pronoun.

## 3. Document shapes are named

- [x] 3.1 In `rule_metadata_present`, detect a leading `---` metadata block and report its position instead of only the missing trailing one.
- [x] 3.2 Add `rule_heading_style` and the `heading-style-setext` identifier; fire only when the body has no `#` heading, and skip `key:`-shaped lines so a metadata delimiter is not read as an underline.
- [x] 3.3 Register the rule before the section rules so the diagnosis precedes the findings it explains.

## 4. Skill prose

- [x] 4.1 `proposal-write`: third must-not-fix item — a demonstrable false positive is reported, markup may be corrected, content may not be deleted, troubleshoot is the route.
- [x] 4.2 `proposal-check`: the mandate states that a combined check-and-fix request is two steps; the digest re-run is the last step of the check, before any edit.
- [x] 4.3 Update the pinned mandate and mandate-successor copies, and pin the new write sentence.

## 5. Tests

- [x] 5.1 L0: code-span, fenced-block and `\@` cases plus the unmarked case that must still report.
- [x] 5.2 L0: `Type I error` silent, real pronoun located, matriculation token and line quoted.
- [x] 5.3 L0: leading metadata block named, setext headings named, prefixed headings and a metadata delimiter silent.
- [x] 5.4 L1: `check_report_compound` task, wired into `models.toml` `excluded` and `EXPECTED_SCORERS`.
- [x] 5.5 Sync the vendored `check.py` copies; confirm `poe test`, `poe cov` and `poe specs` are green and no fixture oracle moved.
