# voxcraft-workbuddy

一个 WorkBuddy 项目工作区，核心产出是 **MiniMax 语音合成 Skill**（文本转语音 / TTS）。

## 这个仓库里有什么

```
voxcraft-workbuddy/
├── .workbuddy/
│   ├── skills/minimax-tts/          # 技能本体
│   │   ├── SKILL.md                 # 触发条件、参数表、命名规则、错误码
│   │   ├── scripts/tts.py           # 核心合成脚本（单文件、零第三方依赖）
│   │   └── references/
│   │       ├── voices.md            # 303 个系统音色分组总表
│   │       └── voices.json          # 音色表机器可读版
│   └── memory/                      # 项目开发记录
├── minimax-tts-test/                # 接口测试产物
│   ├── test_tts.py                  # 连通性探测
│   ├── test_full.py                 # 完整功能测试（模型/音色/情绪/语速/错误处理）
│   └── *.mp3                        # 测试样本
├── audio/                           # --out-dir 参数示例输出
├── *.mp3                            # 合成样例
└── minimax-tts.zip                  # 可分发技能包
```

## 快速开始

技能入口是 `scripts/tts.py`，只依赖 Python 标准库。

```bash
# 基本合成（文本 + API Key）
python3 .workbuddy/skills/minimax-tts/scripts/tts.py "你好，这是语音合成测试。" \
    --api-key "sk-cp-xxxxxxxx"

# 指定音色与情绪
python3 .workbuddy/skills/minimax-tts/scripts/tts.py "今天真是让人开心的一天！" \
    --api-key "sk-cp-xxxxxxxx" --voice female-shaonv --emotion happy

# 列出全部音色（303 个），支持关键词过滤
python3 .workbuddy/skills/minimax-tts/scripts/tts.py --list-voices
python3 .workbuddy/skills/minimax-tts/scripts/tts.py --list-voices 御姐

# 输出到指定目录 / 自定义文件名
python3 .workbuddy/skills/minimax-tts/scripts/tts.py "测试" \
    --api-key "sk-cp-xxxxxxxx" --out-dir ./audio --name demo
```

### 输出命名规则

```
minimax_tts_{YYYYMMDD-HHMMSS}_{文本摘要}.mp3
```

- 时间戳精确到秒，文件天然按时间排序、互不覆盖
- 文本摘要取前 16 字，剔除空白与文件名非法字符（`\ / : * ? " < > |`），
  超长以 `…` 结尾
- 重名自动追加 `-2`、`-3`
- 默认输出到当前工作区目录

## 参数速查

| 参数 | 说明 | 默认 |
|---|---|---|
| `text` / `--text` | 要合成的文本（≤10000 字符） | 必填，或从 stdin 读 |
| `--api-key` | API Key，**每次必传，不落盘** | 无缓存 |
| `--voice` | 音色 ID | `male-qn-qingse` |
| `--model` | 模型 | `speech-2.6-hd` |
| `--emotion` | happy/sad/angry/fearful/disgusted/surprised/neutral | 不设置 |
| `--speed` | 语速 0.5~2.0 | `1.0` |
| `--pitch` | 音调 -12~12 | `0` |
| `--vol` | 音量 0.1~10 | `1.0` |
| `--format` | mp3/pcm/flac/wav | `mp3` |
| `--out-dir` | 输出目录 | 当前工作区目录 |
| `--name` | 自定义文件名 | 自动生成 |
| `--list-voices [关键词]` | 列出音色表 | — |

## 安全约定

**本项目不保存、不缓存、不落盘任何密钥。**

- 每次调用都必须由用户当场传入 API Key（`--api-key` 或环境变量 `MINIMAX_API_KEY`）
- 不写配置文件、`.env`、脚本源码、日志或记忆文件
- 密钥只在单次进程内存中使用，进程结束即消失

## 实测结论

- **接口**：`POST https://api.minimaxi.com/v1/t2a_v2`，`output_format: "hex"`，
  返回体 `data.audio` 为 hex 编码，需解码后落盘
- **鉴权**：`sk-cp-` 开头的新格式 Key 不需要 GroupId 参数
- **可用模型**：`speech-2.6-hd`、`speech-2.6-turbo`、`speech-02-hd`、
  `speech-02-turbo`、`speech-01-turbo`
- **音色**：303 个系统音色，覆盖中文（含粤语）、英语、日语、韩语、西班牙语、
  葡萄牙语等 19 个语种
- **性能**：短文本 ~1s；360 字长文本（78 秒音频）约 2.5s
- **限流**：8 并发会触发 `rate limit exceeded(RPM)`，批量建议串行或 ≤2 并发
- **默认输出**：mp3 / 32kHz / 128kbps / 单声道

## 测试

```bash
export MINIMAX_API_KEY="sk-cp-xxxxxxxx"
cd minimax-tts-test
python3 test_full.py      # 完整功能测试，20 项用例
```

## License

MIT
