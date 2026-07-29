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
  local out = {}
  for i, item in ipairs(el.content) do
    local inner = pandoc.write(pandoc.Pandoc(item), "typst"):gsub("%s+$", "")
    table.insert(out, pandoc.RawBlock("typst", "#rq(" .. i .. ")[" .. inner .. "]"))
  end
  return out
end
