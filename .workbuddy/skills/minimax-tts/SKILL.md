---
name: minimax-tts
description: MiniMax 语音合成（文本转语音 / TTS）。当用户请求"语音合成"、"文字转语音"、"把这段文字读出来"、"生成配音"、"做一段语音"、"minimax语音合成"、"TTS"时使用。输入文本和 API Key，调用 MiniMax T2A v2 接口生成 mp3 音频，并按固定命名规则保存到工作区目录。
agent_created: true
---

# MiniMax 语音合成

## 用途

把文本转成语音（TTS），调用 MiniMax 的 T2A v2 接口，输出 mp3/wav/flac/pcm
音频文件到工作区目录。支持音色、情绪、语速、音调、音量控制。

## 何时使用

在用户提出以下任一诉求时使用本技能：

- 把一段文字转成语音 / 配音 / 音频
- 生成旁白、有声内容、口播稿音频
- 批量把多段文本合成语音
- 明确提到 "MiniMax 语音合成"、"TTS"、"文字转语音"

**不适用**：语音识别（ASR，音频转文字）、音色克隆训练、实时流式对讲。

## 安全约束（最高优先级，不可绕过）

**本技能不保存、不缓存、不落盘任何密钥信息。**

- 每次调用都必须由**用户当场提供** API Key，没有可复用的缓存。
- 密钥只能通过 `--api-key` 参数或环境变量 `MINIMAX_API_KEY` 传入。
- **禁止**把 API Key 写进任何文件：不写配置文件、不写 `.env`、不写脚本源码、
  不写日志、不写 SKILL.md / references、不写记忆文件。
- **禁止**在回复中原样回显用户的 API Key（引用时只显示前几位并打码）。
- 脚本内部只在单次进程的内存中使用该密钥，进程结束即消失。

若用户要求"记住密钥"或"存起来下次用"，**必须拒绝**并说明本技能不提供此能力。

## 前置条件

每次执行前确认用户已提供 API Key：

1. 命令行参数 `--api-key sk-xxxx`
2. 环境变量 `MINIMAX_API_KEY`

若两者都没有，**先向用户索要**，不要凭空编造，也不要尝试从任何文件里翻找。

- 接口域名：`https://api.minimaxi.com`（国际站，已验证可用）
- 鉴权：`Authorization: Bearer <API_KEY>`
- 注意：`sk-cp-` 开头的新格式 Key **不需要** GroupId 参数。

## 如何使用

统一通过 `scripts/tts.py` 执行，不要另行现写调用代码。

```bash
# 基本用法：文本 + API Key 都要传
python3 scripts/tts.py "你好，这是语音合成测试。" --api-key sk-xxxx

# 指定音色和情绪
python3 scripts/tts.py "今天真是让人开心的一天！" --api-key sk-xxxx \
    --voice female-shaonv --emotion happy

# 调整语速（0.5~2.0）
python3 scripts/tts.py "语速测试一二三四五" --api-key sk-xxxx --speed 1.5

# 自定义文件名
python3 scripts/tts.py "开场白" --api-key sk-xxxx --name opening

# 长文本从管道读入
cat script.txt | python3 scripts/tts.py --api-key sk-xxxx --voice male-qn-jingying

# 输出到指定目录（默认=当前工作区目录）
python3 scripts/tts.py "测试" --api-key sk-xxxx --out-dir ./audio

# 列出全部系统音色（303 个）
python3 scripts/tts.py --list-voices

# 按关键词过滤音色（匹配 voice_id 与中文名）
python3 scripts/tts.py --list-voices 女
python3 scripts/tts.py --list-voices 御姐
python3 scripts/tts.py --list-voices cantonese
```

### 常用参数

| 参数 | 说明 | 默认 |
|---|---|---|
| `text` / `--text` | 要合成的文本（≤10000 字符） | 必填，或从 stdin 读 |
| `--api-key` | API Key，**每次必传** | 无缓存，缺失即报错 |
| `--voice` | 音色 ID | `male-qn-qingse` |
| `--model` | 模型 | `speech-2.6-hd` |
| `--emotion` | happy/sad/angry/fearful/disgusted/surprised/neutral | 不设置 |
| `--speed` | 语速 0.5~2.0 | `1.0` |
| `--pitch` | 音调 -12~12 | `0` |
| `--vol` | 音量 0.1~10 | `1.0` |
| `--format` | mp3/pcm/flac/wav | `mp3` |
| `--out-dir` | 输出目录 | 当前工作区目录 |
| `--name` | 自定义文件名（不含扩展名） | 自动生成 |

## 输出文件名规则

未指定 `--name` 时，按以下规则自动生成：

```
minimax_tts_{YYYYMMDD-HHMMSS}_{文本摘要}.mp3
```

- **时间戳**：本地时间，精确到秒，保证文件可排序、不覆盖
- **文本摘要**：取文本前 16 个字符，去掉空白与文件名非法字符
  （`\ / : * ? " < > |`），超长以 `…` 结尾；文本无有效字符时用 `audio`
- **重名处理**：同名时自动追加 `-2`、`-3` …

示例：

```
minimax_tts_20261014-093602_你好这是语音合成测试.mp3
minimax_tts_20261014-093618_今天真是让人开心的一天….mp3
```

## 执行后的回报格式

脚本会向 stdout 输出一段 JSON。**把其中的 `file` 路径告知用户，并用
`present_files` 打开音频**，同时简要说明时长、音色、耗时。

```json
{
  "ok": true,
  "file": "/path/to/workspace/minimax_tts_20261014-093602_你好….mp3",
  "duration_ms": 5400,
  "size_bytes": 88116,
  "model": "speech-2.6-hd",
  "voice": "male-qn-qingse",
  "elapsed_s": 1.02
}
```

失败时 `ok=false`，`error` 为原因，`hint` 为修复建议（若可映射）。

## 常见错误码

| code | 含义 | 处理 |
|---|---|---|
| 1004 | 鉴权失败 | 检查 API Key 是否正确、是否带 `Bearer ` 前缀 |
| 1008 | 余额不足 | 提醒用户充值 |
| 1026 | 内容安全审核不通过 | 调整文本后重试 |
| 2013 | 参数不合法 | 检查 model / voice_setting |
| 2054 | 音色不存在 | 用 `--list-voices` 查可用音色 |
| — | rate limit exceeded(RPM) | 触发每分钟限流，降并发 / 加间隔后重试 |

## 注意事项

- **密钥零持久化**：不生成任何配置文件，不在任何地方缓存 Key。
  每次执行都要用户重新提供。
- 单次文本上限 10000 字符；长文本单次非流式实测可正常返回，
  若遇超时可用 `--out-dir` 分段合成。
- **批量合成务必串行或 ≤2 并发**：实测 8 并发会触发
  `rate limit exceeded(RPM)`。
- 默认输出为 32kHz / 128kbps / 单声道 mp3。
- **选音色的唯一可靠方式是查 `references/voices.md` 或跑 `--list-voices`**。
  不要凭语感替换 ID 里的括号、空格或大小写（例如粤语主持的 ID 是
  `Cantonese_ProfessionalHost（F)` —— 左全是全角括号、右半是半角括号），
  写错会返回 `2054 voice id not exist`。
- 完整音色总表（303 个，含多语种）见 `references/voices.md`；
  机器可读版本见 `references/voices.json`（`--list-voices` 即读它）。
