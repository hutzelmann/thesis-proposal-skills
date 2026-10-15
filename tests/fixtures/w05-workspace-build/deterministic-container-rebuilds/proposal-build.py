#!/usr/bin/env python3
"""Stand-in for a faculty build script — the fixture's whole point is that a
workspace supplies one, not what it produces.

A real one would run pandoc or typst against the program's own template. This
one writes a marker so a test can tell it apart from the shipped pipeline, and
prints the line publish would otherwise print about its own output.
"""

import os
import sys
from pathlib import Path

proposal = Path(sys.argv[1] if len(sys.argv) > 1 else os.environ["PROPOSAL_PATH"])
marker = proposal.with_name("workspace-build-ran.txt")
marker.write_text(f"built {proposal.name} with the workspace pipeline\n", encoding="utf-8")
print(f"built via the workspace build script: {marker.name}")
