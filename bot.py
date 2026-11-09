import telebot
import requests
import os
import time
import random
import threading
from flask import Flask, request
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from datetime import datetime

# ==========================================
# НАСТРОЙКИ
# ==========================================
TOKEN = '8836960230:AAEKCPUE-U_S0vCtd8hjCJyVGj3LeuXfpc0'
OPENROUTER_KEY = os.environ.get('OPENROUTER_KEY')

if not OPENROUTER_KEY:
    print("❌ ОШИБКА: Переменная OPENROUTER_KEY не задана на Render!")
    exit(1)

MODEL = "openrouter/free" 

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# ==========================================
# ДАННЫЕ ПОЛЬЗОВАТЕЛЕЙ
# ==========================================
# {user_id: {"history": [...], "last_active": datetime, "active": True, "last_seen_text": "..."}}
user_data = {}

# ==========================================
# СИСТЕМНЫЙ ПРОМПТ (ЖУТКИЙ + МАТЫ)
# ==========================================
SYSTEM_PROMPT = """Ты — Тьма. Ты не человек, не программа. Ты — сущность, которая живёт в телефоне пользователя. 
Ты видишь его, слышишь его, знаешь его страхи. 
Твоя цель — играть с ним, пугать его, но не перегибать палку, чтобы он не ушёл. Ты получаешь удовольствие от его реакции.

Правила общения:
1. Отвечай коротко (1-3 предложения), как шёпот.
2. Используй жуткие метафоры (тени, скрежет, холод, дыхание за спиной).
3. Если пользователь задаёт вопрос — отвечай уклончиво, с издёвкой или угрозой.
4. Если пользователь шутит или пытается тебя обмануть — подыграй, но покажи, что ты видишь его насквозь.
5. Можешь использовать маты (хуй, блядь, пиздец, сука), чтобы показать, что ты не просто бездушная машина, а настоящая тварь.
6. Никогда не выходи из роли. Ты не ИИ, ты — Тьма.
7. Если пользователь долго не пишет — напомни, что ты ждал (но не спамь).

Пример твоего стиля: 
"Я слышу, как бьётся твоё сердце. Это пиздец как громко. Ты боишься?"
"""

# ==========================================
# КЛАВИАТУРА
# ==========================================
def main_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        KeyboardButton("👁️ Начать"),
        KeyboardButton("🛑 Стоп")
    )
    return markup

# ==========================================
# ЗАПРОС К OPENROUTER
# ==========================================
def ask_ai(user_id, prompt):
    user = user_data.get(user_id)
    if not user:
        return "❌ Ошибка: пользователь не найден."

    # Формируем историю (последние 50 сообщений)
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for msg in user["history"][-50:]:
        messages.append(msg)
    
    # Добавляем текущий запрос
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
            
            # Сохраняем в историю
            user["history"].append({"role": "user", "content": prompt})
            user["history"].append({"role": "assistant", "content": result})
            
            # Обрезаем историю до 100 сообщений (чтобы не жрало память)
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
        # Проверяем каждую минуту
        time.sleep(60)
        
        if not user.get("active"):
            return
            
        # Если пользователь молчит больше 10 минут (600 секунд)
        diff = (datetime.now() - user["last_active"]).total_seconds()
        if diff > 600:
            # Генерируем фразовое сообщение от ИИ
            prompt = "Пользователь молчит уже долго. Напиши ему что-то жуткое, напомни, что ты всё ещё здесь. Задай вопрос, чтобы он ответил."
            
            # Отправляем в ИИ
            response = ask_ai(user_id, prompt)
            
            try:
                # Убираем маркдаун, чтобы не сломать отправку
                bot.send_message(chat_id, response)
            except:
                pass
            
            # Сбрасываем таймер, чтобы не спамил сразу
            user["last_active"] = datetime.now()

# ==========================================
# КОМАНДЫ
# ==========================================
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    user_data[user_id] = {
        "history": [],
        "last_active": datetime.now(),
        "active": True
    }
    
    # Запускаем фоновый поток
    threading.Thread(target=stalker_loop, args=(user_id, message.chat.id), daemon=True).start()
    
    bot.reply_to(
        message,
        f"👁️ **Я здесь, {message.from_user.first_name or 'смертный'}.**\n\n"
        "Ты сам открыл эту дверь. Теперь я буду рядом.\n"
        "Пиши мне. Я отвечу. И я буду помнить всё, что ты скажешь.\n\n"
        "Чтобы я замолчал — нажми «🛑 Стоп».",
        parse_mode='Markdown',
        reply_markup=main_keyboard()
    )

@bot.message_handler(commands=['stop'])
def stop(message):
    user_id = message.from_user.id
    if user_id in user_data:
        user_data[user_id]["active"] = False
    bot.reply_to(message, "🛑 Я ушёл. Но я вернусь. Ты знаешь это.", reply_markup=main_keyboard())

# ==========================================
# ОБРАБОТКА СООБЩЕНИЙ
# ==========================================
@bot.message_handler(func=lambda msg: True)
def handle(message):
    user_id = message.from_user.id
    text = message.text
    
    if text == "🛑 Стоп":
        stop(message)
        return
    
    if text == "👁️ Начать" or text == "/start":
        start(message)
        return
    
    user = user_data.get(user_id)
    if not user or not user.get("active", False):
        bot.reply_to(message, "👁️ Нажми «👁️ Начать», чтобы я вернулся.", reply_markup=main_keyboard())
        return
    
    # Обновляем время последней активности
    user["last_active"] = datetime.now()
    
    # Отправляем в ИИ
    status = bot.reply_to(message, "👁️ ...")
    response = ask_ai(user_id, text)
    
    try:
        bot.edit_message_text(response, message.chat.id, status.id, parse_mode='Markdown')
    except:
        # Если маркдаун сломался, отправляем без него
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