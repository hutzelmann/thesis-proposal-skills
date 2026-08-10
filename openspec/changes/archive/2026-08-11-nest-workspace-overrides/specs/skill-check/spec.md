## ADDED Requirements

### Requirement: Retired override keys are reported, never ignored
The check SHALL report a workspace override key from the pre-migration vocabulary as a configuration error naming the key path that replaces it. A retired key SHALL NOT be honoured, and SHALL NOT be passed over in silence — a workspace whose overrides stopped applying without saying so is worse than one that fails.

The check SHALL apply the same treatment to any override key that is not part of the overridable set, because a typo in an override key is indistinguishable from a retired one from the user's side, and both mean the workspace is not getting what it asked for.

#### Scenario: Workspace uses a retired key
- **WHEN** a workspace `guidelines.md` sets the old flat reference-minimum key
- **THEN** the check reports an error naming the nested key path that replaces it, and the default minimum applies

#### Scenario: Workspace uses an unknown key
- **WHEN** a workspace `guidelines.md` sets a key that is not overridable
- **THEN** the check reports an error naming the unknown key
