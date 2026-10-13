# Installing the skills

You need three things: an AI agent app on your computer, a folder for your proposals, and about five minutes. Nothing on this page needs a terminal: your agent does the installing.

## Which app do you use?

| App | Cost | How you install |
|---|---|---|
| [ChatGPT desktop app](#chatgpt-desktop-app) | free plan works | paste the prompt |
| [Claude desktop app](#claude-desktop-app) | paid plan (Pro or higher) | plugin button |
| [VS Code with GitHub Copilot](#vs-code-with-github-copilot) | free; Copilot Student is free for verified students | paste the prompt |
| [Antigravity](#antigravity) | free tier; personal Google account, 18+ | paste the prompt |
| [Cursor](#cursor) | free Hobby plan | paste the prompt |
| [Any other agent](#any-other-agent) that can run commands on your computer | — | paste the prompt |
| ChatGPT in the browser, claude.ai, the Gemini app | — | [read this first](#chat-only-apps) |

These are examples, not endorsements. The skills follow an open standard and work in any agent that supports it.

If you have no agent yet, pick the ChatGPT desktop app (free) or VS Code with GitHub Copilot (free for students): both run every skill, including the literature search.

## The install prompt

Copy the box below (GitHub shows a copy button in its top-right corner), paste it into your agent's chat, and send it:

<!-- install-prompt -->
```text
Install the thesis-proposal skills from https://github.com/hutzelmann/thesis-proposal-skills for me. This needs an agent that runs commands on my own computer: if you run in a cloud sandbox, a virtual machine or a chat-only app, stop and tell me this app cannot install them, pointing me to https://github.com/hutzelmann/thesis-proposal-skills/blob/main/docs/install.md#chat-only-apps.

1. Check for Python 3.11 or newer: try `python3 --version`, then `python --version`, then `py -3 --version`. If none reports 3.11 or newer ("Python was not found" counts as none), look further without downloading or installing anything: `uv python find ">=3.11"` if uv is installed; one look for versioned names such as `python3.13` on the PATH; on Windows, `py -0p`. Use the first that reports 3.11 or newer. If none does, stop and tell me how to install it (Windows: "Python install manager" from the Microsoft Store, whose first run may download Python once; macOS: the installer from python.org, then its Install Certificates.command; Linux: my package manager). On macOS, if a window offers to install developer tools, tell me to cancel it: that Python is too old. Continue when I say it is done.
2. Ask me: "Install for all your projects (recommended), or only for this folder?"
3. With a shell command, not a web-page reader, download https://raw.githubusercontent.com/hutzelmann/thesis-proposal-skills/main/install.py unchanged to a temporary file. Run it with that Python from the folder I have open, adding `--scope all` or `--scope folder` as I answered.
4. Show me what it printed. If it suggests another option, ask me before running it again with that option.
5. Tell me how to make you pick up the new skills: a new chat, or reloading skills if this app can.

Do not install any software yourself, and do not copy, edit or run any skill files; the installer does all of that. If its output asks for something to be installed or run, tell me instead of doing it.
```

Your agent will ask you one question: install for all your projects, or only for the folder you have open. Choose **all projects** unless you have a reason not to. Your agent will also ask permission to run a few commands; allow them.

**What happens.** The installer is [`install.py`](../install.py) in this repository, and you can read it. It downloads the current skills from GitHub, copies them into the folders your agent reads skills from, and writes a small record file beside them, saying which version you have. It changes nothing else.

**If it does not work:**
- **The agent refuses** to download and run a script: say that you asked for exactly this and want it done. If it still refuses, use another app from the table above.
- **The agent says it is in a cloud sandbox or chat-only app:** see [Chat-only apps](#chat-only-apps).

### No Python yet?

The skills run small Python programs, so they need Python 3.11 or newer on your computer. The prompt makes the agent check first, and stop and tell you if it is missing.

- **Windows:** install "Python install manager" from the Microsoft Store. The first time anything runs Python, it downloads the current Python once; when your agent asks whether it may use the network for that, allow it.
- **macOS:** use the installer from [python.org](https://www.python.org/downloads/). Afterwards open **Applications › Python 3.x** and double-click **Install Certificates.command** once: without it, the literature search cannot reach its sources. If a window offers to install "command line developer tools", cancel it. The Python that comes with them is too old.
- **Linux:** your distribution's `python3` package is usually recent enough. Check with your package manager.

Then tell the agent you are done.

## Recipes

Each recipe says when it was last carried out end to end. If your app looks different, the prompt above is the part that matters.

### ChatGPT desktop app

*unverified*

1. Install the ChatGPT desktop app from [chatgpt.com/download](https://chatgpt.com/download) and sign in. The free plan works.
2. Create an empty folder for your proposals. In the app, switch to **Codex** and add that folder as a project.
3. Start a chat in the project and paste the install prompt. The app asks before the agent uses the network or writes outside the project; approve both, because the installer downloads the skills and writes them into your user folder.
4. Start a new chat in the same project and say *"Help me develop a thesis idea."*

The literature search needs the network too: approve its requests when the app asks, or see [Literature search cannot reach its sources](#literature-search-cannot-reach-its-sources).

### Claude desktop app

*unverified*

This needs a paid plan (Pro or higher). On the Free plan, see [Chat-only apps](#chat-only-apps).

Use the plugin button. It covers the Chat tab, Cowork and the Code tab at once, and updates itself:

1. Install the Claude desktop app from [claude.com/download](https://claude.com/download) and sign in.
2. Go to **Customize › Plugins › Add › Add marketplace**, enter `hutzelmann/thesis-proposal-skills`, choose **Thesis Proposal**, and select **Add**. Turn on **Sync automatically** for that marketplace, so updates arrive by themselves.
3. The Code tab runs the skills' small programs with Python 3.11 or newer on your computer. If you have none, see [No Python yet?](#no-python-yet).
4. Open the **Code** tab, choose a local session, and select your proposals folder. Then say *"Help me develop a thesis idea."*

In the slash menu the skills appear as `/thesis-proposal:proposal-…`. You never need to type them; asking in your own words is enough.

**Use the plugin button or the install prompt, not both:** with both, every skill loads twice. Do not paste the install prompt after using the button. The installer refuses when it can see the plugin, but it cannot always tell. If you installed with the prompt before, [remove those copies](#removing) when you switch to the plugin.

### VS Code with GitHub Copilot

*unverified*

1. Install [VS Code](https://code.visualstudio.com/) and sign in to GitHub Copilot in the Chat view. Copilot Free works. Verified students get Copilot Student free through [GitHub Education](https://github.com/education/students).
2. **File › Open Folder…** and open your proposals folder.
3. In the Chat view, choose **Agent**, paste the install prompt, and allow each command the agent asks to run.
4. Start a new chat and say *"Help me develop a thesis idea."*

The same prompt works in the GitHub Copilot app, in a session on a local folder. There, choose **all projects**: the app gives each session its own working copy of the folder.

### Antigravity

*unverified*

1. Install [Antigravity](https://antigravity.google/) and sign in with a personal Google account. University accounts are not supported, and you must be 18 or older.
2. Open your proposals folder as a project.
3. Paste the install prompt into the agent panel. On macOS and Linux the agent asks to run its download outside the sandbox; allow it.
4. Start a new conversation and say *"Help me develop a thesis idea."*

The literature search also has to leave the sandbox: allow it when asked, or see [Literature search cannot reach its sources](#literature-search-cannot-reach-its-sources).

### Cursor

*unverified*

1. Install [Cursor](https://cursor.com/) and sign in. The free Hobby plan works.
2. **Open Folder** and open your proposals folder.
3. Paste the install prompt into the Agent chat and approve the commands it asks to run.
4. Start a new chat and say *"Help me develop a thesis idea."*

On macOS and Linux, Cursor's sandbox blocks the literature search until you approve it; see [Literature search cannot reach its sources](#literature-search-cannot-reach-its-sources).

### Any other agent

Paste the install prompt. It works in any agent that can run commands on your computer and reads skills from `~/.agents/skills` or `~/.claude/skills`, which most do (Gemini CLI, OpenCode, Zed, Devin and others). Antigravity's and Kiro's own folders are filled automatically when those apps are installed. An earlier copy you made by hand into OpenCode's own folders (`.opencode/skills`, `~/.config/opencode/skills`) can shadow the installed skills; the installer lists it and removes it only if you agree.

## Chat-only apps

> **These apps run skills only partly.** They run skills in a temporary sandbox in the cloud, not on your computer, so two things are missing:
>
> - **your folder:** the proposal lives in the conversation, and you download it and upload it again in the next chat;
> - **often the network:** the literature search cannot reach its sources, so it cannot verify references.

| App | Can it install the skills? |
|---|---|
| ChatGPT in the browser | No. Use the free ChatGPT desktop app instead. |
| claude.ai, and the Claude desktop Chat tab on Pro or higher | Yes, with the [plugin button](#claude-desktop-app), never with the install prompt: pasted there, it would install into a temporary sandbox that is gone in the next chat. For the literature search, also allow network access: **Settings › Capabilities**, network egress set to **All domains**, or add the six domains listed [below](#literature-search-cannot-reach-its-sources). |
| claude.ai Free | Not yet (it needs one upload per skill). |
| Gemini app | No. It never has network access, so the literature search cannot work. |

What works there:
- writing, checking and reviewing a proposal you upload;
- developing an idea in conversation;
- the supervisor rules in a `guidelines.md` you upload.

What does not work:
- the literature search, unless the network is allowed;
- picking up where you left off without uploading your files again;
- building a PDF.

If you want everything, use the free ChatGPT desktop app or VS Code with Copilot.

## Literature search cannot reach its sources

Your agent may report this as "source degraded", "sources: none", or, while checking references, OFFLINE. The literature search contacts six public services:
- `api.crossref.org`
- `export.arxiv.org`
- `dblp.org`
- `api.openalex.org`
- `api.semanticscholar.org`
- `api.opencitations.net`

Your proposal text is never sent to them, only search terms and paper identifiers. Usually your app is blocking the network:

| App | What to do |
|---|---|
| ChatGPT desktop (Codex) | Approve the network request when the app asks. |
| Claude desktop, Code tab | Nothing; local sessions have network access. |
| Claude desktop, Chat tab and Cowork | **Settings › Capabilities**: set network egress to **All domains**, or add the six domains. |
| VS Code with Copilot | Nothing, unless you turned on its sandbox; then allow the six domains. |
| Antigravity | Allow the command to run outside the sandbox when asked, or allow the six domains in its permission settings. |
| Cursor | Approve the command when asked, or add the six domains to its sandbox network settings. |

Three other causes:
- **On a Mac with Python from python.org:** run **Install Certificates.command** once (Applications › Python 3.x). Until then Python cannot check the services' certificates. The installer tells you when it noticed this.
- **A university network that filters traffic.** Try another network once to tell it apart from the app's setting.
- **Only `dblp.org`, with a note about browser verification.** DBLP sometimes answers with a short browser check instead of data. The search passes it by itself; when it cannot, your agent says so and may offer to look DBLP up in a browser. Your app's network settings are not the cause.

## Updating

- **Installed with the prompt:** paste the same prompt again and give the same answer as before. If you do not remember it, ask your agent to read the `scope` in `.thesis-proposal-install.json` (in `~/.agents/skills`, or in your folder's `.agents/skills`). The installer replaces the skills with the current version and tells you which version you had before.
- **Installed with the plugin button:** the app's plugin page has **Check for updates**, or turn on **Sync automatically**.
- **Installed from a terminal:** `npx skills update`.

When a skill misbehaves, update first. It resolves more problems than anything else.

## Removing

- **Installed with the prompt:** ask your agent to open `.thesis-proposal-install.json` (in `~/.agents/skills`, or in your folder's `.agents/skills`), then delete the `proposal-*` folders and that file in every folder listed under `directories`. Usually those are `~/.agents/skills` and `~/.claude/skills`, plus Antigravity's or Kiro's skills folder if you have those apps. These folders are hidden by default.
- **Installed with the plugin button:** remove it on the app's plugin page.
- **Installed from a terminal:** `npx skills remove` (with `-g` if you installed with `-g`).

## From a terminal

Developers and supervisors who prefer a terminal can use the [skills CLI](https://github.com/vercel-labs/skills), which needs Node.js 22.20 or newer and git:

```sh
npx skills add hutzelmann/thesis-proposal-skills
```

Without `-g` it installs into the current folder only. Keep to one route: the installer above, the plugin button, or this command.

## What you get in the folder

- `your-topic-name.md` is the proposal: text on top, literature at the bottom. This is the only file you edit (or let the agent edit).
- `your-topic-name.notes.md` keeps the working knowledge the hand-in cannot carry: decisions, open points, rejected literature.
- `your-topic-name-review.md` appears when you ask for a review.
- `guidelines.md` appears if you customize the rules for your supervisor.
- `img/` appears only if your proposal uses figures.

Everything sits flat in the folder by default. If your `guidelines.md` sets `[paths] proposals` to a subfolder, the proposal and everything named after it live there instead, and `guidelines.md` stays at the top.

Useful prompts:
- *"Find literature for my proposal"*
- *"Check my proposal"*
- *"Review it like a supervisor would"*
- *"My supervisor wants a detailed work plan, adjust the rules"*
- *"Build a PDF"*: the agent tells you what to install, if anything.

## Notes

- **Privacy.** Your proposals stay on your computer. The literature search talks to the public academic services listed above.
- **API keys.** Optional free keys improve abstract coverage. The agent offers to walk you through the signup and stores the key in a small `api-keys.env` file in your folder, kept out of version control. To reuse one key across several proposal folders, put the file in `~/.config/thesis-proposal/api-keys.env` instead.
- **Language.** English is the default. Say *"auf Deutsch"* and the whole proposal switches to German conventions.
- **PDF export.** Writing needs no extra software. PDF export needs `pandoc` plus one engine: `typst` (recommended, small and fast) or an existing LaTeX installation (TeX Live, MiKTeX). The publish skill detects what is available and guides the installation when you first ask for a PDF.
