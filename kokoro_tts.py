import sys, numpy as np, soundfile as sf
import espeakng_loader
from phonemizer.backend.espeak.wrapper import EspeakWrapper
EspeakWrapper.set_library(espeakng_loader.get_library_path())
from kokoro import KPipeline
from misaki import espeak

text, out = sys.argv[1], sys.argv[2]
voice = sys.argv[3] if len(sys.argv) > 3 else "em_alex"
lang = sys.argv[4] if len(sys.argv) > 4 else "es-419"  # Latin American Spanish

pipe = KPipeline(lang_code="e", repo_id="hexgrad/Kokoro-82M")
pipe.g2p = espeak.EspeakG2P(language=lang)  # force Latino accent
chunks = [a for _, _, a in pipe(text, voice=voice)]
audio = np.concatenate(chunks) if chunks else np.zeros(1)
sf.write(out, audio, 24000)
print("wrote", out, round(len(audio)/24000, 2), "s |", voice, lang)
