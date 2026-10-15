#!/bin/sh
# Build every fixture proposal on the typst tier and compile it.
#
# The pandoc/typst image carries pandoc and typst but no Python, so
# tests/unit/test_export_matrix.py cannot run there. This script therefore
# restates the typst tier's pandoc invocation — and that restatement is exactly
# the kind of copy that drifts, so tests/unit/test_ci_typst_drift.py asserts it
# passes every option, template, CSL, and filter publish.py's pandoc_command()
# does. Add an option there, add it here. (The staged path never holds the
# path-list separator, so publish.py's run-from-the-folder fallback has no
# counterpart here.)
#
# For the same reason it walks the corpus itself, the way the shared walker
# harness/fixture_paths.py does: every fixture that carries an expected.json
# oracle has one proposal, in a folder of its own, `<fixture>/<slug>/<slug>.md`
# or `<fixture>/proposals/<slug>/<slug>.md` (a nested file counts only in the
# folder named by its stem, so w13's flat proposal at its root is never
# built). `--list` prints that walk without building, and
# tests/unit/test_fixture_paths.py holds it equal to the shared walker's. A
# run that builds fewer proposals than there are oracles fails, so a layout
# change can never silently empty this tier.
set -eu

TEMPLATES="skills/proposal-publish/templates"
FIXTURES="tests/fixtures"

# list_proposals: the proposal of every oracle-bearing fixture, one per line
list_proposals() {
    for oracle in "$FIXTURES"/*/expected.json; do
        fixture=${oracle%/expected.json}
        for proposal in "$fixture"/*/*.md "$fixture"/proposals/*/*.md; do
            [ -f "$proposal" ] || continue
            if [ "$(basename "$(dirname "$proposal")").md" = "$(basename "$proposal")" ]; then
                echo "$proposal"
            fi
        done
    done
}

if [ "${1:-}" = "--list" ]; then
    list_proposals
    exit 0
fi

workdir=$(mktemp -d)
trap 'rm -rf "$workdir"' EXIT
failed=0
built=0
oracles=0
for oracle in "$FIXTURES"/*/expected.json; do
    oracles=$((oracles + 1))
done
list_proposals > "$workdir/proposals.txt"

while IFS= read -r proposal; do
    rel=${proposal#"$FIXTURES"/}
    name=${rel%%/*}
    # copy the fixture's whole workspace: f16's proposal links img/ in its folder
    cp -r "$FIXTURES/$name" "$workdir/$name"
    staged="$workdir/$rel"
    source="${staged%.md}.typ"

    if ! pandoc "$staged" \
        --resource-path "$(dirname "$staged")" \
        --shift-heading-level-by=-1 \
        -M lang=en \
        -M references-heading=References \
        --lua-filter "$TEMPLATES/subtitle-filter.lua" \
        --lua-filter "$TEMPLATES/author-intext.lua" \
        --lua-filter "$TEMPLATES/cite-split.lua" \
        --csl "$TEMPLATES/compact-numeric.csl" \
        --citeproc \
        --lua-filter "$TEMPLATES/rq-filter.lua" \
        --lua-filter "$TEMPLATES/todo-filter.lua" \
        --template "$TEMPLATES/proposal.typ" \
        -o "$source" < /dev/null; then
        echo "FAIL (pandoc): $name"
        failed=1
        continue
    fi

    if ! typst compile "$source" "${source%.typ}.pdf" < /dev/null; then
        echo "FAIL (typst): $name"
        failed=1
        continue
    fi

    built=$((built + 1))
done < "$workdir/proposals.txt"

echo "typst tier: $built of $oracles oracle-bearing fixtures built"
if [ "$failed" -ne 0 ]; then
    echo "typst tier: at least one fixture failed to build"
    exit 1
fi
if [ "$built" -eq 0 ] || [ "$built" -lt "$oracles" ]; then
    echo "typst tier: built $built proposals but $oracles fixtures carry an oracle — the walk no longer finds the corpus"
    exit 1
fi
