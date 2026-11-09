import telebot
import os
import random
import time
from flask import Flask, request
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

TOKEN = '8836960230:AAEKCPUE-U_S0vCtd8hjCJyVGj3LeuXfpc0'

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# ==========================================
# БАЗА СЛОВ ДЛЯ ВИСЕЛИЦЫ
# ==========================================
WORDS = [
    "программирование", "телефон", "космос", "котлета", "автомобиль",
    "апельсин", "вселенная", "футбол", "шоколад", "библиотека",
    "медведь", "пингвин", "клавиатура", "солнце", "путешествие",
    "математика", "музыка", "искусство", "приключение", "технология"
]

# ==========================================
# СТАДИИ ВИСЕЛИЦЫ
# ==========================================
HANGMAN_STAGES = [
    "  +---+\n  |   |\n      |\n      |\n      |\n      |\n=========",
    "  +---+\n  |   |\n  O   |\n      |\n      |\n      |\n=========",
    "  +---+\n  |   |\n  O   |\n  |   |\n      |\n      |\n=========",
    "  +---+\n  |   |\n  O   |\n /|   |\n      |\n      |\n=========",
    "  +---+\n  |   |\n  O   |\n /|\\  |\n      |\n      |\n=========",
    "  +---+\n  |   |\n  O   |\n /|\\  |\n /    |\n      |\n=========",
    "  +---+\n  |   |\n  O   |\n /|\\  |\n / \\  |\n      |\n=========",
]

# ==========================================
# СОСТОЯНИЯ ИГР
# ==========================================
game_state = {}

def reset_state(user_id):
    game_state[user_id] = {"mode": None, "data": {}}

# ==========================================
# КЛАВИАТУРА
# ==========================================
def main_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        KeyboardButton("🎲 Кубик"),
        KeyboardButton("🪙 Монетка"),
        KeyboardButton("🔢 Случайное число"),
        KeyboardButton("🎯 Угадай число"),
        KeyboardButton("🪢 Виселица"),
        KeyboardButton("ℹ️ Помощь")
    )
    return markup

# ==========================================
# СТАРТ
# ==========================================
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    reset_state(user_id)
    
    bot.reply_to(
        message,
        f"👋 Привет, {message.from_user.first_name or 'друг'}!\n\n"
        "Я — **Игровой бот** 🎮. Умею:\n\n"
        "🎲 **Кубик** — брошу кубик (1–6)\n"
        "🪙 **Монетка** — орёл или решка\n"
        "🔢 **Случайное число** — от 1 до 100\n"
        "🎯 **Угадай число** — игра\n"
        "🪢 **Виселица** — угадай слово по буквам\n\n"
        "Выбирай кнопку внизу 👇",
        parse_mode='Markdown',
        reply_markup=main_keyboard()
    )

# ==========================================
# ОБРАБОТЧИК
# ==========================================
@bot.message_handler(func=lambda msg: True)
def handle(message):
    user_id = message.from_user.id
    text = message.text.strip()
    text_lower = text.lower()

    state = game_state.get(user_id, {"mode": None, "data": {}})

    # ==================================
    # ГЛОБАЛЬНЫЕ КОМАНДЫ
    # ==================================
    if text == "/stop":
        reset_state(user_id)
        bot.reply_to(message, "🛑 Игра остановлена. Возвращайся!", reply_markup=main_keyboard())
        return

    if text == "ℹ️ Помощь" or text == "/help":
        bot.reply_to(
            message,
            "📖 **Что я умею:**\n\n"
            "🎲 **Кубик** — анимация кубика\n"
            "🪙 **Монетка** — орёл/решка\n"
            "🔢 **Случайное число** — 1–100\n"
            "🎯 **Угадай число** — игра\n"
            "🪢 **Виселица** — угадай слово\n\n"
            "Команды:\n"
            "/dice — кубик\n"
            "/coin — монетка\n"
            "/random — число\n"
            "/guess — угадай число\n"
            "/hangman — виселица\n"
            "/stop — стоп",
            parse_mode='Markdown',
            reply_markup=main_keyboard()
        )
        return

    # ==================================
    # РАНДОМАЙЗЕР
    # ==================================
    if text == "🎲 Кубик" or text == "/dice":
        bot.send_dice(message.chat.id, emoji="🎲")
        return

    if text == "🪙 Монетка" or text == "/coin":
        msg = bot.reply_to(message, "🪙 Подбрасываю...")
        time.sleep(1)
        result = random.choice(["🦅 **Орёл!**", "🪙 **Решка!**"])
        bot.edit_message_text(result, message.chat.id, msg.id, parse_mode='Markdown')
        return

    if text == "🔢 Случайное число" or text == "/random":
        bot.reply_to(message, f"🔢 Случайное число: **{random.randint(1, 100)}**", parse_mode='Markdown')
        return

    # ==================================
    # ЗАПУСК ИГР
    # ==================================
    if text == "🎯 Угадай число" or text == "/guess":
        game_state[user_id] = {
            "mode": "guess",
            "data": {"secret": random.randint(1, 100), "attempts": 0}
        }
        bot.reply_to(
            message,
            "🎯 Я загадал число от **1 до 100**.\n"
            "Пиши числа — я скажу «больше/меньше».\n\n"
            "Выйти — /stop",
            parse_mode='Markdown'
        )
        return

    if text == "🪢 Виселица" or text == "/hangman":
        word = random.choice(WORDS)
        game_state[user_id] = {
            "mode": "hangman",
            "data": {"word": word, "guessed": [], "wrong": 0, "max_wrong": 6}
        }
        bot.reply_to(
            message,
            f"🪢 **Виселица началась!**\n\n"
            f"<code>{HANGMAN_STAGES[0]}</code>\n\n"
            f"Слово: `{show_word(word, [])}`\n"
            f"Жизни: {'❤️' * 6} (6)\n\n"
            "Пиши букву (например: `а`) или слово целиком.",
            parse_mode='HTML'
        )
        return

    # ==================================
    # ЛОГИКА ИГРЫ "УГАДАЙ ЧИСЛО"
    # ==================================
    if state["mode"] == "guess":
        try:
            guess = int(text)
        except ValueError:
            bot.reply_to(message, "🤔 Введи число от 1 до 100 или /stop")
            return
        
        if guess < 1 or guess > 100:
            bot.reply_to(message, "⚠️ От 1 до 100.")
            return
        
        secret = state["data"]["secret"]
        state["data"]["attempts"] += 1
        attempts = state["data"]["attempts"]
        
        if guess < secret:
            bot.reply_to(message, f"📈 Больше! (попытка {attempts})")
        elif guess > secret:
            bot.reply_to(message, f"📉 Меньше! (попытка {attempts})")
        else:
            if attempts <= 3:
                emoji = "🔥 Гений!"
            elif attempts <= 7:
                emoji = "😎 Отлично!"
            else:
                emoji = "😅 Наконец-то!"
            
            reset_state(user_id)
            bot.reply_to(
                message,
                f"🎉 **Угадал!** Число **{secret}**\n"
                f"{emoji} Попыток: **{attempts}**",
                parse_mode='Markdown',
                reply_markup=main_keyboard()
            )
        return

    # ==================================
    # ЛОГИКА ИГРЫ "ВИСЕЛИЦА"
    # ==================================
    if state["mode"] == "hangman":
        data = state["data"]
        word = data["word"]
        guessed = data["guessed"]
        
        # Слово целиком
        if len(text) > 1:
            if text_lower == word:
                reset_state(user_id)
                bot.reply_to(
                    message,
                    f"🎉 **Победа!** Ты угадал слово: **{word.upper()}**",
                    parse_mode='Markdown',
                    reply_markup=main_keyboard()
                )
            else:
                data["wrong"] += 1
                if check_lose(data, message):
                    return
                bot.reply_to(
                    message,
                    f"❌ Не то слово. Ошибок: {data['wrong']}/{data['max_wrong']}\n"
                    f"Жизни: {show_lives(data)}"
                )
            return
        
        # Буква
        letter = text_lower
        if not letter.isalpha():
            bot.reply_to(message, "🤔 Введи **одну** букву или слово целиком.")
            return
        
        if letter in guessed:
            bot.reply_to(message, "😏 Эту букву уже называли.")
            return
        
        guessed.append(letter)
        data["guessed"] = guessed
        
        if letter in word:
            if all(c in guessed for c in word):
                reset_state(user_id)
                bot.reply_to(
                    message,
                    f"🎉 **Победа!**\n\n"
                    f"Слово: **{word.upper()}**\n"
                    f"Ошибок: {data['wrong']}",
                    parse_mode='Markdown',
                    reply_markup=main_keyboard()
                )
            else:
                bot.reply_to(
                    message,
                    f"✅ Есть буква **{letter.upper()}**!\n\n"
                    f"<code>{HANGMAN_STAGES[data['wrong']]}</code>\n\n"
                    f"`{show_word(word, guessed)}`\n"
                    f"Жизни: {show_lives(data)}\n"
                    f"Буквы: {', '.join(sorted(guessed))}",
                    parse_mode='HTML'
                )
        else:
            data["wrong"] += 1
            if check_lose(data, message):
                return
            
            bot.reply_to(
                message,
                f"❌ Буквы **{letter.upper()}** нет.\n\n"
                f"<code>{HANGMAN_STAGES[data['wrong']]}</code>\n\n"
                f"`{show_word(word, guessed)}`\n"
                f"Жизни: {show_lives(data)}\n"
                f"Буквы: {', '.join(sorted(guessed))}",
                parse_mode='HTML'
            )
        return

    # ==================================
    # НЕИЗВЕСТНАЯ КОМАНДА
    # ==================================
    bot.reply_to(
        message,
        "🤔 Не понял. Выбери кнопку внизу или /help",
        reply_markup=main_keyboard()
    )

# ==========================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ==========================================
def show_word(word, guessed):
    result = ""
    for char in word:
        if char in guessed:
            result += char + " "
        else:
            result += "_ "
    return result.strip()

def show_lives(data):
    alive = data["max_wrong"] - data["wrong"]
    return "❤️" * alive + "🖤" * data["wrong"]

def check_lose(data, message):
    if data["wrong"] >= data["max_wrong"]:
        word = data["word"]
        user_id = message.from_user.id
        reset_state(user_id)
        bot.reply_to(
            message,
            f"💀 **Ты проиграл!**\n\n"
            f"<code>{HANGMAN_STAGES[6]}</code>\n\n"
            f"Слово было: **{word.upper()}**\n\n"
            "Хочешь ещё? Нажми «🪢 Виселица»",
            parse_mode='HTML',
            reply_markup=main_keyboard()
        )
        return True
    return False

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
    return "🎮 Игровой бот работает!"

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