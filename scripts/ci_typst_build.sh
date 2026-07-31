#!/bin/sh
# Build every fixture proposal on the typst tier and compile it.
#
# The pandoc/typst image carries pandoc and typst but no Python, so
# tests/unit/test_export_matrix.py cannot run there. This script therefore
# restates the typst tier's pandoc invocation — and that restatement is exactly
# the kind of copy that drifts, so tests/unit/test_ci_typst_drift.py asserts it
# names the same template, CSL, and filters as publish.py's pandoc_command().
# Add a filter there, add it here.
set -eu

TEMPLATES="skills/proposal-publish/templates"
workdir=$(mktemp -d)
trap 'rm -rf "$workdir"' EXIT
failed=0
built=0

for proposal in tests/fixtures/*/*.md; do
    case "$proposal" in
        */README.md | */guidelines.md) continue ;;
    esac
    name=$(basename "$(dirname "$proposal")")
    # copy the fixture's whole directory: f16-figures-import links img/ relatively
    cp -r "$(dirname "$proposal")" "$workdir/$name"
    staged="$workdir/$name/$(basename "$proposal")"
    source="${staged%.md}.typ"

    if ! pandoc "$staged" \
        --lua-filter "$TEMPLATES/author-intext.lua" \
        --lua-filter "$TEMPLATES/cite-split.lua" \
        --csl "$TEMPLATES/compact-numeric.csl" \
        --citeproc \
        --lua-filter "$TEMPLATES/rq-filter.lua" \
        --lua-filter "$TEMPLATES/todo-filter.lua" \
        --template "$TEMPLATES/proposal.typ" \
        -o "$source"; then
        echo "FAIL (pandoc): $name"
        failed=1
        continue
    fi

    if ! typst compile "$source" "${source%.typ}.pdf"; then
        echo "FAIL (typst): $name"
        failed=1
        continue
    fi

    built=$((built + 1))
done

echo "typst tier: $built fixtures built"
if [ "$failed" -ne 0 ]; then
    echo "typst tier: at least one fixture failed to build"
    exit 1
fi
