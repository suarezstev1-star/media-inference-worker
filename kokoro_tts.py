import sys, json, numpy as np, soundfile as sf
import espeakng_loader
from phonemizer.backend.espeak.wrapper import EspeakWrapper
EspeakWrapper.set_library(espeakng_loader.get_library_path())
from kokoro import KPipeline
from misaki import espeak

txtfile, out = sys.argv[1], sys.argv[2]           # txtfile: one caption phrase per line
voice = sys.argv[3] if len(sys.argv) > 3 else "ef_dora"
lang  = sys.argv[4] if len(sys.argv) > 4 else "es-419"
speed = float(sys.argv[5]) if len(sys.argv) > 5 else 0.92
pause = float(sys.argv[6]) if len(sys.argv) > 6 else 0.24

phrases = [l.strip() for l in open(txtfile, encoding="utf-8") if l.strip()]
pipe = KPipeline(lang_code="e", repo_id="hexgrad/Kokoro-82M")
pipe.g2p = espeak.EspeakG2P(language=lang)
SR = 24000
gap = np.zeros(int(SR * pause), dtype=np.float32)
parts, timing, t = [], [], 0.0
# one chunk per line (KPipeline splits on \n+)
for res, phrase in zip(pipe("\n".join(phrases), voice=voice, speed=speed), phrases):
    a = np.asarray(res.audio if hasattr(res, "audio") else res[2], dtype=np.float32)
    d = len(a) / SR
    timing.append({"text": phrase, "start": round(t, 3), "end": round(t + d, 3)})
    parts += [a, gap]; t += d + pause
audio = np.concatenate(parts) if parts else np.zeros(1, dtype=np.float32)
sf.write(out, audio, SR)
json.dump(timing, open(out.rsplit(".", 1)[0] + ".json", "w"), ensure_ascii=False, indent=1)
print("wrote", out, round(len(audio)/SR, 2), "s |", len(timing), "phrases")
