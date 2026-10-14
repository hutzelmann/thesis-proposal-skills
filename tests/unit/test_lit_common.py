"""L0: lit-search shared helpers — offline, no network."""

from pathlib import Path

import common

REPO = Path(__file__).resolve().parents[2]


def make(title, doi=None, source="a", **kw):
    return common.entry(title=title, source=source, doi=doi, **kw)


def test_clean_doi_strips_url_form():
    assert common.clean_doi("https://doi.org/10.1145/AbC") == "10.1145/abc"
    assert common.clean_doi(None) is None


def test_entry_url_only_without_doi():
    with_doi = common.entry(title="T", source="s", doi="10.1/x", url="http://u")
    without = common.entry(title="T", source="s", url="http://u")
    assert "URL" not in with_doi
    assert with_doi["DOI"] == "10.1/x"
    assert without["URL"] == "http://u"


def test_dedupe_by_doi_merges_fields():
    a = make("Same Paper", doi="10.1/x")
    b = make("Same paper!", doi="10.1/x", source="b", abstract="An abstract.")
    merged = common.dedupe([a, b])
    assert len(merged) == 1
    assert merged[0]["abstract"] == "An abstract."
    assert merged[0]["_source"] == "a,b"


def test_dedupe_by_normalized_title():
    a = make("Deep Learning for Tests")
    b = make("Deep  learning for tests", source="b")
    assert len(common.dedupe([a, b])) == 1


def test_make_key_shape():
    item = {
        "author": [{"family": "Müller-Lüdenscheidt", "given": "A."}],
        "issued": {"year": 2026},
        "title": "The Deep Analysis of Things",
    }
    key = common.make_key(item)
    assert key.startswith("MllerLdens26Deep")
    assert len(key) < 20


def test_csl_yaml_roundtrip_via_check_regex():
    items = [
        make("A: Colon Title", doi="10.1/x",
             authors=[{"family": "Doe", "given": "J."}], year=2025)
    ]
    items[0]["id"] = common.make_key(items[0])
    yaml = common.to_csl_yaml(items)
    assert '- id: Doe25Colon' in yaml
    assert 'title: "A: Colon Title"' in yaml
    assert "DOI: 10.1/x" in yaml


def test_dedupe_keeps_distinct_bare_doi_items():
    items = [{"DOI": f"10.1/x{i}", "_source": "opencitations"} for i in range(3)]
    assert len(common.dedupe(items)) == 3


def test_get_key_env_then_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv(common.KEY_FILE_ENV, raising=False)
    (tmp_path / "api-keys.env").write_text(
        "# keys\nOPENALEX_API_KEY = from-file\nCONTACT_EMAIL=a@b.c\n"
    )
    monkeypatch.delenv("OPENALEX_API_KEY", raising=False)
    assert common.get_key("OPENALEX_API_KEY") == "from-file"
    monkeypatch.setenv("OPENALEX_API_KEY", "from-env")
    assert common.get_key("OPENALEX_API_KEY") == "from-env"
    assert common.get_key("MISSING_KEY") is None


def test_get_key_never_reads_ancestor_directories(tmp_path, monkeypatch):
    """No directory traversal: a key file above the working directory is not consulted."""
    (tmp_path / "api-keys.env").write_text("OPENALEX_API_KEY=from-ancestor\n", encoding="utf-8")
    deep = tmp_path / "sub" / "dir"
    deep.mkdir(parents=True)
    monkeypatch.chdir(deep)
    monkeypatch.delenv(common.KEY_FILE_ENV, raising=False)
    monkeypatch.delenv("OPENALEX_API_KEY", raising=False)
    assert common.get_key("OPENALEX_API_KEY") is None
    candidates = common.key_file_candidates()
    assert tmp_path / "api-keys.env" not in candidates
    assert deep / "api-keys.env" in candidates


def test_search_rejects_unknown_source(tmp_path):
    """Static registry: an unknown --sources name aborts before any work (no dynamic import)."""
    import subprocess
    import sys as _sys

    evil = tmp_path / "evilmodule.py"
    evil.write_text("raise SystemExit('must never be imported')\n")
    result = subprocess.run(
        [_sys.executable, str(REPO / "skills" / "proposal-lit-search" / "scripts" / "search.py"),
         "query", "--sources", "dblp,evilmodule"],
        capture_output=True, encoding="utf-8", cwd=tmp_path,
    )
    assert result.returncode == 2
    assert "unknown source" in result.stderr
    assert "evilmodule" in result.stderr
    assert "dblp" in result.stderr  # valid names are listed
    assert "must never be imported" not in result.stderr + result.stdout


def spy_reads(monkeypatch) -> list[Path]:
    """Record every file `Path.read_text` is asked to open during the test."""
    opened: list[Path] = []
    original = Path.read_text

    def recording(self, *args, **kwargs):
        opened.append(Path(self))
        return original(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", recording)
    return opened


def test_l0_never_opens_a_real_key_file(monkeypatch):
    """The developer's own key files stay out of L0 (`_lit_keys_offline` in
    conftest): neither the user-global file nor `api-keys.env` where pytest
    runs is opened by a key lookup, the user agent, or a keyless source."""
    import openalex
    import pytest

    real = {Path.home() / ".config" / "thesis-proposal" / common.KEY_FILE,
            Path.cwd() / common.KEY_FILE}
    assert common.GLOBAL_KEY_FILE not in real
    opened = spy_reads(monkeypatch)
    assert common.get_key("OPENALEX_API_KEY") is None
    assert "mailto:" not in common.user_agent()
    with pytest.raises(common.SourceError, match="no OPENALEX_API_KEY"):
        openalex.search("anything", 1)
    assert not real & set(opened), f"L0 opened a real key file: {sorted(real & set(opened))}"


def test_l0_key_reader_opens_nothing_outside_the_test_temp_root(monkeypatch):
    opened = spy_reads(monkeypatch)
    assert common._read_key(REPO / "pyproject.toml", "name") is None
    assert opened == []


def test_get_key_explicit_path_overrides_and_resolves_per_key(tmp_path, monkeypatch):
    override = tmp_path / "elsewhere" / "keys.env"
    override.parent.mkdir()
    override.write_text("OPENALEX_API_KEY=from-override\n", encoding="utf-8")
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "api-keys.env").write_text(
        "OPENALEX_API_KEY=from-workspace\nCONTACT_EMAIL=a@b.c\n"
    )
    monkeypatch.chdir(workspace)
    monkeypatch.setenv(common.KEY_FILE_ENV, str(override))
    monkeypatch.delenv("OPENALEX_API_KEY", raising=False)
    monkeypatch.delenv("CONTACT_EMAIL", raising=False)
    assert common.get_key("OPENALEX_API_KEY") == "from-override"
    # the override has no CONTACT_EMAIL, so the next candidate supplies it
    assert common.get_key("CONTACT_EMAIL") == "a@b.c"
