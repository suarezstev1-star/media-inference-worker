#!/usr/bin/env python3
"""Mux a voiceover (and optional music bed) onto a finished commercial video.

Usage:
    python mux_audio.py VIDEO VOICE [MUSIC] OUT

- Freezes the video's last frame if the voiceover is longer, so nothing is cut.
- Ducks/ò fades the music under the voice and fades everything out at the end.
Outputs H.264 + AAC MP4 ready for social.
"""

import re
import subprocess
import sys
from pathlib import Path

import imageio_ffmpeg

FF = imageio_ffmpeg.get_ffmpeg_exe()


def duration(path):
    r = subprocess.run([FF, "-i", str(path)], capture_output=True, text=True)
    m = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", r.stderr)
    if not m:
        return None
    h, mi, s = m.groups()
    return int(h) * 3600 + int(mi) * 60 + float(s)


def main():
    if len(sys.argv) not in (4, 5):
        print("usage: python mux_audio.py VIDEO VOICE [MUSIC] OUT")
        return 1
    video, voice = sys.argv[1], sys.argv[2]
    music = sys.argv[3] if len(sys.argv) == 5 else None
    out = sys.argv[-1]

    vdur = duration(video) or 6.0
    adur = duration(voice) or vdur
    total = max(vdur, adur) + 0.4  # small tail

    inputs = ["-i", video, "-i", voice]
    if music:
        inputs += ["-i", music]

    # Video: slow it down (continuous motion) to match the voice; if that would
    # need more than 1.8x, stretch to the cap and freeze only the small remainder.
    factor = total / vdur if vdur else 1.0
    cap = 1.8
    if factor <= 1.02:
        vfilter = "[0:v]copy[v]"
    elif factor <= cap:
        vfilter = f"[0:v]setpts={factor:.4f}*PTS[v]"
    else:
        rem = total - vdur * cap
        vfilter = (f"[0:v]setpts={cap:.4f}*PTS,"
                   f"tpad=stop_mode=clone:stop_duration={max(0, rem):.2f}[v]")

    if music:
        afilter = (
            f"[1:a]volume=1.0[vo];"
            f"[2:a]volume=0.18,afade=t=out:st={total-1.2:.2f}:d=1.2[mus];"
            f"[vo][mus]amix=inputs=2:duration=first:dropout_transition=0[a]"
        )
    else:
        afilter = f"[1:a]afade=t=out:st={max(0, adur-0.4):.2f}:d=0.4[a]"

    fc = vfilter + ";" + afilter
    cmd = [FF, "-y", *inputs, "-filter_complex", fc,
           "-map", "[v]", "-map", "[a]",
           "-c:v", "libx264", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
           "-c:a", "aac", "-b:a", "192k", "-t", f"{total:.2f}", out]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stderr[-1500:])
        return 1
    print("saved", out, f"({total:.1f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
