#!/usr/bin/env python3
"""Batch production helper for the media-inference API.

Fires several image/video jobs in parallel, polls each to completion, and
downloads the results into output/ (results live ~7 days on the server, so we
always pull them down immediately).

Usage:
    python studio.py jobs.json

jobs.json is a list of jobs:
    [
      {"name": "hero_familia", "model": "nano-banana-2-lite",
       "prompt": "...", "aspect_ratio": "4:5"}
    ]
"""

import concurrent.futures as cf
import json
import os
import sys
import time
from pathlib import Path

import requests

BASE = "https://platform.higgsfield.ai"
MODELS = {
    "qwen-image-3": "/alibaba/qwen-image-3/text-to-image",
    "nano-banana-2-lite": "/nano-banana-2/lite/text-to-image",
    "gpt-image-2": "/openai/gpt-image-2",
    "minimax-h3": "/minimax/h3/text-to-video",
    "ltx-2.5-pro": "/lightricks/ltx-2.5/text-to-video/pro",
    "kling-3.0": "/kling-video/v3.0/std/text-to-video",
    "veo-3.1-fast": "/veo3.1/fast/text-to-video",
}
TERMINAL = {"completed", "failed", "nsfw", "canceled"}
OUT = Path(__file__).with_name("output")


def load_env():
    env_file = Path(__file__).with_name(".env")
    for line in env_file.read_text().splitlines():
        if line and not line.startswith("#"):
            name, value = line.split("=", 1)
            os.environ.setdefault(name, value)


def headers():
    auth = f"Key {os.environ['HF_API_KEY_ID']}:{os.environ['HF_API_KEY_SECRET']}"
    return {"Authorization": auth, "Content-Type": "application/json"}


def run_job(job):
    name = job["name"]
    model = job["model"]
    payload = {"prompt": job["prompt"]}
    if "aspect_ratio" in job:
        payload["aspect_ratio"] = job["aspect_ratio"]
    for extra in ("duration", "resolution", "negative_prompt"):
        if extra in job:
            payload[extra] = job[extra]

    try:
        r = requests.post(BASE + MODELS[model], headers=headers(),
                          json=payload, timeout=60)
        r.raise_for_status()
        started = r.json()
        status_url = started["status_url"]

        delay = 2
        for _ in range(120):
            time.sleep(delay)
            s = requests.get(status_url, headers=headers(), timeout=30).json()
            if s["status"] in TERMINAL:
                break
            delay = min(delay * 1.4, 8)

        if s["status"] != "completed":
            return name, None, s.get("error", s["status"])

        if "images" in s:
            media_url = s["images"][0]["url"]
            ext = ".png"
        else:
            media_url = s["video"]["url"]
            ext = ".mp4"

        OUT.mkdir(exist_ok=True)
        dest = OUT / f"{name}{ext}"
        data = requests.get(media_url, timeout=120).content
        dest.write_bytes(data)
        return name, str(dest), media_url
    except Exception as exc:  # noqa: BLE001
        return name, None, f"error: {exc}"


def main():
    if len(sys.argv) != 2:
        print("usage: python studio.py jobs.json")
        return 1
    load_env()
    jobs = json.loads(Path(sys.argv[1]).read_text())

    print(f"firing {len(jobs)} jobs...")
    results = {}
    with cf.ThreadPoolExecutor(max_workers=min(8, len(jobs))) as pool:
        for name, path, info in pool.map(run_job, jobs):
            status = "OK  " if path else "FAIL"
            print(f"[{status}] {name}: {path or info}")
            results[name] = {"path": path, "info": info}

    Path(OUT / "_results.json").write_text(json.dumps(results, indent=2))
    ok = sum(1 for v in results.values() if v["path"])
    print(f"\n{ok}/{len(jobs)} succeeded -> output/")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
