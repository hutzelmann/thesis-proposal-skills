"""L0: lit-search shared helpers — offline, no network."""

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "skills" / "proposal-lit-search" / "scripts"))

import common  # noqa: E402


def make(title, doi=None, source="a", **kw):
    return common.entry(title=title, source=source, doi=doi, **kw)


def test_clean_doi_strips_url_form():
    assert common.clean_doi("https://doi.org/10.1145/AbC") == "10.1145/abc"
    assert common.clean_doi(None) is None


def test_entry_url_only_without_doi():
    with_doi = common.entry(title="T", source="s", doi="10.1/x", url="http://u")
    without = common.entry(title="T", source="s", url="http://u")
    assert "URL" not in with_doi and with_doi["DOI"] == "10.1/x"
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
    items = [make("A: Colon Title", doi="10.1/x", authors=[{"family": "Doe", "given": "J."}], year=2025)]
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
    (tmp_path / "api-keys.env").write_text("# keys\nOPENALEX_API_KEY = from-file\nCONTACT_EMAIL=a@b.c\n")
    monkeypatch.delenv("OPENALEX_API_KEY", raising=False)
    assert common.get_key("OPENALEX_API_KEY") == "from-file"
    monkeypatch.setenv("OPENALEX_API_KEY", "from-env")
    assert common.get_key("OPENALEX_API_KEY") == "from-env"
    assert common.get_key("MISSING_KEY") is None


def test_get_key_found_from_workspace_subdirectory(tmp_path, monkeypatch):
    """Running a script from a subdirectory must still see the workspace key file."""
    (tmp_path / "api-keys.env").write_text("OPENALEX_API_KEY=from-workspace-root\n")
    deep = tmp_path / "skills" / "proposal-lit-search" / "scripts"
    deep.mkdir(parents=True)
    monkeypatch.chdir(deep)
    monkeypatch.delenv(common.KEY_FILE_ENV, raising=False)
    monkeypatch.delenv("OPENALEX_API_KEY", raising=False)
    assert common.get_key("OPENALEX_API_KEY") == "from-workspace-root"


def test_get_key_explicit_path_overrides_and_resolves_per_key(tmp_path, monkeypatch):
    override = tmp_path / "elsewhere" / "keys.env"
    override.parent.mkdir()
    override.write_text("OPENALEX_API_KEY=from-override\n")
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "api-keys.env").write_text("OPENALEX_API_KEY=from-workspace\nCONTACT_EMAIL=a@b.c\n")
    monkeypatch.chdir(workspace)
    monkeypatch.setenv(common.KEY_FILE_ENV, str(override))
    monkeypatch.delenv("OPENALEX_API_KEY", raising=False)
    monkeypatch.delenv("CONTACT_EMAIL", raising=False)
    assert common.get_key("OPENALEX_API_KEY") == "from-override"
    # the override has no CONTACT_EMAIL, so the next candidate supplies it
    assert common.get_key("CONTACT_EMAIL") == "a@b.c"
