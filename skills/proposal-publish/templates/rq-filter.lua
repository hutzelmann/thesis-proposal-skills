-- rq-filter.lua — styles the ordered list under the research-questions
-- heading as bold "RQ n:" items (typst output; other formats untouched).
-- The list itself stays plain markdown in the proposal file.

local expect_rq_list = false

local function is_rq_heading(text)
  return text:match("Research Questions") ~= nil
    or text:match("Forschungsfragen") ~= nil
end

function Header(el)
  expect_rq_list = is_rq_heading(pandoc.utils.stringify(el))
  return nil
end

function OrderedList(el)
  if not expect_rq_list then
    return nil
  end
  expect_rq_list = false
  if not FORMAT:match("typst") then
    return nil
  end
  -- Wrap each item's already-processed inlines with raw #rq(n)[ ... ] markers
  -- in place, instead of re-serializing the item as a standalone sub-document:
  -- a standalone pandoc.write() runs before citeproc has resolved citations
  -- inside list items, leaving unresolved @key citations that typst can't find.
  local out = {}
  for i, item in ipairs(el.content) do
    local blocks = {}
    for j, block in ipairs(item) do
      if block.t == "Plain" or block.t == "Para" then
        local inlines = block.content
        if j == 1 then
          table.insert(inlines, 1, pandoc.RawInline("typst", "#rq(" .. i .. ")["))
        end
        if j == #item then
          table.insert(inlines, pandoc.RawInline("typst", "]"))
        end
        table.insert(blocks, pandoc.Plain(inlines))
      else
        table.insert(blocks, block)
      end
    end
    for _, b in ipairs(blocks) do
      table.insert(out, b)
    end
  end
  return out
end
