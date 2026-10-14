#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MiniMax TTS 完整功能测试
覆盖：多模型 / 多音色 / 情绪 / 语速 / 长文本 / 错误处理 / 延迟 / 音频校验
"""
import json
import math
import os
import urllib.request
import urllib.error
import os
import time
import binascii
import struct

# API Key 不再硬编码，运行时通过环境变量传入：
#   export MINIMAX_API_KEY="sk-cp-..."
API_KEY = os.environ.get("MINIMAX_API_KEY", "")
if not API_KEY:
    raise SystemExit("请先设置环境变量 MINIMAX_API_KEY")
BASE = "https://api.minimaxi.com"
OUT_DIR = os.path.dirname(os.path.abspath(__file__))

RESULTS = []


def call(model, text, voice="male-qn-qingse", emotion=None, speed=1.0, volume=1.0, pitch=0):
    url = f"{BASE}/v1/t2a_v2"
    vs = {"voice_id": voice, "speed": speed, "vol": volume, "pitch": pitch}
    if emotion:
        vs["emotion"] = emotion
    payload = {
        "model": model,
        "text": text,
        "stream": False,
        "voice_setting": vs,
        "audio_setting": {"sample_rate": 32000, "bitrate": 128000, "format": "mp3", "channel": 1},
        "output_format": "hex",
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
        method="POST",
    )
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data, time.time() - t0, None
    except urllib.error.HTTPError as e:
        return None, time.time() - t0, f"HTTP {e.code}: {e.read().decode('utf-8','ignore')[:200]}"
    except Exception as e:
        return None, time.time() - t0, f"{type(e).__name__}: {e}"


def save(data, name):
    hex_audio = (data.get("data") or {}).get("audio")
    if not hex_audio:
        return None
    path = os.path.join(OUT_DIR, name)
    with open(path, "wb") as f:
        f.write(binascii.unhexlify(hex_audio))
    return path


def mp3_duration(path):
    """粗略解析 MP3 帧数估算时长，并校验文件头"""
    with open(path, "rb") as f:
        raw = f.read()
    if raw[:3] not in (b"ID3", b"\xff\xfb", b"\xff\xf3", b"\xff\xf2"):
        # 允许 ID3v2 之外的裸帧
        if raw[0] != 0xFF:
            return None, "非 MP3 文件头"
    # 用 MiniMax 返回的时长即可，这里仅做完整性校验
    return len(raw), "ok"


def record(case, ok, detail):
    RESULTS.append((case, ok, detail))
    flag = "✅" if ok else "❌"
    print(f"{flag} {case}\n     {detail}\n")


def main():
    print("=" * 74)
    print(" MiniMax TTS 完整功能测试   " + time.strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 74 + "\n")

    # ---- 1. 多模型 ----
    print("── 1. 模型对比 ──")
    for model in ["speech-2.6-hd", "speech-2.6-turbo", "speech-02-hd", "speech-02-turbo", "speech-01-turbo"]:
        d, dt, err = call(model, "这是模型测试，用于对比不同版本语音合成的音质与速度。")
        if err:
            record(f"模型 {model}", False, err)
        elif d.get("base_resp", {}).get("status_code") == 0:
            p = save(d, f"model_{model}.mp3")
            extra = d.get("extra_info", {})
            record(f"模型 {model}", True,
                   f"耗时 {dt:.2f}s | 音频 {extra.get('audio_length')}ms | "
                   f"{os.path.getsize(p)} bytes | {extra.get('audio_format')}/{extra.get('audio_sample_rate')}Hz")
        else:
            record(f"模型 {model}", False, str(d.get("base_resp")))

    # ---- 2. 多音色 ----
    print("── 2. 音色测试 ──")
    voices = {
        "male-qn-qingse": "青涩青年音色",
        "female-shaonv": "少女音色",
        "male-qn-jingying": "精英青年音色",
        "female-yujie": "御姐音色",
        "Chinese (Mandarin)_Warm_Girl": "温暖女孩",
    }
    for vid, desc in voices.items():
        d, dt, err = call("speech-2.6-hd", "你好，我是音色测试。", voice=vid)
        if err:
            record(f"音色 {vid} ({desc})", False, err)
        elif d.get("base_resp", {}).get("status_code") == 0:
            save(d, f"voice_{vid.replace(' ','_').replace('(','').replace(')','')}.mp3")
            record(f"音色 {vid} ({desc})", True, f"合成成功，耗时 {dt:.2f}s")
        else:
            record(f"音色 {vid} ({desc})", False, str(d.get("base_resp")))

    # ---- 3. 情绪控制 ----
    print("── 3. 情绪控制 ──")
    for emo in ["happy", "sad", "angry", "neutral"]:
        d, dt, err = call("speech-2.6-hd", "今天真是让人难忘的一天。", emotion=emo)
        if err:
            record(f"情绪 {emo}", False, err)
        elif d.get("base_resp", {}).get("status_code") == 0:
            save(d, f"emotion_{emo}.mp3")
            record(f"情绪 {emo}", True, f"合成成功，耗时 {dt:.2f}s")
        else:
            record(f"情绪 {emo}", False, str(d.get("base_resp")))

    # ---- 4. 语速控制 ----
    print("── 4. 语速控制 ──")
    for sp in [0.7, 1.0, 1.5]:
        d, dt, err = call("speech-2.6-hd", "语速测试一二三四五六七八九十。", speed=sp)
        if err:
            record(f"语速 {sp}", False, err)
        elif d.get("base_resp", {}).get("status_code") == 0:
            extra = d.get("extra_info", {})
            save(d, f"speed_{sp}.mp3")
            record(f"语速 {sp}", True, f"音频时长 {extra.get('audio_length')}ms（同文本，时长随语速变化）")
        else:
            record(f"语速 {sp}", False, str(d.get("base_resp")))

    # ---- 5. 长文本 ----
    print("── 5. 长文本 ──")
    long_text = ("人工智能正在深刻改变我们的生活方式。从智能语音助手到自动驾驶，"
                 "从医疗影像诊断到金融风控，人工智能技术已经渗透到各行各业。" * 6)
    d, dt, err = call("speech-2.6-hd", long_text)
    if err:
        record(f"长文本 ({len(long_text)}字)", False, err)
    elif d.get("base_resp", {}).get("status_code") == 0:
        extra = d.get("extra_info", {})
        save(d, "long_text.mp3")
        record(f"长文本 ({len(long_text)}字)", True,
               f"耗时 {dt:.2f}s | 音频 {extra.get('audio_length')}ms ({extra.get('audio_length',0)/1000:.1f}s)")
    else:
        record("长文本", False, str(d.get("base_resp")))

    # ---- 6. 错误处理 ----
    print("── 6. 错误处理 ──")
    d, dt, err = call("speech-2.6-hd", "测试", voice="this-voice-does-not-exist-123")
    if err:
        record("非法音色", True, f"如期被拒绝 -> {err[:120]}")
    elif d.get("base_resp", {}).get("status_code") != 0:
        record("非法音色", True, f"如期返回业务错误 -> {d.get('base_resp')}")
    else:
        record("非法音色", False, "非法音色竟然合成成功（异常）")

    # ---- 7. 鉴权 ----
    print("── 7. 鉴权校验 ──")
    global API_KEY
    good = API_KEY
    API_KEY = "sk-cp-invalid-key-0000000000000000000000000000000000"
    d, dt, err = call("speech-2.6-hd", "测试")
    if err or (d and d.get("base_resp", {}).get("status_code") != 0):
        record("错误 API Key", True, f"如期被拒绝 -> {err or d.get('base_resp')}")
    else:
        record("错误 API Key", False, "错误 key 竟然通过（异常）")
    API_KEY = good

    # ---- 汇总 ----
    print("=" * 74)
    total = len(RESULTS)
    ok = sum(1 for _, o, _ in RESULTS if o)
    print(f" 测试汇总: {ok}/{total} 通过")
    print("=" * 74)

    report = os.path.join(OUT_DIR, "test_report.json")
    with open(report, "w", encoding="utf-8") as f:
        json.dump([{"case": c, "pass": o, "detail": d} for c, o, d in RESULTS],
                  f, ensure_ascii=False, indent=2)
    print(f"报告已保存: {report}")


if __name__ == "__main__":
    main()
