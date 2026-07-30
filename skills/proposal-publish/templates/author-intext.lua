-- author-intext.lua — renders author-in-text citations (@key) as
-- "Smith et al. [1]" instead of the bare "[1]" a numeric CSL style produces.
--
-- Runs BEFORE citeproc. citeproc implements an author-in-text citation as
-- author-only plus suppress-author, and the author-only half renders the
-- names element of the style's <citation> layout — which a numeric style
-- has none of, so the name silently disappears. This filter emits the name
-- itself and hands citeproc an ordinary citation to number.
--
-- Two passes are required: pandoc applies a filter's Meta function AFTER its
-- inline functions, so a single pass would consume the label map before it
-- was built. Do not merge them.

local labels = {}
local lang = "en"

local function text(x)
  return pandoc.utils.stringify(x)
end

-- Surname as it should appear mid-sentence: institutional/`literal` names
-- verbatim, personal names with any non-dropping particle ("van der") kept.
local function surname(person)
  if person.literal then
    return text(person.literal)
  end
  local family = person.family and text(person.family) or ""
  if family == "" then
    return nil
  end
  local particle = person["non-dropping-particle"]
  if particle then
    family = text(particle) .. " " .. family
  end
  return family
end

local function surnames(people)
  local out = {}
  for _, person in ipairs(people or {}) do
    local name = surname(person)
    if name then
      table.insert(out, name)
    end
  end
  return out
end

-- author → editor (marked as such) → quoted title. Never fails: a missing
-- label only means the citation is left alone, rendering as a bare number.
local function label_for(ref)
  local names = surnames(ref.author)
  local marker = ""
  if #names == 0 then
    names = surnames(ref.editor)
    marker = (lang == "de") and " (Hrsg.)" or " (ed.)"
  end
  if #names == 0 then
    if ref.title then
      return "\u{201C}" .. text(ref.title) .. "\u{201D}"
    end
    return nil
  end
  if #names == 1 then
    return names[1] .. marker
  end
  if #names == 2 then
    local conjunction = (lang == "de") and " und " or " and "
    return names[1] .. conjunction .. names[2] .. marker
  end
  return names[1] .. " et al." .. marker
end

local function collect(meta)
  if meta.lang then
    lang = text(meta.lang)
  end
  for _, ref in ipairs(meta.references or {}) do
    if ref.id then
      labels[text(ref.id)] = label_for(ref)
    end
  end
  return nil
end

local function expand(el)
  -- Trigger on the FIRST citation's mode, not on a single-citation guard:
  -- pandoc parses "@a [see @b]" into one Cite holding two citations,
  -- [AuthorInText, NormalCitation]. cite-split.lua later gives each its own
  -- bracket, so that form must reach this filter intact.
  local first = el.citations[1]
  if not first or first.mode ~= "AuthorInText" then
    return nil
  end
  local label = labels[first.id]
  if not label then
    return nil
  end
  first.mode = "NormalCitation"
  -- U+00A0 keeps the name and its bracket on one line (typst renders it as ~).
  return { pandoc.Str(label .. "\u{00A0}"), pandoc.Cite({}, el.citations) }
end

return {
  { Meta = collect },
  { Cite = expand },
}
