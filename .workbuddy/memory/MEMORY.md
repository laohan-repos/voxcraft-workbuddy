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
