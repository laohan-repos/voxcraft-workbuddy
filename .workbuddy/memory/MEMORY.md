# 项目长期记忆 — voxcraft-workbuddy

## 安全硬约束（最高优先级，任何情况下不得违反）

- **禁止保存、缓存或落盘任何 API Key / 密钥 / 凭据。**
  - 不写配置文件、`.env`、脚本源码、日志、SKILL.md、记忆文件。
  - 每次调用必须由用户当场传入。
  - 不在回复中原样回显密钥（只显示前几位并打码）。
  - 用户若要求"记住密钥"，必须拒绝并说明原因。
- 该约束由用户于 2026-10-14 明确提出，适用于本项目所有 Skill 与脚本。

## 已有 Skill

### `minimax-tts`（MiniMax 语音合成）
- 位置：`.workbuddy/skills/minimax-tts/`
- 触发词：语音合成 / 文字转语音 / 生成配音 / TTS / minimax语音合成
- 入口：`scripts/tts.py`
- Key 传入：`--api-key` 或环境变量 `MINIMAX_API_KEY`（**无持久化**）
- 输出命名：`minimax_tts_{YYYYMMDD-HHMMSS}_{文本摘要}.mp3`，默认落在工作区目录
- 接口：`POST https://api.minimaxi.com/v1/t2a_v2`，`output_format=hex`
- 已知限制：RPM 限流（并发 >2 易触发）；文本上限 10000 字符

## 代码仓库

| 平台 | 地址 | 状态 |
|---|---|---|
| Gitee | `https://gitee.com/laohan_repos/voxcraft-workbuddy` | ✅ 已同步 |
| GitHub | `https://github.com/laohan-repos/voxcraft-workbuddy` | ✅ 已同步 |

- 两端的 `main` 均指向同一提交；GitHub 属主账号为 `laohan-repos`（个人账号，非组织）。
- **Gitee**：走 HTTPS，macOS 钥匙串已存 `oauth2` 令牌，`git push gitee main` 直接可用。
- **GitHub**：SSH 不可用（本机 `id_rsa` 绑定的是 `ead007`，对 `laohan-repos` 无写权限），
  须用 HTTPS + PAT，且**每次由用户当场传入**。

## 排错经验（GitHub 推送，已踩坑）

1. **不要用 `curl` 判断 GitHub 连通性** —— `curl https://github.com` 返回 `000`，
   但 `git ls-remote https://github.com/...` 实际完全正常。必须用 git 自身实测。
2. **环境依赖代理**：`http_proxy/https_proxy = http://127.0.0.1:64667`，
   git 自动读取。这是 HTTPS 能通的根本原因，**不要 unset 代理**。
3. **GitHub 的 git 端点只接受 Basic 认证，不支持 `Bearer`**：
   - ❌ `Authorization: Bearer <fine-grained-PAT>` → `remote: invalid credentials`
   - ✅ `Authorization: Basic base64("x-access-token:<PAT>")` → 成功
   - 标准做法（凭据不落盘）：
     ```bash
     AUTH=$(printf 'x-access-token:%s' "$TOK" | base64 | tr -d '\n')
     git -c http.extraHeader="Authorization: Basic $AUTH" \
         push "https://github.com/laohan-repos/voxcraft-workbuddy.git" main
     ```
4. SSH 隧道 `ssh.github.com:443` 本身可用，障碍只在账号身份不匹配。
