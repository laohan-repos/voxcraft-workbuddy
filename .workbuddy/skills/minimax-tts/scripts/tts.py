#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MiniMax 语音合成 (T2A v2) —— 文本转语音，输出 mp3 到工作区目录。

安全约定:
    每次调用都必须由用户传入 API Key（--api-key 或环境变量 MINIMAX_API_KEY）。
    本脚本不读取、不写入、不缓存任何密钥文件，密钥只存在于本次进程内存中。

用法示例:
    python3 tts.py "你好，这是语音合成测试。" --api-key sk-xxxx
    python3 tts.py --text "今天天气不错" --api-key sk-xxxx --voice female-shaonv --emotion happy
    python3 tts.py "语速测试" --api-key sk-xxxx --speed 1.5 --name my_demo
    echo "从管道读入文本" | python3 tts.py --api-key sk-xxxx --voice male-qn-jingying

文件名规则:
    minimax_tts_{YYYYMMDD-HHMMSS}_{文本摘要}.mp3
    例: minimax_tts_20261014-093602_你好这是语音合成测试.mp3
    同名冲突时自动追加 -2 / -3 ...
    可用 --name 覆盖为自定义文件名。
"""
import argparse
import binascii
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

DEFAULT_BASE_URL = "https://api.minimaxi.com"
DEFAULT_MODEL = "speech-2.6-hd"
DEFAULT_VOICE = "male-qn-qingse"

# 文本摘要最多保留多少字符
SLUG_MAX = 16
# 文件名中不允许出现的字符
ILLEGAL = r'[\\/:*?"<>|\r\n\t\x00-\x1f]'


# ---------------------------------------------------------------- API Key
def resolve_api_key(cli_key):
    """
    每次调用都必须由用户传入 API Key。

    优先级: --api-key > 环境变量 MINIMAX_API_KEY

    本脚本**不读取也不写入任何密钥文件**，不做任何持久化。
    密钥仅在本次进程内存中使用，进程结束即消失。
    """
    if cli_key:
        return cli_key.strip()
    return os.environ.get("MINIMAX_API_KEY", "").strip()


# ---------------------------------------------------------------- 文件名
def make_slug(text):
    """把文本压成适合做文件名的短摘要。"""
    s = re.sub(ILLEGAL, "", text)
    s = re.sub(r"\s+", "", s)
    s = s.strip("._- ")
    if not s:
        return "audio"
    slug = s[:SLUG_MAX]
    if len(s) > SLUG_MAX:
        slug += "…"
    # Windows/macOS 都不喜欢结尾的点
    return slug.rstrip(". ")


def build_filename(text, out_dir, name=None, ext="mp3"):
    """生成最终输出路径，自动避免覆盖已有文件。"""
    if name:
        base = os.path.splitext(name)[0]
    else:
        ts = time.strftime("%Y%m%d-%H%M%S")
        base = f"minimax_tts_{ts}_{make_slug(text)}"

    path = os.path.join(out_dir, f"{base}.{ext}")
    if not os.path.exists(path):
        return path
    i = 2
    while True:
        cand = os.path.join(out_dir, f"{base}-{i}.{ext}")
        if not os.path.exists(cand):
            return cand
        i += 1


# ---------------------------------------------------------------- 合成
def synthesize(api_key, text, model, voice, emotion, speed, pitch, vol,
               fmt, sample_rate, base_url, timeout=180):
    url = f"{base_url.rstrip('/')}/v1/t2a_v2"
    voice_setting = {"voice_id": voice, "speed": speed, "vol": vol, "pitch": pitch}
    if emotion and emotion != "none":
        voice_setting["emotion"] = emotion

    payload = {
        "model": model,
        "text": text,
        "stream": False,
        "voice_setting": voice_setting,
        "audio_setting": {
            "sample_rate": sample_rate,
            "bitrate": 128000,
            "format": fmt,
            "channel": 1,
        },
        "output_format": "hex",
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    t0 = time.time()
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data, time.time() - t0


# ---------------------------------------------------------------- 主流程
def main():
    p = argparse.ArgumentParser(
        description="MiniMax 语音合成 —— 文本转 mp3（输出到工作区目录）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("text", nargs="*", help="要合成的文本；省略则从 stdin 读取")
    p.add_argument("--text", dest="text_opt", help="要合成的文本（与位置参数二选一）")
    p.add_argument("--api-key", help="MiniMax API Key（必填）；也可用环境变量 MINIMAX_API_KEY")
    p.add_argument("--voice", default=DEFAULT_VOICE, help=f"音色 ID（默认 {DEFAULT_VOICE}）")
    p.add_argument("--model", default=DEFAULT_MODEL, help=f"模型（默认 {DEFAULT_MODEL}）")
    p.add_argument("--emotion", default=None,
                   help="情绪: happy/sad/angry/fearful/disgusted/surprised/neutral")
    p.add_argument("--speed", type=float, default=1.0, help="语速 0.5~2.0（默认 1.0）")
    p.add_argument("--pitch", type=int, default=0, help="音调 -12~12（默认 0）")
    p.add_argument("--vol", type=float, default=1.0, help="音量 0.1~10（默认 1.0）")
    p.add_argument("--format", default="mp3", choices=["mp3", "pcm", "flac", "wav"],
                   help="音频格式（默认 mp3）")
    p.add_argument("--sample-rate", type=int, default=32000, help="采样率（默认 32000）")
    p.add_argument("--out-dir", default=os.getcwd(),
                   help="输出目录（默认当前工作区目录）")
    p.add_argument("--name", help="自定义文件名（不含扩展名），覆盖默认命名规则")
    p.add_argument("--base-url", default=DEFAULT_BASE_URL, help="API 域名（一般无需修改）")
    p.add_argument("--list-voices", nargs="?", const="", default=None, metavar="关键词",
                   help="列出系统音色总表；可跟关键词过滤，如 --list-voices 女")
    args = p.parse_args()

    if args.list_voices is not None:
        return print_voices(args.list_voices)

    # 文本来源
    text = args.text_opt if args.text_opt else " ".join(args.text)
    if not text:
        if sys.stdin.isatty():
            p.error("未提供文本。请作为参数传入，或通过 stdin 管道输入。")
        text = sys.stdin.read()
    text = text.strip()
    if not text:
        p.error("文本为空。")
    if len(text) > 10000:
        p.error(f"文本过长（{len(text)} 字符），MiniMax 上限为 10000 字符。")

    api_key = resolve_api_key(args.api_key)
    if not api_key:
        print(json.dumps({
            "ok": False,
            "error": "缺少 API Key。每次调用都必须由你提供：用 --api-key 传入，"
                     "或设置环境变量 MINIMAX_API_KEY。",
            "note": "本技能不保存任何密钥，不存在缓存的 Key 可复用。",
        }, ensure_ascii=False))
        return 2

    out_dir = os.path.abspath(args.out_dir)
    os.makedirs(out_dir, exist_ok=True)

    try:
        data, elapsed = synthesize(
            api_key, text, args.model, args.voice, args.emotion,
            args.speed, args.pitch, args.vol, args.format,
            args.sample_rate, args.base_url,
        )
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "ignore")[:300]
        print(json.dumps({"ok": False, "error": f"HTTP {e.code}: {body}"},
                         ensure_ascii=False))
        return 1
    except Exception as e:
        print(json.dumps({"ok": False, "error": f"{type(e).__name__}: {e}"},
                         ensure_ascii=False))
        return 1

    base_resp = data.get("base_resp", {}) or {}
    if base_resp.get("status_code") not in (0, None):
        print(json.dumps({
            "ok": False,
            "error": base_resp.get("status_msg"),
            "status_code": base_resp.get("status_code"),
            "hint": ERROR_HINTS.get(base_resp.get("status_code"), ""),
            "trace_id": data.get("trace_id"),
        }, ensure_ascii=False))
        return 1

    audio_hex = (data.get("data") or {}).get("audio")
    if not audio_hex:
        print(json.dumps({"ok": False, "error": "接口未返回音频数据",
                          "trace_id": data.get("trace_id")}, ensure_ascii=False))
        return 1

    out_path = build_filename(text, out_dir, args.name, args.format)
    with open(out_path, "wb") as f:
        f.write(binascii.unhexlify(audio_hex))

    extra = data.get("extra_info", {}) or {}
    print(json.dumps({
        "ok": True,
        "file": out_path,
        "size_bytes": os.path.getsize(out_path),
        "duration_ms": extra.get("audio_length"),
        "format": extra.get("audio_format", args.format),
        "sample_rate": extra.get("audio_sample_rate", args.sample_rate),
        "model": args.model,
        "voice": args.voice,
        "emotion": args.emotion,
        "speed": args.speed,
        "text_chars": len(text),
        "elapsed_s": round(elapsed, 2),
        "trace_id": data.get("trace_id"),
    }, ensure_ascii=False, indent=2))
    return 0


# 音色总表（由 references/voices.json 提供，共 300+ 个系统音色）
VOICES_JSON = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "references", "voices.json",
)


def load_voices():
    """读取本地缓存的系统音色总表；缺失时返回空列表（不报错）。"""
    try:
        with open(VOICES_JSON, "r", encoding="utf-8") as f:
            return json.load(f).get("system_voice", [])
    except Exception:
        return []


def print_voices(keyword):
    voices = load_voices()
    if not voices:
        print("未找到音色表 references/voices.json。")
        return 0
    kw = (keyword or "").lower()
    hit = [v for v in voices
           if not kw or kw in v["voice_id"].lower() or kw in v["voice_name"].lower()]
    if not hit:
        print(f"没有匹配 “{keyword}” 的音色。")
        return 0
    width = max(len(v["voice_id"]) for v in hit) + 2
    for v in hit:
        print(f'{v["voice_id"]:<{width}}{v["voice_name"]}')
    print(f"\n共 {len(hit)} / {len(voices)} 个音色"
          + (f"（关键词：{keyword}）" if kw else ""))
    return 0


ERROR_HINTS = {
    1004: "鉴权失败：API Key 无效或未正确传递。",
    1008: "余额不足或账号未开通该模型。",
    1026: "文本触发了内容安全审核，请调整文本。",
    2013: "参数不合法，请检查 model / voice_setting 等字段。",
    2054: "音色 ID 不存在，请用 --list-voices 查看可用音色。",
}

if __name__ == "__main__":
    sys.exit(main())
