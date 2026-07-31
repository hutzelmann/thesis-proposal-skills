-- todo-filter.lua — renders `[TODO: …]` markers as numbered annotations
-- instead of plain prose, so a leftover gap cannot be read as a finished
-- sentence in the built document.
--
-- Two filter tables, not one: pandoc applies `Meta` AFTER the blocks within a
-- single table, which would number a `subtitle` marker last. Running `Meta` as
-- its own earlier table makes metadata numbers precede body numbers, matching
-- reading order. `author-intext.lua` uses the same shape for the same reason.
--
-- Marker syntax is canonically defined by `todo_marker` in
-- `shared/structure.json` ("\\[TODO:[^\\]]*\\]"); the scanner below is kept in
-- sync with it by tests/unit/test_todo_filter_drift.py. Pandoc parses a marker
-- into a run of Str/Space inlines with the brackets fused to the outer words,
-- so this cannot key on a single Str.

local counter = 0

-- Block-level annotations are only legal where the surrounding structure
-- accepts block content. Inside these, every marker degrades to the inline
-- form — notably so rq-filter.lua's pandoc.Plain(inlines) rebuild of a
-- research-question item stays valid.
local INLINE_ONLY = {
  Header = true, BulletList = true, OrderedList = true,
  DefinitionList = true, BlockQuote = true, Table = true,
}

-- Find the next marker in `inlines` at or after `start`.
-- Returns first index, last index, hint inlines, and any text that followed the
-- closing bracket inside the same Str — or nil when no marker remains.
local function find_marker(inlines, start)
  for i = start, #inlines do
    local el = inlines[i]
    local after_open = el.t == "Str" and el.text:match("^%[TODO:(.*)$")
    if after_open then
      local hint, tail, last = {}, nil, nil
      -- the opening Str may already carry the closing bracket ("[TODO:x]")
      local pre, post = after_open:match("^([^%]]*)%](.*)$")
      if pre then
        if pre ~= "" then table.insert(hint, pandoc.Str(pre)) end
        if post ~= "" then tail = pandoc.Str(post) end
        last = i
      else
        if after_open ~= "" then table.insert(hint, pandoc.Str(after_open)) end
        for j = i + 1, #inlines do
          local e = inlines[j]
          local p, q = nil, nil
          if e.t == "Str" then p, q = e.text:match("^([^%]]*)%](.*)$") end
          if p then
            if p ~= "" then table.insert(hint, pandoc.Str(p)) end
            if q ~= "" then tail = pandoc.Str(q) end
            last = j
            break
          elseif e.t == "SoftBreak" or e.t == "LineBreak" then
            -- a marker split across source lines reads as one annotation
            table.insert(hint, pandoc.Space())
          else
            table.insert(hint, e)
          end
        end
      end
      if last then
        while hint[1] and hint[1].t == "Space" do table.remove(hint, 1) end
        while hint[#hint] and hint[#hint].t == "Space" do table.remove(hint) end
        return i, last, hint, tail
      end
      -- unterminated marker: leave it as written and keep looking
    end
  end
  return nil
end

local function is_break(el)
  return el == nil or el.t == "SoftBreak" or el.t == "LineBreak"
end

-- A marker owns its source line when nothing but a line break (or the edge of
-- the paragraph) sits on either side of it.
local function owns_line(inlines, first, last)
  return is_break(inlines[first - 1]) and is_break(inlines[last + 1])
end

-- soul re-scans \hl's argument token by token and aborts with "Reconstruction
-- failed" on anything richer than plain text, so the LaTeX tier only
-- highlights a hint made purely of words and spaces.
local function is_plain_text(hint)
  for _, el in ipairs(hint) do
    if el.t ~= "Str" and el.t ~= "Space" then return false end
  end
  return true
end

-- Wrap the hint's own inlines in raw delimiters rather than re-serializing
-- them, so the writer keeps its own escaping of dashes, quotes, and specials.
local function wrap(hint, format, open, close)
  local out = { pandoc.RawInline(format, open) }
  for _, el in ipairs(hint) do table.insert(out, el) end
  table.insert(out, pandoc.RawInline(format, close))
  return out
end

local function inline_annotation(n, hint)
  if FORMAT:match("typst") then
    return wrap(hint, "typst", "#todo-inline(" .. n .. ")[", "]")
  elseif FORMAT:match("latex") then
    local macro = is_plain_text(hint) and "todoinline" or "todoinlineplain"
    return wrap(hint, "latex", "\\" .. macro .. "{" .. n .. "}{", "}")
  end
  -- every other writer, docx included: pandoc maps a `mark` span to a real
  -- highlight run, so the word-processor tier gets a genuine annotation
  local content = { pandoc.Strong({ pandoc.Str("TODO " .. n) }), pandoc.Space() }
  for _, el in ipairs(hint) do table.insert(content, el) end
  return { pandoc.Span(content, pandoc.Attr("", { "mark" })) }
end

local function block_annotation(n, hint)
  if FORMAT:match("typst") then
    return pandoc.Plain(wrap(hint, "typst", "#todo-block(" .. n .. ")[", "]"))
  elseif FORMAT:match("latex") then
    local macro = is_plain_text(hint) and "todoblock" or "todoblockplain"
    return pandoc.Plain(wrap(hint, "latex", "\\" .. macro .. "{" .. n .. "}{", "}"))
  end
  return pandoc.Para(inline_annotation(n, hint))
end

-- Convert every marker in one inline list. Returns a block list when an
-- own-line marker split the paragraph, otherwise nil plus the rewritten
-- inlines.
local function convert(inlines, allow_block)
  local blocks, run, i, split = {}, {}, 1, false
  while i <= #inlines do
    local first, last, hint, tail = find_marker(inlines, i)
    if not first then
      for j = i, #inlines do table.insert(run, inlines[j]) end
      break
    end
    for j = i, first - 1 do table.insert(run, inlines[j]) end
    counter = counter + 1
    if allow_block and tail == nil and owns_line(inlines, first, last) then
      while #run > 0 and is_break(run[#run]) do table.remove(run) end
      if #run > 0 then table.insert(blocks, pandoc.Para(run)) end
      run = {}
      table.insert(blocks, block_annotation(counter, hint))
      split = true
      i = last + 1
      if is_break(inlines[i]) and inlines[i] ~= nil then i = i + 1 end
    else
      for _, el in ipairs(inline_annotation(counter, hint)) do
        table.insert(run, el)
      end
      if tail then table.insert(run, tail) end
      i = last + 1
    end
  end
  if split then
    if #run > 0 then table.insert(blocks, pandoc.Para(run)) end
    return blocks
  end
  return nil, run
end

local function convert_inline_only(inlines)
  return (select(2, convert(inlines, false)))
end

-- A hand-written recursion rather than a Para handler: a handler cannot tell a
-- top-level paragraph from one inside a list item, and splitting containers
-- across filter tables would number a list in a later section before a
-- paragraph in an earlier one. One depth-first walk keeps both correct.
local function process(blocks, allow_block)
  local out = {}
  for _, blk in ipairs(blocks) do
    if blk.t == "Para" or blk.t == "Plain" then
      local split, inlines = convert(blk.content, allow_block)
      if split then
        for _, b in ipairs(split) do table.insert(out, b) end
      else
        blk.content = inlines
        table.insert(out, blk)
      end
    elseif blk.t == "BulletList" or blk.t == "OrderedList" then
      for k, item in ipairs(blk.content) do
        blk.content[k] = process(item, false)
      end
      table.insert(out, blk)
    elseif blk.t == "BlockQuote" or blk.t == "Div" then
      blk.content = process(blk.content, blk.t == "Div" and allow_block or false)
      table.insert(out, blk)
    elseif INLINE_ONLY[blk.t] then
      table.insert(out, pandoc.walk_block(blk, { Inlines = convert_inline_only }))
    else
      table.insert(out, blk)
    end
  end
  return out
end

-- Only `title` and `subtitle` may carry a marker. `references` is never
-- visited, so a bracketed fragment inside a reference abstract can neither be
-- styled nor consume a number.
local function number_metadata(meta)
  for _, key in ipairs({ "title", "subtitle" }) do
    local value = meta[key]
    if value and pandoc.utils.type(value) == "Inlines" then
      meta[key] = pandoc.Inlines(convert_inline_only(value))
    end
  end
  return meta
end

return {
  { Meta = number_metadata },
  { Pandoc = function(doc)
      doc.blocks = process(doc.blocks, true)
      return doc
    end },
}
