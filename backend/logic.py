import os, requests
import assemblyai as aai
from dotenv import load_dotenv

load_dotenv()
aai.settings.api_key = os.getenv("ASSEMBLYAI_API_KEY")

class Recorder:
    def __init__(self):
        self.frames: list[bytes] = []
        self.channels = 1
        self.rate = 16000
        self.frames_per_buffer = 1024
        self.sample_size = 2
        self.output_file = r"C:\Users\KANNAN\Downloads\archive\ML\Translation_Transcription\backend\output.webm"
        self.recording = False

    def start(self):
        self.frames.clear()
        self.recording = True

    def stop(self):
        self.recording = False
        ok = self.save()
        if not ok:
            raise RuntimeError("No audio received")
        return self.output_file

    def add_chunk(self, chunk: bytes):
        if self.recording:
            self.frames.append(chunk)
            print("Chunk Appended")

    def save(self):
        print(f"Saving audio, chunks: {len(self.frames)}")
        if not self.frames:
            print("No audio frames received")
            return False

        with open(self.output_file, "wb") as f:
            for chunk in self.frames:
                f.write(chunk)
        print("Audio file saved:", self.output_file)
        return True


class Transcription:
    def __init__(self):
        self.config = aai.TranscriptionConfig(language_detection=True)
        self.transcriber = aai.Transcriber(config=self.config)
        self.output_file = r"C:\Users\KANNAN\Downloads\archive\ML\Translation_Transcription\backend\output.webm"

    def transcribe(self, audio_file):
        print("Transcribing...")
        if not os.path.exists(audio_file):
            raise FileNotFoundError(f"Audio file not found: {audio_file}")

        print("Audio file size:", os.path.getsize(audio_file))

        transcript = self.transcriber.transcribe(audio_file)
        if transcript.status == "error":
            print("Transcription error")
            return None
        else:
            print(f"Transcription complete, Result: {transcript.text}")
            return transcript.text, transcript.json_response['language_code']

class Translation:
    def __init__(self):
        self.transcriber = Transcription()
        key = os.getenv("TRANSLATE_API_KEY")
        self.headers = {"X-API-KEY": key,"Content-Type": "application/json"}
        self.url = "https://api.translateplus.io/v2/translate"

    async def translate_text(self, text, target_language, detected_lang):
        if text and detected_lang:
            print(f"Detected language: {detected_lang}")
            print(f"Target language: {target_language}")
            if detected_lang == target_language:
                translated = text
            else:
                print("Translating...")
                data = {"text": text, "source": detected_lang, "target": target_language}
                response = requests.post(self.url, headers=self.headers, json=data)
                result = response.json()
                translated = result['translations']['translation']

            if translated:
                print(f"Translation complete, Result: {translated}")
                return translated
            else:
                raise ValueError("Translation failed")
        else:
            raise ValueError("Transcription Error")