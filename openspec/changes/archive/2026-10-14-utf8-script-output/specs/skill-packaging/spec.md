## ADDED Requirements

### Requirement: Script output encoding

Every user-side script with a command-line entry point, whether shipped inside a skill or the repository installer, SHALL write its standard output and standard error as UTF-8, whatever encoding the platform gives a pipe or console. The switch SHALL happen before the script writes anything. The installer is the one exception to that ordering: it makes the switch directly after its interpreter-version check, which stays its first statement. Switching SHALL keep each stream's existing error handler, so a diagnostic that was escaped before is still escaped and never raises. It SHALL NOT change line-ending translation or buffering. A stream that cannot be reconfigured, such as an in-memory buffer a caller substituted or an absent stream, SHALL be left exactly as it is. Messages a script captures as text from a program it starts SHALL be decoded as UTF-8, never in the platform's default encoding, and a byte that is not UTF-8 SHALL NOT abort the script. Files a script reads or writes keep their own explicit UTF-8 encoding; this requirement concerns only the two output streams and captured program messages.

#### Scenario: Output outside the pipe's code page

- **WHEN** a script runs with its output streams in a single-byte code page such as cp1252, as a Windows pipe gives them, and its output contains a character outside that code page, such as an author name with `Ł` or `ő`
- **THEN** the script writes that character as UTF-8 and exits with the code its documentation gives for that run, not with an encoding error

#### Scenario: Error handler and line endings preserved

- **WHEN** a script switches a stream whose error handler is not the default, such as `backslashreplace` (standard error) or `surrogateescape` (standard output under a POSIX C locale), or whose line endings are translated
- **THEN** the stream is UTF-8 afterwards and keeps that error handler and that line-ending translation

#### Scenario: Stream without reconfiguration

- **WHEN** a script's entry point is called with an output stream that cannot be reconfigured, such as an in-memory text buffer, or with no stream at all
- **THEN** the script runs as before and writes to that stream unchanged

#### Scenario: Captured program messages outside the code page

- **WHEN** a script captures the messages of a program it starts, such as the document converter or the typesetter, and they contain a UTF-8 character whose bytes the platform's code page cannot decode, such as `Ł`, or a byte that is not UTF-8 at all
- **THEN** the script decodes them without an error, whether the program succeeded or failed, and a failure report quotes the character intact

#### Scenario: Entry point without the switch

- **WHEN** a user-side script's entry point does not make the switch first (for the installer: directly after its version check), a script family's switch differs from the others, or a user-side script captures a program's messages as text without naming their encoding
- **THEN** the offline test suite fails and names the script
