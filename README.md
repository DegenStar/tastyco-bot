<div align="center">

# TastyCo BOT

**Automated TastyCo account operations with multi-account, EVM wallet, CAPTCHA, and proxy support.**

[![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Repository](https://img.shields.io/badge/GitHub-yukiasuna15%2Ftasty-181717?logo=github&logoColor=white)](https://github.com/yukiasuna15/tasty)
[![Stars](https://img.shields.io/github/stars/yukiasuna15/tasty?style=flat&logo=github)](https://github.com/yukiasuna15/tasty/stargazers)
[![License](https://img.shields.io/badge/License-Not%20specified-lightgrey.svg)](#license)

</div>

## Overview

TastyCo BOT is a Python-based automation utility for interacting with the TastyCo platform through its web API. It supports multiple EVM accounts, wallet-based authentication, daily reward claims, available mission processing, optional proxy routing, and continuous scheduled execution.

The project is designed for users who want a repeatable command-line workflow for managing several authorized accounts from one local environment. It uses the private keys supplied in the local account file only to derive wallet addresses and sign authentication messages.

> **Use responsibly.** Run this project only with accounts, wallets, proxies, and API credentials that you own or are explicitly authorized to operate. Review the platform's terms and applicable laws before using any automation.

## Features

| Capability | Description |
|---|---|
| **Multi-account processing** | Loads and processes multiple EVM accounts sequentially. |
| **Wallet authentication** | Derives EVM addresses and signs the authentication message required by the platform. |
| **Token lifecycle** | Refreshes access and refresh tokens when required. |
| **Daily rewards** | Checks the current daily reward status and claims an eligible reward. |
| **Mission handling** | Lists available missions, starts supported activities, and claims eligible rewards. |
| **Optional proxy routing** | Runs with direct connectivity or assigns proxies per account. |
| **Proxy rotation** | Can rotate to the next proxy when a configured proxy fails its connectivity check. |
| **User-agent rotation** | Assigns user-agent entries to accounts from `useragent.txt`. |
| **Scheduled loop** | Repeats account processing on a daily UTC schedule after the initial run. |
| **Terminal logging** | Displays account, points, rank, role, connection, mission, and reward status in the terminal. |

## Project Structure

```text
.
├── bot.py              # Main automation script
├── requirements.txt    # Pinned Python dependencies
├── accounts.txt        # One authorized EVM private key per line
├── sctg.txt            # CAPTCHA solver API key read by the script
├── proxy.txt           # Optional proxy list
├── useragent.txt       # User-agent list
├── captcha_key.txt     # Additional local key file from the source archive
├── README.md
└── .gitignore
```

## Requirements

Before starting, make sure the following are available on the machine where the project will run:

- Python 3.9 or later.
- `pip` with permission to install the dependencies.
- Authorized EVM wallet accounts for testing and operation.
- A valid CAPTCHA solver credential configured locally.
- Optional HTTP, HTTPS, SOCKS4, or SOCKS5 proxies.

The exact package versions are pinned in [`requirements.txt`](requirements.txt), including `cloudscraper`, `eth-account`, `eth-utils`, and `colorama`.

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/yukiasuna15/tasty.git
cd tasty
```

### 2. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

On Windows PowerShell, use:

```powershell
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Configuration

The script reads its runtime configuration from text files in the project root. Use placeholders while preparing the files and never commit real secrets to a public repository.

### `accounts.txt`

Add one authorized EVM private key per line:

```text
0xYOUR_AUTHORIZED_PRIVATE_KEY_1
0xYOUR_AUTHORIZED_PRIVATE_KEY_2
```

### `sctg.txt`

The script reads the first line as the CAPTCHA solver API key:

```text
YOUR_CAPTCHA_SOLVER_API_KEY
```

### `useragent.txt`

Add one browser user-agent string per line. The script accepts entries beginning with `Mozilla/5.0`:

```text
Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36
Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36
```

### `proxy.txt` (optional)

The file accepts one proxy per line. A scheme is optional; when omitted, the script assumes HTTP:

```text
192.0.2.10:8080
https://192.0.2.11:8443
socks5://username:password@192.0.2.12:1080
```

Keep proxy credentials private and use only infrastructure you are authorized to access.

## Usage

Start the bot from the project directory:

```bash
python bot.py
```

At startup, the program asks whether to use proxies:

```text
1. Run With Proxy
2. Run Without Proxy
```

When proxy mode is enabled, it also asks whether invalid proxies should be rotated automatically. After the initial account pass, the program waits for the next scheduled UTC run and continues processing the configured accounts.

## Operational Notes

The bot signs authentication messages with the configured wallets and sends requests to the TastyCo API. Mission types that require external actions, such as connecting a Telegram bot or inviting a real user, may still require manual completion. Network failures, invalid credentials, expired tokens, unavailable missions, and CAPTCHA solver errors can prevent an account from completing its cycle.

Do not run the bot against accounts that you do not own or manage with explicit permission. Avoid sharing terminal output, private keys, API keys, access tokens, refresh tokens, or authenticated proxy URLs in issues, pull requests, screenshots, or chat messages.

## Security

This repository is public. **Never place real private keys, CAPTCHA credentials, proxy passwords, access tokens, or other secrets in tracked files.** If any secret has previously been committed, revoke or rotate it immediately; deleting the file in a later commit does not remove it from Git history.

For safer local use, keep sensitive configuration outside version control and consider changing the script to load secrets from environment variables or an ignored local configuration file before operating real accounts.

## Contributing

Contributions are welcome when they improve reliability, readability, documentation, or responsible account handling. Before opening a pull request, test changes locally, keep secrets out of commits, explain the behavioral impact, and update this README when configuration or execution steps change.

## Support

For bugs or documentation issues, please open a [GitHub Issue](https://github.com/yukiasuna15/tasty/issues) with a minimal reproducible description. Do not include credentials, private keys, tokens, proxy passwords, or other sensitive data in the issue.

## License

No license has been specified for this repository yet. Until a license is added, the source code should be treated as **all rights reserved** and should not be redistributed or reused beyond applicable permissions.

---

<div align="center">

Maintained by [@yukiasuna15](https://github.com/yukiasuna15)

[View repository](https://github.com/yukiasuna15/tasty) · [Open an issue](https://github.com/yukiasuna15/tasty/issues)

</div>
