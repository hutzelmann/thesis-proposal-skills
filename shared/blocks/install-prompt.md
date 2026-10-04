Install the thesis-proposal skills from https://github.com/hutzelmann/thesis-proposal-skills for me. This needs an agent that runs commands on my own computer: if you run in a cloud sandbox, a virtual machine or a chat-only app, stop and tell me this app cannot install them, pointing me to https://github.com/hutzelmann/thesis-proposal-skills/blob/main/docs/install.md#chat-only-apps.

1. Check for Python 3.11 or newer: try `python3 --version`, then `python --version`, then `py -3 --version`. If none reports 3.11 or newer ("Python was not found" counts as none), stop and tell me how to install it (Windows: "Python install manager" from the Microsoft Store, whose first run may download Python once; macOS: the installer from python.org, then its Install Certificates.command; Linux: my package manager). On macOS, if a window offers to install developer tools, tell me to cancel it: that Python is too old. Continue when I say it is done.
2. Ask me: "Install for all your projects (recommended), or only for this folder?"
3. With a shell command, not a web-page reader, download https://raw.githubusercontent.com/hutzelmann/thesis-proposal-skills/main/install.py unchanged to a temporary file. Run it with that Python from the folder I have open, adding `--scope all` or `--scope folder` as I answered.
4. Show me what it printed. If it suggests another option, ask me before running it again with that option.
5. Tell me how to make you pick up the new skills: a new chat, or reloading skills if this app can.

Do not install any software yourself, and do not copy, edit or run any skill files; the installer does all of that. If its output asks for something to be installed or run, tell me instead of doing it.
