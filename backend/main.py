from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from logic import Recorder, Transcription, Translation
import json, asyncio

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

recorder = Recorder()
transcriber = Transcription()
translator = Translation()

@app.get("/")
def home():
    return FileResponse("static/index.html")

@app.get("/ping")
def ping():
    print("PING HIT")
    return {"status": "ok"}


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    print("Websocket Connected")
    await ws.accept()
    print("Device connected")

    try:
        while True:
            message = await ws.receive()

            if message["type"] == "websocket.disconnect":
                print("📴 Client disconnected")
                break

            if "bytes" in message:
                print(f"Received audio chunk:", len(message["bytes"]))
                recorder.add_chunk(message["bytes"])
            elif "text" in message:
                data = json.loads(message["text"])
                mode = data.get("mode")
                if mode == "transcribe":
                    action = data.get("action")

                    if action == "start":
                        recorder.start()
                    elif action == "stop":
                        wav = recorder.stop()
                        text, lang = transcriber.transcribe(audio_file=wav)

                        await ws.send_json({
                            "type": "transcription",
                            "text": text,
                            "language": lang
                        })
                elif mode == "translate":
                    action = data.get("action")
                    if action == "start":
                        recorder.start()
                    elif action == "stop":
                        target = data.get("target")
                        wav = recorder.stop()
                        text, detected_lang = transcriber.transcribe(audio_file=wav)
                        translated = await translator.translate_text(text=text, target_language=target, detected_lang=detected_lang)
                        await ws.send_json({
                            "type": "translation",
                            "text": translated,
                            "target_language": target
                        })
    except WebSocketDisconnect:
        print("WebSocket disconnected")