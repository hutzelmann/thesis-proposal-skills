## REMOVED Requirements

### Requirement: Reproducible demo content
**Reason**: The demo is no longer a derived artifact. With the screenshots gone, the README text is the demo itself, so there is nothing to regenerate and no render command to document.
**Migration**: None needed. `docs/demo/replay.py` and `docs/demo/transcript.jsonl` are deleted; edit the demo directly in `README.md`.

### Requirement: Authentic, synthetic demo content
**Reason**: The rule survives the change but belongs to the capability that owns the README demo.
**Migration**: Carried over verbatim in scope as "Authentic, synthetic demo content" under `user-onboarding`, with the harvested session output still committed as the audit trail.

### Requirement: Agent-neutral presentation
**Reason**: The requirement guarded against imitating a branded agent interface in rendered terminal screenshots. Plain quoted text attributed to skill names has no interface chrome to imitate.
**Migration**: None needed.

### Requirement: Small plainly-committed images
**Reason**: No images remain in the demo.
**Migration**: None needed. The three PNGs are deleted from the repository.
