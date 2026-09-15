<div align="center">

# 🤖 TastyCo BOT

**支持多账户、EVM 钱包、验证码及代理的 TastyCo 账户自动化操作工具。**

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![星标](https://img.shields.io/github/stars/yukiasuna15/tasty?style=flat&logo=github)](https://github.com/yukiasuna15/tasty/stargazers)
[![许可证](https://img.shields.io/badge/License-Not%20specified-lightgrey.svg)](#许可证)

</div>

![TastyCo 官网首页](pic/web.png)
🔗 官网：https://tastyco.io/

## 📖 项目简介

- TastyCo BOT 是一款基于 Python 的自动化工具，通过 Web API 与 TastyCo 平台交互。它支持多个 EVM 账户、钱包身份验证、每日奖励领取、可用任务处理、可选代理路由以及持续定时运行。

- 本项目适合希望在同一本地环境中，通过可重复执行的命令行流程管理多个授权账户的用户。程序仅使用本地账户文件中提供的私钥来派生钱包地址并签署身份验证消息。

- 当前版本不会创建或发送链上交易，私钥不用于合约写入或资产转账，因此无需为这些账户准备原生币来支付 Gas 费。若未来新增链上操作，则需要根据对应网络的要求准备原生币。

> **请负责任地使用。** 仅可将本项目用于您本人拥有或已获得明确操作授权的账户、钱包、代理和 API 凭据。在使用任何自动化功能前，请先查阅平台条款及适用法律。

## 📦 功能特性

| 功能 | 说明 |
|---|---|
| **多账户处理** | 依次加载并处理多个 EVM 账户。 |
| **钱包身份验证** | 派生 EVM 地址，并签署平台要求的身份验证消息。 |
| **令牌生命周期管理** | 在需要时刷新访问令牌和刷新令牌。 |
| **每日奖励** | 检查当前每日奖励状态，并领取符合条件的奖励。 |
| **任务处理** | 列出可用任务、启动支持的活动并领取符合条件的奖励。 |
| **可选代理路由** | 支持直接连接，或为每个账户分配代理。 |
| **代理轮换** | 配置的代理未通过连通性检查时，可自动切换至下一个代理。 |
| **有界失败处理** | 每轮每个账户最多检查一次各个不同代理，全部失效时跳过账户；不会自动退回直连。 |
| **User-Agent 轮换** | 从 `config/useragent.txt` 中为账户分配 User-Agent。 |
| **定时循环** | 首次运行后，按照每日 UTC 计划重复处理账户。 |
| **单次与非交互运行** | 支持单轮执行、显式代理模式和独立配置目录，适合外部调度。 |
| **终端日志** | 在终端中显示账户、积分、排名、角色、连接、任务及奖励状态。 |

## 🗂️ 项目结构

```text
.
├── bot.py              # 主自动化脚本
├── pyproject.toml      # uv 项目配置、依赖与开发工具
├── uv.lock             # 完整依赖锁文件，应提交到版本控制
├── .python-version     # 默认使用 Python 3.12
├── config/             # 可直接编辑的配置模板（禁止填入真实密钥后提交）
├── tests/              # 离线回归测试
├── pic/web.png         # 官网截图
├── README.md
└── .gitignore
```

## 🌿 环境要求

开始之前，请确保运行本项目的计算机满足以下条件：

- [uv](https://docs.astral.sh/uv/getting-started/installation/)。
- Python 3.10 或更高版本；项目默认选择 3.12，uv 可在需要时自动下载解释器。
- 用于测试和运行的已授权 EVM 钱包账户。
- 已在本地配置有效的验证码识别服务凭据。
- 可选的 HTTP、HTTPS、SOCKS4 或 SOCKS5 代理。

直接依赖在 [`pyproject.toml`](pyproject.toml) 中声明，完整依赖版本由 [`uv.lock`](uv.lock) 锁定。已显式包含 SOCKS 代理支持。依赖要求 Python 3.10 及以上，旧文档中的 3.9 不再适用。

## 🖥️ 跨平台说明

项目支持 macOS、Linux、WSL 和 Windows。脚本使用 `pathlib` 处理配置路径，默认从项目目录下的 `config/` 读取文件；不会依赖当前终端所在目录。uv 会根据 `.python-version` 选择 Python 版本，`uv sync` 和 `uv run` 的命令在四个平台上保持一致。

- **macOS / Linux / WSL**：在终端安装 uv 后执行本文档中的命令。WSL 中请使用 WSL 内的 Python、uv 和项目路径，不要混用 Windows Python 环境。
- **Windows PowerShell**：安装 uv 后，在 PowerShell 中执行相同的 `uv sync`、`uv run` 命令。配置文件统一使用 UTF-8 编码；不要使用批处理文件中的反斜杠替换路径。
- **Windows CMD**：同样支持 `uv` 命令；如果需要传递带空格的配置目录，请将路径放在双引号中，例如 `--config-dir "D:\TastyCo\config"`。

程序只在交互式终端中显示清屏和输入菜单；CI、任务计划程序、cron 或其他无终端调度器必须显式指定 `--proxy` 或 `--no-proxy`。代理、验证码服务和 API 的网络连通性仍取决于当前操作系统、防火墙和网络环境。

## 🚀 安装

### 1. 克隆仓库

```bash
git clone https://github.com/yukiasuna15/tasty.git
cd tasty
```

### 2. 安装依赖/同步环境

```bash
# macOS / Linux / WSL
./install.sh
uv sync --locked
```

```powershell
# Windows：以管理员身份运行 PowerShell
powershell -ExecutionPolicy Bypass -File .\install.ps1
uv sync --locked
```

uv 会创建项目独立的 `.venv`，无需手动激活；Windows、macOS 和 Linux 的 uv 命令一致。只运行程序时可使用 `uv sync --locked --no-dev`，启动时也使用 `uv run --locked --no-dev bot.py ...`，避免重新安装开发依赖。

## ⚙️ 配置

程序默认从项目根目录下的 `config/` 读取配置，文件使用 UTF-8 编码。也可以通过 `--config-dir` 指定其他配置目录。`config/` 中的模板会被 Git 跟踪，真实私钥、验证码密钥和代理凭据请改放到仓库外的目录，再将该目录传给 `--config-dir`，或在提交前确保没有真实机密。

### `accounts.txt`

每行添加一个已授权的 EVM 私钥：

```text
0x1a2b3c4d5e6f7......
0x9f8e7d6c5b4a3......
...
```

### `sctg.txt`

脚本会将第一行读取为验证码识别服务的 API 密钥：

```text
YOUR_CAPTCHA_SOLVER_API_KEY
```

获取和配置 API Key：

1. 打开验证码识别服务网站 [sctg.xyz](https://sctg.xyz)，注册并登录账户。
2. 在账户控制台或 API 设置页面创建、查看或复制 API Key；如果服务要求充值或启用 Turnstile 服务，请先完成对应设置。
3. 将 API Key 单独放在 `config/sctg.txt` 第一行，不要添加引号或其他文字。

也可以通过环境变量 `TASTYCO_CAPTCHA_KEY` 提供密钥，其优先级高于文件：

```bash
export TASTYCO_CAPTCHA_KEY="YOUR_CAPTCHA_SOLVER_API_KEY"  # macOS / Linux / WSL
```

```powershell
$env:TASTYCO_CAPTCHA_KEY = "YOUR_CAPTCHA_SOLVER_API_KEY"  # Windows PowerShell
```

程序不会自动加载 `.env` 文件。请确认 API Key 对 Turnstile 任务有效，并妥善保管，不要提交到 Git、截图、日志或问题反馈中。

### `config/useragent.txt`

每行添加一个浏览器 User-Agent 字符串。脚本会去除行首空白，接受以 `Mozilla/5.0` 开头的条目，并自动去重；因此也兼容包含缩进 UA 字段的浏览器画像资料：

```text
Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36
Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36
```

获取真实 User-Agent 的常用方法：

1. 在 Chrome、Edge 或 Firefox 中打开任意网页，按 `F12` 打开开发者工具。
2. 切换到“控制台”（Console），执行：

   ```javascript
   navigator.userAgent
   ```

3. 复制返回的完整字符串，粘贴到 `config/useragent.txt`，每行放置一个值。

也可以在 macOS、Linux 或 WSL 的终端执行以下命令查看当前浏览器通常发送的 User-Agent：

```bash
curl -s https://httpbin.org/user-agent
```

Windows PowerShell 可使用：

```powershell
(Invoke-WebRequest -UseBasicParsing https://httpbin.org/user-agent).Content
```

建议优先使用实际运行环境中的浏览器值，并保持浏览器版本、操作系统与 User-Agent 内容一致；不要随意拼接不存在的版本号，也不要使用来自未知来源的指纹配置。

列表为空或没有有效条目时，程序会在发起网络请求前报错退出。

### `proxy.txt`（可选）

该文件每行接受一个代理地址。协议方案可省略；省略时，脚本默认使用 HTTP：

```text
192.0.2.10:8080
https://192.0.2.11:8443
socks5://username:password@192.0.2.12:1080
```

请妥善保管代理凭据，并仅使用您有权访问的基础设施。

### 邀请码（可选）

仅在设置环境变量 `TASTYCO_REF_CODE` 时尝试绑定邀请码。默认不绑定原作者或其他人的邀请码。

## ❇️ 使用方法

在项目目录中启动机器人：

```bash
uv run --locked bot.py
```

程序启动时会显示以下英文选项，分别表示“使用代理运行”和“不使用代理运行”：

```text
1. Run With Proxy
2. Run Without Proxy
```

启用代理模式后，程序还会询问是否自动轮换失效代理。完成首轮账户处理后，程序会等待次日或当日尚未到达的 **UTC 00:01（北京时间／新加坡时间 08:01）**，继续处理账户。

只执行一轮并直连：

```bash
uv run --locked bot.py --once --no-proxy
```

使用代理并在失败时轮换：

```bash
uv run --locked bot.py --proxy --rotate-proxy
```

使用 `--help` 查看参数。非交互环境必须指定 `--proxy` 或 `--no-proxy`，`--rotate-proxy` 必须与 `--proxy` 一起使用。程序不继承 `HTTP_PROXY` 等环境代理配置；验证码识别服务请求保持直连，账户 API 请求使用所选代理。

`--once` 成功退出码为 0，配置无效或账户处理失败为 1，命令参数错误为 2，Ctrl+C 中断为 130。需要手动完成或尚不符合条件的任务属于正常跳过。单个账户或单条任务数据出错时，会继续处理其余项目。网络请求有超时；Ctrl+C 时正在执行的线程请求可能需要等到请求结束或超时。

## 开发与验证

```bash
uv sync --locked
uv run --locked pytest
uv run --locked ruff check .
uv run --locked ruff format --check .
```

测试使用临时配置和模拟网络响应，不会操作真实账户。测试覆盖令牌解析、代理轮换、请求清理、敏感错误信息、任务状态、单次运行和 UTC 调度。

修改依赖时更新 `pyproject.toml` 并执行 `uv lock`，一起提交配置和锁文件。旧的 `requirements.txt` 已被替代；如需为其他工具导出，可运行：

```bash
uv export --locked --no-dev --format requirements-txt --output-file requirements.txt
```

## 运行说明

机器人使用已配置的钱包签署身份验证消息，并向 TastyCo API 发送请求。连接 Telegram 机器人或邀请真实用户等需要外部操作的任务类型，可能仍需手动完成。网络故障、无效凭据、令牌过期、任务不可用及验证码识别服务错误，都可能导致账户无法完成处理周期。

请勿使用本机器人操作您不拥有或未获明确授权管理的账户。请勿在议题、拉取请求、截图或聊天消息中分享终端输出、私钥、API 密钥、访问令牌、刷新令牌或包含身份验证信息的代理 URL。

## 安全

本仓库是公开仓库。**切勿将真实私钥、验证码服务凭据、代理密码、访问令牌或其他机密信息放入 Git 跟踪的文件中。** 如果曾经提交过任何机密信息，请立即撤销或轮换；在后续提交中删除文件并不会将其从 Git 历史记录中移除。

请使用 `config/` 或仓库外的配置目录，API 密钥也可通过环境变量提供。程序不会记录私钥解析错误的原始内容、HTTP 错误响应正文或网络异常中的完整请求 URL；访问令牌仅保留在进程内存中。

## 参与贡献

欢迎提交能够提升可靠性、可读性、文档质量或账户操作规范性的贡献。创建拉取请求前，请先在本地测试改动，确保提交中不含机密信息，说明行为变化的影响，并在配置或运行步骤发生变化时同步更新本 README。

## 支持

如需报告程序错误或文档问题，请创建 [GitHub Issue](https://github.com/yukiasuna15/tasty/issues)，并提供最小可复现说明。请勿在议题中包含凭据、私钥、令牌、代理密码或其他敏感数据。

## 许可证

本仓库目前尚未指定许可证。在添加许可证之前，源代码应视为**保留所有权利**，不得在适用权限范围之外重新分发或复用。

---

<div align="center">

由 [@yukiasuna15](https://github.com/yukiasuna15) 维护

[查看仓库](https://github.com/yukiasuna15/tasty) · [提交问题](https://github.com/yukiasuna15/tasty/issues)

</div>
