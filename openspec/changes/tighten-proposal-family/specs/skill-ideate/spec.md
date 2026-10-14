## ADDED Requirements

### Requirement: Provisional handle resolved at seeding
The notes file created as soon as a topic phrase exists SHALL be named by a provisional slug derived from that phrase. A session resumed from `ideation.notes.md` SHALL rename that file to the provisional slug's notes file as soon as a topic phrase exists, and SHALL NOT create a second notes file.

At seeding, the slug SHALL be derived from the working title the user settled, in the shape proposal-file-format's "Content-derived slug filenames" requires: lowercase, hyphenated, 2–4 words of the title. The skill SHALL state that shape where it creates the seed. When it differs from the provisional slug, the skill SHALL rename the whole family under the provisional slug to it, as proposal-file-format's "A rename moves the whole family" requires. The family includes the notes file, kept files and figures. When any target name under the derived slug is taken, the slug SHALL take the numeric suffix, and the whole family SHALL move to the suffixed slug. The skill SHALL say in chat which files it renamed. After seeding, no file under the provisional slug SHALL remain. A title that changes after seeding SHALL NOT change the slug.

#### Scenario: Diverged slug at seeding
- **WHEN** the notes file is `<provisional>.notes.md`, a sketch `img/<provisional>-sketch.png` and a kept reading list `<provisional>.reading-list.md` exist, and the settled working title yields a different slug
- **THEN** after seeding the seed, the notes file, the sketch and the reading list carry the new slug, nothing remains under the provisional slug, and the chat names the renamed files

#### Scenario: Long working title at seeding
- **WHEN** the settled working title has more than four words
- **THEN** the seed's slug is lowercase and hyphenated and carries two to four of the title's words, never the whole title

#### Scenario: Slug unchanged at seeding
- **WHEN** the settled working title yields the provisional slug
- **THEN** no file is renamed and the seed is written beside the notes file

#### Scenario: Session resumed from slug-less notes
- **WHEN** a session resumes from `ideation.notes.md` and a topic phrase emerges
- **THEN** the notes file becomes `<provisional>.notes.md`, with its content kept, and no second notes file exists
