## Why

The default methodology set grew from four branches to seven on the strength of a literature survey, but nothing in the product records where any branch comes from. A student or supervisor asking "why these seven, and why these subsections?" should get a citation, not a shrug — that question is exactly how the external fork that prompted the survey came about. `structure.json` holds only the mechanically checkable skeleton, so provenance is prose; the answer is split between a one-line citation per branch where the contracts live and a full sources page where the argument lives.

## What Changes

- Each shipped branch's content contract in `guidelines.md` gains one closing provenance sentence naming its primary source (e.g. Runeson & Höst 2009 for Case Study, Kitchenham & Charters 2007 for the SLR protocol). One line each, because `guidelines.md` is loaded into agent context on every run and students do not need bibliographies there.
- New `docs/methodology-sources.md`: per branch, the taxonomy or standard it derives from, the source of its subsection contract, and what was deliberately compressed away; plus the survey-level argument for the set as a whole (the expressiveness check against Stol & Fitzgerald's framework, the "most students need this" bar, and why Design Science Research, Mixed Methods, Grounded Theory, and Simulation are not defaults).
- The README's docs links gain the new page.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `guidance-model`: an added requirement that every default methodology branch records its provenance — a citation in the content contract and a maintained sources document.

## Impact

- `shared/guidelines/guidelines.md` and generated copies; `docs/methodology-sources.md` (new); `README.md` (one link).
- No structured-data, fixture, or script changes.
