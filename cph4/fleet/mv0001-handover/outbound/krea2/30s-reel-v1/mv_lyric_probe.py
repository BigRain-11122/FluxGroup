import sys

print("loading whisper model small ...", flush=True)
import whisper
model = whisper.load_model("small")
print("model loaded, loading audio ...", flush=True)

audio = whisper.load_audio(r"C:\Users\sjs20\Desktop\FluxGroup\cph4\fleet\mv0001-handover\audio\mv001_source_320k.mp3")
audio = audio[: 70 * 16000]
print("audio len:", len(audio) / 16000, "s; transcribing ...", flush=True)

result = model.transcribe(
    audio,
    language="zh",
    word_timestamps=True,
    verbose=False,
    initial_prompt="周杰伦《爱在西元前》歌词：古巴比伦王颁布了汉谟拉比法典，刻在黑色的玄武岩，距今已经三千七百多年。你在橱窗前凝视碑文的字眼，我却在旁静静欣赏你那张我深爱的脸。",
)

for seg in result["segments"]:
    words = " ".join(f"{w['word']}@{w['start']:.2f}" for w in seg.get("words", []))
    print(f"[{seg['start']:7.2f} - {seg['end']:7.2f}] {seg['text']}")
    if words:
        print(f"    WORDS: {words}")
print("DONE", flush=True)
