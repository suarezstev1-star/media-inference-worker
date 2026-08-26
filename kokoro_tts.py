import sys, numpy as np, soundfile as sf
import espeakng_loader
from phonemizer.backend.espeak.wrapper import EspeakWrapper
EspeakWrapper.set_library(espeakng_loader.get_library_path())
from kokoro import KPipeline
from misaki import espeak

text, out = sys.argv[1], sys.argv[2]
voice = sys.argv[3] if len(sys.argv) > 3 else "ef_dora"
lang  = sys.argv[4] if len(sys.argv) > 4 else "es-419"
speed = float(sys.argv[5]) if len(sys.argv) > 5 else 0.92   # slower = premium
pause = float(sys.argv[6]) if len(sys.argv) > 6 else 0.28   # sec between sentences

pipe = KPipeline(lang_code="e", repo_id="hexgrad/Kokoro-82M")
pipe.g2p = espeak.EspeakG2P(language=lang)
gap = np.zeros(int(24000 * pause), dtype=np.float32)
parts = []
for _, _, a in pipe(text, voice=voice, speed=speed):
    parts.append(np.asarray(a, dtype=np.float32)); parts.append(gap)
audio = np.concatenate(parts) if parts else np.zeros(1, dtype=np.float32)
sf.write(out, audio, 24000)
print("wrote", out, round(len(audio)/24000, 2), "s |", voice, lang, "spd", speed)
