-- subtitle-filter.lua — first in the chain. Lua filters run before pandoc
-- applies --shift-heading-level-by, so this filter sees the source shape:
-- the leading `# <title>` as a level-1 Header and the emphasized subtitle
-- paragraph as the block after it. Three jobs, all about the document frame
-- the body now carries:
--   1. Promote the leading level-1 heading to the `title` metadata (doing it
--      here rather than leaving it to the shift keeps a `[TODO: …]` title
--      marker in metadata, where todo-filter numbers it ahead of the
--      subtitle and the body — reading order).
--   2. Promote the emphasized first paragraph to the `subtitle` metadata;
--      the templates render it in the title block.
--   3. Mark the closing references heading (named by the `references-heading`
--      metadata, "References"/"Literatur") unnumbered, so it renders like a
--      section heading without a number — the look the injected
--      `reference-section-title` headline used to have. citeproc appends the
--      bibliography entries after it.
-- A file whose first block is not the title heading is left alone: the check
-- names that shape, and quietly guessing a title here would hide it.
function Pandoc(doc)
  local blocks = doc.blocks
  local first = blocks[1]
  if first and first.t == "Header" and first.level == 1 and not doc.meta.title then
    doc.meta.title = pandoc.MetaInlines(first.content)
    blocks:remove(1)
    local nxt = blocks[1]
    if nxt and nxt.t == "Para" and #nxt.content == 1
        and nxt.content[1].t == "Emph" and not doc.meta.subtitle then
      doc.meta.subtitle = pandoc.MetaInlines(nxt.content[1].content)
      blocks:remove(1)
    end
  end
  local wanted = doc.meta["references-heading"]
      and pandoc.utils.stringify(doc.meta["references-heading"])
  if wanted then
    for i = #blocks, 1, -1 do
      local block = blocks[i]
      if block.t == "Header" then
        if pandoc.utils.stringify(block.content) == wanted then
          block.identifier = "bibliography"
          block.classes = pandoc.List({ "unnumbered" })
        end
        break
      end
    end
  end
  doc.blocks = blocks
  return doc
end
