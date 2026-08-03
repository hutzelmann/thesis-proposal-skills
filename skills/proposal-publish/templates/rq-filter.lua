-- rq-filter.lua — styles the ordered list under the research-questions
-- heading as bold "RQ n:" items (typst and latex output via #rq()/\rqblock
-- in the templates; other formats untouched). The list itself stays plain
-- markdown in the proposal file.

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
  local fmt
  if FORMAT:match("typst") then
    fmt = "typst"
  elseif FORMAT:match("latex") then
    fmt = "latex"
  else
    return nil
  end
  -- Wrap each item's already-processed inlines with raw #rq(n)[ ... ] (typst)
  -- or \rqblock{n}{ ... } (latex) markers in place, instead of re-serializing
  -- the item as a standalone sub-document: a standalone pandoc.write() runs
  -- before citeproc has resolved citations inside list items, leaving
  -- unresolved @key citations that the final document can't find.
  local out = {}
  for i, item in ipairs(el.content) do
    local open, close
    if fmt == "typst" then
      open, close = "#rq(" .. i .. ")[", "]"
    else
      open, close = "\\rqblock{" .. i .. "}{", "}"
    end
    local blocks = {}
    for j, block in ipairs(item) do
      if block.t == "Plain" or block.t == "Para" then
        local inlines = block.content
        if j == 1 then
          table.insert(inlines, 1, pandoc.RawInline(fmt, open))
        end
        if j == #item then
          table.insert(inlines, pandoc.RawInline(fmt, close))
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
