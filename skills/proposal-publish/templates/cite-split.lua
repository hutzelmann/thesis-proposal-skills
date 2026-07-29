-- cite-split.lua — splits multi-key citations into adjacent single citations
-- BEFORE citeproc runs, so each reference renders in its own bracket
-- (legacy compactarticle style: max one citation per bracket).

function Cite(el)
  if #el.citations <= 1 then
    return nil
  end
  local out = {}
  for i, citation in ipairs(el.citations) do
    if i > 1 then
      table.insert(out, pandoc.Space())
    end
    table.insert(out, pandoc.Cite({}, {citation}))
  end
  return out
end
