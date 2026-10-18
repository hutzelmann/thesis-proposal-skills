# Design

## Context

Python caches bytecode for imported modules only. The program file itself is never cached. So the scripts at risk are the ones a SKILL.md runs that import a module from their own folder:

| Script | Sibling imports | Source |
|---|---|---|
| `proposal-lit-search/scripts/search.py` | `arxiv`, `common`, `crossref`, `dblp`, `openalex`, `semantic_scholar` | own |
| `proposal-lit-search/scripts/snowball.py` | `common`, `crossref`, `openalex`, `opencitations`, `semantic_scholar` | own |
| `proposal-import/scripts/validate_refs.py` | `common`, `crossref` | own |
| `proposal-reverse/scripts/validate_refs.py` | same | generated from import's |

The library modules (`common`, `crossref`, `arxiv`, …) also import `common`, but none of them has a `__main__` block or is run by a SKILL.md. `check.py`, `collect.py` and `publish.py` import only the standard library. No shipped script loads modules through `importlib`, `runpy` or a child interpreter.

Two other facts shape the approach. Shipped modules are imported in-process by the test suite (`tests/conftest.py`, `test_lit_search_cli.py`, `test_validate_refs.py`) and by the harness (`harness/lit_live.py`, `harness/l1_checks.py`). And the open change `host-neutral-script-paths` is rewriting the SKILL.md command paragraphs that invoke these scripts.

## Goals / Non-Goals

**Goals:**
- A documented script run leaves the install directory byte-identical, interpreter caches included.
- The guard checks the property itself (no cache appears), however a script achieves it.

**Non-Goals:**
- Undocumented invocations, such as an agent running `python -c "import search"` inside the install directory. Those are outside the contract.
- Removing caches that earlier releases left behind. The next install does that (see Decision 3).
- Changing where the dev runner or the harness ignore `__pycache__` in the developer's checkout. Those exclusions read the working tree, where the test suite's caches legitimately live.

## Decisions

### 1. Switch the cache off in the entry script, only when it is the program

Each of the three entry scripts gets this before its first sibling import:

```python
if __name__ == "__main__":
    sys.dont_write_bytecode = True
```

Python reads the flag on every import, so one setting at the top of the entry script covers its siblings and everything they import in turn.

Alternatives considered:
- **Unconditional `sys.dont_write_bytecode = True` at module top.** The flag belongs to the whole interpreter. `test_lit_search_cli.py` imports `search`, so an unconditional switch would turn off bytecode caching, pytest's assertion-rewrite cache included, for every module the test session imported after it, and the same would happen to the harness. Ruff 0.16 also reports E402 on the imports after a module-level assignment, but not after an `if` block, and this repository carries no `noqa` and no per-file ignores.
- **Switch it in every module that imports a sibling, library modules included.** A library module is only ever imported. Under an entry script the flag is already set, and anywhere else setting it is a side effect on whoever imported the module.
- **`python3 -B` or `PYTHONDONTWRITEBYTECODE` in the documented commands.** This depends on every agent copying the flag. It does not survive the prose fallback for hosts that do not substitute the skill directory, and it would edit the command paragraphs the `host-neutral-script-paths` change owns.
- **`sys.pycache_prefix`.** It moves the write rather than preventing it: the cache still lands somewhere on the user's machine, in a folder the script would have to choose for each platform.
- **Lazy imports inside `main()`.** The source registries (`SEARCH_SOURCES`, snowball's equivalents) and the tests read module-level names, so this is a larger restructure for the same effect.

The cost is negligible: each run recompiles `common.py` (≈26 KB) and a few small modules, a matter of milliseconds.

### 2. Behavioral guard, run from a copy

`tests/unit/test_script_bytecode.py` discovers every `skills/*/scripts/*.py` with a `__main__` block, so a new entry script is covered automatically. For each one it:

1. copies the script's skill folder into `tmp_path`;
2. runs `sys.executable <copy>/scripts/<name>.py --help` from a separate workspace directory, with `PYTHONDONTWRITEBYTECODE` and `PYTHONPYCACHEPREFIX` removed from the child's environment;
3. asserts exit code 0, which proves the module-level imports ran (every entry script uses `argparse`, and `--help` exits after the imports and before any file or network access);
4. asserts that no `__pycache__` entry exists anywhere in the copy, and on failure names the script and the cache files.

A companion test imports `search` from a copied scripts folder through `python -c` and asserts two things. The child prints `sys.dont_write_bytecode` as `False`, which is the "imported by another program" scenario. And a `__pycache__` folder does appear in that copy. That second assertion is the negative control: it proves the detection works under this interpreter and environment, so the main test cannot pass vacuously because some ambient setting suppressed caching.

Alternatives considered:
- **A static AST check** that the switch precedes the first sibling import. It would pin one spelling, it cannot see transitive imports, and it could pass while the property fails, for example with a switch placed under the wrong condition. The behavioral test measures exactly what the spec states.
- **In-process tests.** Bytecode writing is decided by a fresh interpreter's import of a module not yet imported, so a subprocess is the only faithful measurement. Coverage is not lost, because these scripts' logic is already exercised in-process by their own tests.

### 3. Collector and installer stay as they are

- **`proposal-troubleshoot/scripts/collect.py`** already skips `__pycache__` and `.git` when it hashes installed skill files (`SKIP_DIR_NAMES`), and `test_hashes_cover_scripts_and_references_not_only_instructions` pins that. The skip stays even though shipped scripts stop writing caches. Installs of 0.9.0 and earlier already hold caches, and the user's own interpreter or editor tooling can write one at any time. A hashed `.pyc` would match no revision, so `poe identify` would report a locally edited install that is not.
- **`install.py`** writes each skill into a fresh staging folder and swaps it in for the live one (`write_skill`), so an update or reinstall drops any cache the old folder held. Uninstalling removes the folder whole. When the source is a local directory, `read_directory` skips `__pycache__`, so a developer's caches are never installed. Nothing needs to change. The spec scenario "Cache already present in an installed skill folder" records this behavior, and a test pins the directory-source skip if none does already.

## Risks / Trade-offs

- [A future entry script does not use `argparse`, so `--help` is read as a positional argument] → The test asserts exit code 0, so it fails loudly and names the script instead of passing silently. The writer then picks an argument that exits after the imports.
- [A host runs a script as a module (`python -m`) or through a wrapper] → `__name__` is still `"__main__"` under `-m`. Wrappers that import the script are outside the documented commands.
- [Installs made before this change keep their caches until the next update] → They are harmless to running scripts, invisible to the collector's hashes, and dropped by the installer's folder swap.
