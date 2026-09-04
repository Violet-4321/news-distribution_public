# 每日中文新闻简报

[English](README.md) | **简体中文**

本项目生成过去 24 小时内高信息量的中文新闻简报。

它从 Google News RSS、GDELT、美联储货币政策 RSS 和 BLS 经济数据发布 RSS 中采集候选新闻，剔除明显低价值的内容、对相似标题去重，用大语言模型(OpenAI 兼容接口，也可切换 DeepSeek)对最强的新闻进行排序并用简体中文总结，同时附上 VIX 指数，最后渲染成适合手机阅读的 HTML 邮件并通过 SMTP 发送。

目标是质量而非数量。简报最多 10 条，5 分钟内可读完。

## 安装

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Windows PowerShell 下激活:

```powershell
.\.venv\Scripts\Activate.ps1
```

## 配置

复制示例环境文件并填入你的配置:

```bash
cp .env.example .env
```

必需变量:

```text
OPENAI_API_KEY=你的大模型API Key
OPENAI_MODEL=gpt-4o-mini
MAX_STORIES=10
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USER=你的SMTP用户名
EMAIL_PASSWORD=你的SMTP授权码(不是登录密码)
EMAIL_TO=收件人@example.com
EMAIL_FROM=发件人@example.com
# 可选：微信推送账号(见下文)
SERVERCHAN_SENDKEY=
```

`EMAIL_PASSWORD` 填 SMTP 授权码/应用专用密码,不是账号登录密码(例如 QQ 邮箱授权码、Gmail 应用专用密码)。

## 微信推送(可选)

想让简报除了邮件外也推到微信,推荐用 [Server酱(方糖)](https://sct.ftqq.com),免费:

1. 打开 [sct.ftqq.com](https://sct.ftqq.com),用微信扫码登录,关注 Server酱 公众号
2. 复制你的 SendKey,填到 `.env` 的 `SERVERCHAN_SENDKEY=`(用 Actions 时也加到 GitHub Secret)
3. 工作流生成简报后,会在发送邮件之后把同样内容推到你的微信

免费额度每天若干条,足够一条日报加偶尔的重大事件提醒。(也兼容 `PUSHPLUS_TOKEN`,但该服务需要付费实名认证才能发送。)

## 重大事件即时提醒(可选)

`breaking_events.yml` 每小时运行一次,监控突发的历史性重大国际事件——例如某大国突然开战或发动大规模军事打击、核事故、灾难以外的全球性灾难等。检测到后立即通过微信推送。阈值非常严格:常规外交、孤立事件、已可预期的事件一律忽略,同一事件只提醒一次。

它使用和日报相同的 `OPENAI_*` 与微信推送密钥。已提醒的事件记录在 `state/notified_breaking.json`,14 天后自动清理。

## 用 DeepSeek 替代 OpenAI

管道使用 OpenAI SDK,该 SDK 兼容 DeepSeek 接口。切换时在 `.env` 设置:

```text
OPENAI_API_KEY=你的deepseek_api_key
OPENAI_BASE_URL=https://api.deepseek.com
OPENAI_MODEL=deepseek-v4-flash
```

`deepseek-v4-flash` 是非思考模式(已弃用 `deepseek-chat` 的继任者);想用思考模式就填 `deepseek-v4-pro`。若继续用 OpenAI,把 `OPENAI_BASE_URL` 留空、`OPENAI_MODEL` 填 `gpt-4o-mini` 即可。

通过 GitHub Actions 运行时,记得把 `OPENAI_BASE_URL` 也加到仓库 Secret。

## 本地测试

用 dry-run 生成 HTML 预览而不发邮件:

```bash
python -m src.main --dry-run
```

会生成 `daily_news_preview.html` 并打印采集数量。若没配 `OPENAI_API_KEY`,dry-run 仍会用本地启发式规则生成预览,便于验证采集、筛选、VIX 和排版。要获得高质量排序和中文摘要,请配置大模型 API。

本地发送邮件:

```bash
python -m src.main
```

## GitHub Secrets

在 GitHub 仓库里添加这些 Secret:

```text
OPENAI_API_KEY
OPENAI_BASE_URL
OPENAI_MODEL
MAX_STORIES
EMAIL_HOST
EMAIL_PORT
EMAIL_USER
EMAIL_PASSWORD
EMAIL_TO
EMAIL_FROM
SERVERCHAN_SENDKEY
PUSHPLUS_TOKEN
```

`OPENAI_MODEL` 首版可用 `gpt-4o-mini` 以节省成本。

## GitHub Actions 定时任务

工作流在 `.github/workflows/daily_news.yml`,已配置为每天北京时间 `20:00`(`12:00 UTC`)运行:

```yaml
on:
  schedule:
    - cron: "0 12 * * *"
  workflow_dispatch:
```

定时工作流可能比 cron 时间晚几分钟开始。你也可以从 Actions 标签页通过 `workflow_dispatch` 手动触发。要改时间就修改工作流里的 cron 表达式。简报覆盖过去 24 小时。

## 部署到自己的账号

1. 点击仓库顶部 Fork,把仓库复制到你自己的 GitHub 账号
2. 在 fork 的 Settings → Secrets and variables → Actions → New repository secret 中添加仓库密钥:`OPENAI_API_KEY`、`OPENAI_BASE_URL`、`OPENAI_MODEL`、`MAX_STORIES`、`EMAIL_HOST`、`EMAIL_PORT`、`EMAIL_USER`、`EMAIL_PASSWORD`、`EMAIL_TO`、`EMAIL_FROM`,以及可选的 `SERVERCHAN_SENDKEY`(Server酱 微信推送)
3. `daily_news.yml` 已配置每天北京时间 20:00 运行;可选的 `breaking_events.yml` 每小时检查重大国际事件。不想要就删掉对应文件或去掉 cron
4. 在 Actions 标签页手动运行一次验证,之后交给定时任务即可

提示:**公开**仓库免费无限 GitHub Actions 分钟;**私有**仓库免费账号每月仅 2,000 分钟,这套系统每小时监控可能接近该上限。

## 首个版本的限制

Google News RSS 的链接可能指向 Google 跳转地址而非直接来源。

系统只基于标题、摘要、来源和链接排序,不抓取正文,可降低大模型调用成本,但也可能漏掉细微信息。

GDELT 和 RSS 结果会因可用性和上游排序而波动。Google News RSS 的描述通常只是重复标题,因此仅凭标题的新闻会得到较短摘要,避免无依据的填充。

美联储和 BLS 数据源使用严格本地过滤,常规美联储纪要或较小经济数据变动不会自动进入候选池。

项目宁可舍弃弱新闻,也不为了凑数量而填充邮件。

## 许可证

[MIT](LICENSE)
