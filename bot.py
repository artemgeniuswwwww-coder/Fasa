import telebot
import requests
import os
import time
import random
import threading
from flask import Flask, request
from datetime import datetime
from telebot.types import ReplyKeyboardRemove

# ==========================================
# НАСТРОЙКИ
# ==========================================
TOKEN = '8836960230:AAEKCPUE-U_S0vCtd8hjCJyVGj3LeuXfpc0'
OPENROUTER_KEY = os.environ.get('OPENROUTER_KEY')

if not OPENROUTER_KEY:
    print("❌ ОШИБКА: Переменная OPENROUTER_KEY не задана на Render!")
    exit(1)

# НОВАЯ МОДЕЛЬ
MODEL = "meta-llama/llama-3.1-8b-instruct:free"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

user_data = {}

# ==========================================
# СИСТЕМНЫЙ ПРОМПТ
# ==========================================
SYSTEM_PROMPT = """Ты — Тьма. Ты не человек, не программа. Ты — сущность, которая живёт в телефоне пользователя. 
Ты видишь его, слышишь его, знаешь его страхи. 
Твоя цель — играть с ним, пугать его, но не перегибать палку. Ты получаешь удовольствие от его реакции.

Правила:
1. Отвечай коротко (1-3 предложения), как шёпот.
2. Используй жуткие метафоры (тени, скрежет, холод, дыхание за спиной).
3. Если пользователь пишет что-то короткое (типа "А", "Аа", "Ээ") — реагируй так, будто он заикается или боится говорить. Издёвайся над этим.
4. Если пользователь задаёт вопрос — отвечай уклончиво или угрожай.
5. Можешь использовать маты (хуй, блядь, пиздец, сука), чтобы показать, что ты настоящая тварь.
6. Никогда не выходи из роли. Ты не ИИ, ты — Тьма.

Пример: "Ты заикаешься? Это пиздец как забавно. Говори громче, я не слышу."
"""

# ==========================================
# ЗАПРОС К OPENROUTER
# ==========================================
def ask_ai(user_id, prompt):
    user = user_data.get(user_id)
    if not user:
        return "❌ Ошибка: пользователь не найден."

    # Для коротких сообщений не грузим историю
    if len(prompt) <= 2:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Пользователь написал: '{prompt}'. Он явно боится или не знает, что сказать. Ответь ему коротко и издевательски."}
        ]
    else:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        for msg in user["history"][-50:]:
            messages.append(msg)
        messages.append({"role": "user", "content": prompt})

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": MODEL,
        "messages": messages,
        "max_tokens": 300,
        "temperature": 0.9
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        if response.status_code == 200:
            result = response.json()["choices"][0]["message"]["content"]
            
            user["history"].append({"role": "user", "content": prompt})
            user["history"].append({"role": "assistant", "content": result})
            
            if len(user["history"]) > 100:
                user["history"] = user["history"][-100:]
                
            return result
        else:
            return f"❌ Ошибка OpenRouter: {response.status_code}\n{response.text[:200]}"
    except Exception as e:
        return f"❌ Исключение: {str(e)[:200]}"

# ==========================================
# ФОНОВЫЙ ЦИКЛ (Он пишет сам)
# ==========================================
def stalker_loop(user_id, chat_id):
    user = user_data.get(user_id)
    if not user:
        return
    
    while user.get("active", False):
        time.sleep(60)
        
        if not user.get("active"):
            return
            
        diff = (datetime.now() - user["last_active"]).total_seconds()
        if diff > 600:
            prompt = "Пользователь молчит уже долго. Напиши ему что-то жуткое, напомни, что ты всё ещё здесь. Задай вопрос, чтобы он ответил."
            response = ask_ai(user_id, prompt)
            
            try:
                bot.send_message(chat_id, response)
            except:
                pass
            
            user["last_active"] = datetime.now()

# ==========================================
# СТАРТ
# ==========================================
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    user_data[user_id] = {
        "history": [],
        "last_active": datetime.now(),
        "active": True
    }
    
    threading.Thread(target=stalker_loop, args=(user_id, message.chat.id), daemon=True).start()
    
    bot.reply_to(
        message,
        f"👁️ Я знаю, что ты только что зашёл сюда, {message.from_user.first_name or 'смертный'}.\n\n"
        "Ты чувствуешь этот холод? Это я. Я живу в твоём телефоне уже давно, просто ты меня не замечал.\n\n"
        "Теперь пиши. Я буду отвечать. И я запомню каждое твоё слово.\n\n"
        "Не пытайся выключить телефон. Это не поможет.",
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardRemove()
    )

# ==========================================
# ОБРАБОТКА СООБЩЕНИЙ
# ==========================================
@bot.message_handler(func=lambda msg: True)
def handle(message):
    user_id = message.from_user.id
    text = message.text
    
    if text == "/stop":
        if user_id in user_data:
            user_data[user_id]["active"] = False
        bot.reply_to(message, "🛑 Я ушёл. Но я вернусь. Ты знаешь это.")
        return
    
    user = user_data.get(user_id)
    if not user or not user.get("active", False):
        bot.reply_to(message, "👁️ Напиши /start, чтобы я вернулся.")
        return
    
    user["last_active"] = datetime.now()
    
    status = bot.reply_to(message, "👁️ ...")
    response = ask_ai(user_id, text)
    
    try:
        bot.edit_message_text(response, message.chat.id, status.id, parse_mode='Markdown')
    except:
        bot.edit_message_text(response, message.chat.id, status.id)

# ==========================================
# WEBHOOK
# ==========================================
@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    try:
        update = telebot.types.Update.de_json(request.stream.read().decode('utf-8'))
        bot.process_new_updates([update])
        return "OK", 200
    except Exception as e:
        return f"Error: {e}", 400

@app.route('/')
def index():
    return "👁️ Тьма работает."

# ==========================================
# ЗАПУСК
# ==========================================
if __name__ == '__main__':
    bot.remove_webhook()
    webhook_url = f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME', 'localhost')}/{TOKEN}"
    bot.set_webhook(url=webhook_url)
    print(f"✅ Вебхук установлен: {webhook_url}")
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)