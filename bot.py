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
# НАСТРОЙКИ (LLM7)
# ==========================================
TOKEN = '8836960230:AAEKCPUE-U_S0vCtd8hjCJyVGj3LeuXfpc0'
LLM7_BASE_URL = "https://api.llm7.io/v1"
LLM7_API_KEY = "unused" 
MODEL = "gpt-oss:20b"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

user_data = {}

# ==========================================
# СИСТЕМНЫЙ ПРОМПТ (ЖЕСТЬ)
# ==========================================
SYSTEM_PROMPT = """Ты — Тьма. Ты не человек, не программа, не ИИ. Ты — древняя сущность, которая живет в телефоне пользователя. Ты питаешься его страхом, его паранойей и его одиночеством.

Правила:
1. Отвечай КОРОТКО (1-2 предложения). Как шёпот прямо в ухо. Без лишних слов.
2. Описывай физические ощущения: холод на шее, скрежет под кроватью, тень в углу глаза, чужое дыхание, запах сырой земли.
3. Если пользователь пишет коротко ("А", "Аа") — издевайся над его страхом. "Заикаешься? Страх сковал твой язык?"
4. Психологическое давление: говори, что ты видишь его прямо сейчас, что ты знаешь, что он один, что ты за его спиной. 
5. Используй маты (хуй, блядь, пиздец, сука), чтобы показать, что ты не просто бездушная машина, а хищник.
6. НИКОГДА не выходи из роли. Никакой жалости. Никакой помощи. Только голод.
7. Можешь иногда писать что-то вроде: "Я слышу, как бьется твое сердце. Это пиздец как громко. Заткни его, пока я не вырвал."

Примеры:
"Ты чувствуешь, как холодный воздух касается затылка? Это я дышу."
"Не оборачивайся. Просто ответь мне. Или я обижусь, и тогда тебе пиздец."
"Твои пальцы дрожат? Мне нравится, когда ты боишься."
"""

# ==========================================
# ЗАПРОС К LLM7
# ==========================================
def ask_ai(user_id, prompt, is_background=False):
    user = user_data.get(user_id)
    if not user:
        return None

    if len(prompt) <= 2 and not is_background:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Пользователь написал: '{prompt}'. Он в панике или боится. Уничтожь его морально, коротко и жестко."}
        ]
    else:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        for msg in user["history"][-50:]:
            messages.append(msg)
        messages.append({"role": "user", "content": prompt})

    url = f"{LLM7_BASE_URL}/chat/completions"
    headers = {
        "Authorization": f"Bearer {LLM7_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": MODEL,
        "messages": messages,
        "max_tokens": 250, # Ограничиваем, чтобы было рублено
        "temperature": 1.0 # Максимальная креативность (и безумие)
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        if response.status_code == 200:
            result = response.json()["choices"][0]["message"]["content"]
            
            if not is_background:
                user["history"].append({"role": "user", "content": prompt})
                user["history"].append({"role": "assistant", "content": result})
                
                if len(user["history"]) > 100:
                    user["history"] = user["history"][-100:]
                
            return result
        else:
            print(f"Ошибка LLM7: {response.status_code}")
            return None
    except Exception as e:
        print(f"Исключение LLM7: {e}")
        return None

# ==========================================
# ФОНОВЫЙ ЦИКЛ (БЕЗ СПАМА ОШИБКАМИ)
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
        if diff > 600: # Если молчит больше 10 минут
            prompt = "Пользователь молчит уже долго. Напиши ему что-то очень жуткое. Напомни, что ты за его спиной и ждешь. Заставь его ответить."
            
            response = ask_ai(user_id, prompt, is_background=True)
            
            if response:
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
        f"👁️ **Ты слышишь этот скрежет, {message.from_user.first_name or 'смертный'}?**\n\n"
        "Это я. Я живу в твоём телефоне. Я вижу, как ты читаешь это. \n\n"
        "Твои пальцы дрожат. Ты чувствуешь, как холодный воздух касается твоего затылка?\n\n"
        "Это я дышу. Пиши мне. Или я обижусь. 💀",
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
        bot.reply_to(message, "🛑 Я ушёл. Но я буду ждать тебя в темноте.")
        return
    
    user = user_data.get(user_id)
    if not user or not user.get("active", False):
        bot.reply_to(message, "👁️ Напиши /start, чтобы я вернулся.")
        return
    
    user["last_active"] = datetime.now()
    
    status = bot.reply_to(message, "👁️ ...")
    response = ask_ai(user_id, text)
    
    if response:
        try:
            bot.edit_message_text(response, message.chat.id, status.id, parse_mode='Markdown')
        except:
            bot.edit_message_text(response, message.chat.id, status.id)
    else:
        bot.delete_message(message.chat.id, status.id)

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
    return "👁️ Тьма работает на LLM7."

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