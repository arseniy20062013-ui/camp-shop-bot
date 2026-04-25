import os
import requests
import base64
import subprocess
from io import BytesIO
from PIL import Image

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = "ТВОЙ_ТОКЕН"

# ===== ЛОКАЛЬНЫЕ СЕРВИСЫ =====
SD_URL = "http://127.0.0.1:7860/sdapi/v1/txt2img"
OLLAMA_URL = "http://localhost:11434/api/generate"

# ===== START =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 LUUM LOCAL\n\n"
        "/photo\n"
        "/video\n"
        "/doc\n"
        "Просто пиши для общения"
    )

# ===== ЧАТ (СВОЯ ИИ) =====
def ask_llm(prompt):
    r = requests.post(OLLAMA_URL, json={
        "model": "llama3",
        "prompt": prompt,
        "stream": False
    })
    return r.json()["response"]

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🧠 Думаю...")

    answer = ask_llm(update.message.text)

    await update.message.reply_text(answer)

# ===== ФОТО =====
async def photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = " ".join(context.args)

    if not prompt:
        await update.message.reply_text("Напиши промпт")
        return

    payload = {
        "prompt": prompt,
        "width": 1280,
        "height": 720,
        "steps": 20
    }

    r = requests.post(SD_URL, json=payload)
    result = r.json()

    img_data = base64.b64decode(result['images'][0])

    with open("img.png", "wb") as f:
        f.write(img_data)

    await update.message.reply_photo(photo=open("img.png", "rb"))

    os.remove("img.png")

# ===== ВИДЕО =====
async def video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = " ".join(context.args)

    await update.message.reply_text("🎬 Генерация (долго)...")

    frames = 30

    for i in range(frames):
        payload = {
            "prompt": f"{prompt}, frame {i}",
            "width": 1280,
            "height": 720,
            "steps": 15
        }

        r = requests.post(SD_URL, json=payload)
        result = r.json()

        img_data = base64.b64decode(result['images'][0])

        with open(f"frame_{i}.png", "wb") as f:
            f.write(img_data)

    subprocess.run([
        "ffmpeg",
        "-y",
        "-framerate", "3",
        "-i", "frame_%d.png",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "video.mp4"
    ])

    await update.message.reply_video(video=open("video.mp4", "rb"))

    for i in range(frames):
        os.remove(f"frame_{i}.png")
    os.remove("video.mp4")

# ===== DOC =====
async def doc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = " ".join(context.args) or "LUUM DOC"

    with open("doc.txt", "w", encoding="utf-8") as f:
        f.write(text)

    await update.message.reply_document(open("doc.txt", "rb"))

    os.remove("doc.txt")

# ===== MAIN =====
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("photo", photo))
    app.add_handler(CommandHandler("video", video))
    app.add_handler(CommandHandler("doc", doc))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

    print("🚀 LUUM LOCAL STARTED")
    app.run_polling()

if __name__ == "__main__":
    main()