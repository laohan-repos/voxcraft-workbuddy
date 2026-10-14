#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MiniMax 语音合成 (T2A v2) 测试脚本
- 遍历多个 endpoint / model 组合，找到可用配置
- 成功则把 hex 音频解码成 mp3 落盘
"""
import json
import os
import urllib.request
import urllib.error
import os
import binascii

# API Key 不再硬编码，运行时通过环境变量传入：
#   export MINIMAX_API_KEY="sk-cp-..."
API_KEY = os.environ.get("MINIMAX_API_KEY", "")
if not API_KEY:
    raise SystemExit("请先设置环境变量 MINIMAX_API_KEY")

OUT_DIR = os.path.dirname(os.path.abspath(__file__))

TEXT = "你好，这是MiniMax语音合成的接口测试。今天天气不错，适合出门走走。"

# 候选域名（国内 / 国际）
BASES = [
    "https://api.minimaxi.com",
    "https://api.minimax.chat",
    "https://api.minimaxi.chat",
]

# 候选模型（新 -> 旧）
MODELS = [
    "speech-2.6-hd",
    "speech-2.6-turbo",
    "speech-02-hd",
    "speech-02-turbo",
    "speech-01-turbo",
]

# 系统音色候选
VOICES = ["male-qn-qingse", "female-shaonv", "male-qn-jingying"]


def call(base, model, voice, group_id=None):
    url = f"{base}/v1/t2a_v2"
    if group_id:
        url += f"?GroupId={group_id}"

    payload = {
        "model": model,
        "text": TEXT,
        "stream": False,
        "voice_setting": {
            "voice_id": voice,
            "speed": 1.0,
            "vol": 1.0,
            "pitch": 0,
        },
        "audio_setting": {
            "sample_rate": 32000,
            "bitrate": 128000,
            "format": "mp3",
            "channel": 1,
        },
        "output_format": "hex",
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        body = resp.read().decode("utf-8")
    return json.loads(body)


def main():
    print("=" * 70)
    print("MiniMax TTS 接口测试")
    print("=" * 70)

    # 先拿一个组合做连通性探测
    for base in BASES:
        for model in MODELS:
            voice = VOICES[0]
            label = f"{base} | {model} | {voice}"
            try:
                data = call(base, model, voice)
            except urllib.error.HTTPError as e:
                err = e.read().decode("utf-8", "ignore")[:300]
                print(f"[HTTP {e.code}] {label}\n    -> {err}\n")
                continue
            except Exception as e:
                print(f"[ERR ] {label}\n    -> {type(e).__name__}: {e}\n")
                continue

            base_resp = data.get("base_resp", {})
            code = base_resp.get("status_code")
            msg = base_resp.get("status_msg")
            audio_hex = (data.get("data") or {}).get("audio")

            if code == 0 and audio_hex:
                print(f"[OK  ] {label}  ✅ 合成成功")
                out = os.path.join(OUT_DIR, f"tts_{model}.mp3")
                with open(out, "wb") as f:
                    f.write(binascii.unhexlify(audio_hex))
                size = os.path.getsize(out)
                extra = data.get("extra_info", {})
                print(f"        文件: {out}  ({size} bytes)")
                print(f"        音频信息: {extra.get('audio_length')}ms, "
                      f"{extra.get('audio_format')}, {extra.get('audio_sample_rate')}Hz")
                print(f"        trace_id: {data.get('trace_id')}")
                print()
                # 找到一个可用组合即可结束连通性探测
                return base, model
            else:
                print(f"[FAIL] {label}\n    -> code={code} msg={msg}\n")

    print("所有组合均失败")
    return None, None


if __name__ == "__main__":
    main()
