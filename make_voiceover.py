#!/usr/bin/env python3
"""Generate the PoC voice-over clips with Gemini TTS.

Reads GEMINI_API_KEY from the environment. Writes vo/<name>.wav clips and
vo/durations.json (used by videodemo.rpy to size each scene's pause).
"""

import base64
import json
import os
import struct
import subprocess
import sys
import urllib.request

VOICE = "Kore"
MODEL = "gemini-2.5-flash-preview-tts"
STYLE = "Narrate in a clear, warm, engaging tech-demo narrator voice: "

LINES = [
    ("title", "Dynamic sprite lighting in Ren'Py, update. One sprite, one normal map, and now a depth map for real self-shadows."),
    ("plain", "This is the flat sprite, straight from the PNG. Plain Ren'Py."),
    ("shader", "And this is the same sprite going through the shader, with a neutral frontal light. Almost identical... until we move the light."),
    ("day", "Daylight. Warm light from the upper right, with a soft blue ambient from the sky. Notice the volume in the skirt pleats and the hair."),
    ("sunset", "Sunset. An orange, almost horizontal sun from the left. One side lights up, while the other falls into violet shadow."),
    ("night", "Night. Cold, faint moonlight, and a blue rim light outlining the silhouette against the dark."),
    ("top", "A harsh top light. A white spotlight straight overhead, with no ambient at all. Interrogation mood."),
    ("shadow_off", "And here is what's new. Same harsh top light, with self-shadows turned off. The skirt is lit, but the legs right under it are lit too. Nothing blocks the light."),
    ("shadow_on", "Self-shadows on. The shader now marches through a grayscale depth map towards the light. The skirt hem drops a real shadow band onto the thighs, the chin shadows the neck, and the hair shadows the shoulders."),
    ("below", "Light from below. The classic horror flashlight. And watch the shadows flip with it: now the skirt hem darkens the torso above it."),
    ("fire", "A campfire. A warm point light at her feet, with distance falloff and a flicker animated entirely in ATL. The point light reads the depth map too, so closer features really are closer to the flame."),
    ("orbit", "An orbiting light. The light direction spins around the character, and the self-shadows sweep across the body with it. The shader uniforms are interpolated directly by ATL, with no per-frame Python."),
    ("mouse", "And it's fully interactive. A point light following the mouse cursor in real time."),
    ("end", "Same PNG, same shader, and now real self-shadows from a depth map. Only the light changes. Full source code on GitHub, link in the description."),
]


def tts(key, text):
    body = json.dumps({
        "contents": [{"parts": [{"text": STYLE + text}]}],
        "generationConfig": {
            "responseModalities": ["AUDIO"],
            "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": VOICE}}},
        },
    }).encode()
    req = urllib.request.Request(
        "https://generativelanguage.googleapis.com/v1beta/models/%s:generateContent" % MODEL,
        data=body,
        headers={"x-goog-api-key": key, "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        d = json.load(r)
    part = d["candidates"][0]["content"]["parts"][0]["inlineData"]
    assert part["mimeType"].startswith("audio/L16"), part["mimeType"]
    return base64.b64decode(part["data"])


def write_wav(path, pcm, rate=24000):
    with open(path, "wb") as f:
        f.write(b"RIFF" + struct.pack("<I", 36 + len(pcm)) + b"WAVE")
        f.write(b"fmt " + struct.pack("<IHHIIHH", 16, 1, 1, rate, rate * 2, 2, 16))
        f.write(b"data" + struct.pack("<I", len(pcm)) + pcm)


def main():
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        sys.exit("GEMINI_API_KEY is not set")

    os.makedirs("vo", exist_ok=True)
    durations = {}

    for name, text in LINES:
        path = os.path.join("vo", name + ".wav")
        if not os.path.exists(path):
            pcm = tts(key, text)
            write_wav(path, pcm)
        out = subprocess.check_output(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "csv=p=0", path]).decode().strip()
        durations[name] = float(out)
        print("%-8s %5.2fs  %s" % (name, durations[name], text[:60]))

    with open(os.path.join("vo", "durations.json"), "w") as f:
        json.dump(durations, f, indent=2)


if __name__ == "__main__":
    main()
