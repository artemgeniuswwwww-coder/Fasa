import telebot
import os
import random
import time
import threading
from flask import Flask, request
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta

TOKEN = '8836960230:AAEKCPUE-U_S0vCtd8hjCJyVGj3LeuXfpc0'

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# ==========================================
# БАЗЫ ДАННЫХ
# ==========================================
user_data = {}
game_state = {}

# ==========================================
# КОНТЕНТ: ДНЕВНИК (20+ ШАГОВ)
# ==========================================
DIARY_STEPS = {
    0: {
        "text": "🕯️ **Запись №1**\n\n*«Я нашёл этот дневник на чердаке старого дома. Он пахнет сыростью и... чем-то ещё. Кожа обложки холодная, будто её только что держали в морге.»*",
        "buttons": [("Открыть дневник", "go_1"), ("Бросить его", "quit")]
    },
    1: {
        "text": "🕯️ **Запись №2**\n\n*«Первая страница пуста. Вторая — тоже. Но когда я провёл пальцем по бумаге, я почувствовал, как что-то шевельнулось под кожей.»*",
        "buttons": [("Перелистнуть", "go_2"), ("Закрыть", "quit")]
    },
    2: {
        "text": "🕯️ **Запись №3**\n\n*«На третьей странице — каракули. Они похожи на... моё имя. Я не писал этого. Я никогда не был в этом доме. Почему моё имя здесь?»*",
        "buttons": [("Дальше", "go_3"), ("Закрыть", "quit")]
    },
    3: {
        "text": "🕯️ **Запись №4**\n\n*«Я слышу шорох за спиной. Но когда оборачиваюсь — никого. Только тень, которая движется чуть медленнее, чем должна.»*",
        "buttons": [("Обернуться", "go_4"), ("Не обращать внимания", "go_5")]
    },
    4: {
        "text": "🕯️ **Запись №5 (ветка А)**\n\n*«Я обернулся. В углу комнаты — фигура. Она не двигается. Она просто стоит и смотрит. И улыбается. У неё нет лица, но я знаю, что она улыбается.»*",
        "buttons": [("Спросить, кто она", "go_6"), ("Бежать", "go_7")]
    },
    5: {
        "text": "🕯️ **Запись №5 (ветка Б)**\n\n*«Я не обернулся. Но шорох стал громче. Теперь он прямо за спиной. Я чувствую холодное дыхание на шее.»*",
        "buttons": [("Всё-таки обернуться", "go_4"), ("Закрыть глаза", "go_8")]
    },
    6: {
        "text": "🕯️ **Запись №6**\n\n*«Я спросил: \"Кто ты?\" Фигура не ответила. Но в комнате стало холоднее. И я услышал голос — не снаружи, а внутри головы: \"Я — тот, кто всегда был рядом. Ты просто не замечал.\"»*",
        "buttons": [("Дальше", "go_9"), ("Закрыть дневник", "quit")]
    },
    7: {
        "text": "🕯️ **Запись №7**\n\n*«Я побежал. Дверь не открылась. Окно не разбилось. Я заперт здесь. С ней. С ним. С ними.»*",
        "buttons": [("Оглядеться", "go_9"), ("Сдаться", "quit")]
    },
    8: {
        "text": "🕯️ **Запись №8**\n\n*«Я закрыл глаза. Но я всё равно вижу. Оно внутри меня. Оно шепчет: \"Теперь ты — часть дневника.\"»*",
        "buttons": [("Открыть глаза", "go_9")]
    },
    9: {
        "text": "🕯️ **Запись №9**\n\n*«Страницы начали перелистываться сами. Одна за другой. Я вижу имена. Много имён. И моё — в самом конце. Оно ещё не написано. Но оно появится.»*",
        "buttons": [("Что это за имена?", "go_10"), ("Попытаться вырвать страницу", "go_11")]
    },
    10: {
        "text": "🕯️ **Запись №10**\n\n*«Имена... Это люди, которые нашли этот дневник до меня. Все они исчезли. Все до единого. Теперь я понимаю, почему дом был заброшен.»*",
        "buttons": [("Что мне делать?", "go_12"), ("Принять свою судьбу", "go_13")]
    },
    11: {
        "text": "🕯️ **Запись №11**\n\n*«Я попытался вырвать страницу. Бумага не поддалась. А из неё вырвалась рука — бледная, холодная — и схватила меня за запястье. Я вырвал руку. На коже остался след.»*",
        "buttons": [("Дальше", "go_12")]
    },
    12: {
        "text": "🕯️ **Запись №12**\n\n*«Дневник открылся на последней странице. Там написано: \"Ты — следующий. Но у тебя есть выбор. Закрой дневник и забудь. Или дочитай до конца — и узнай правду.\"»*",
        "buttons": [("Дочитать до конца", "go_14"), ("Закрыть дневник", "quit")]
    },
    13: {
        "text": "🕯️ **Запись №13 (концовка 1)**\n\n*«Я принял судьбу. Дневник закрылся сам. Но я знаю, что теперь я — часть его истории. И когда-нибудь кто-то найдёт этот дневник и увидит моё имя.»*",
        "buttons": [("В меню", "main_menu")]
    },
    14: {
        "text": "🕯️ **Запись №14**\n\n*«Я дочитал. Правда оказалась хуже, чем я думал. Дневник — это не книга. Это дверь. И я её открыл.»*",
        "buttons": [("Что за дверью?", "go_15"), ("Закрыть дверь", "go_16")]
    },
    15: {
        "text": "🕯️ **Запись №15**\n\n*«За дверью — ничего. Или всё сразу. Я вижу комнату, в которой сижу. И вижу себя, читающего этот дневник. Время сломалось.»*",
        "buttons": [("Дальше", "go_17")]
    },
    16: {
        "text": "🕯️ **Запись №16**\n\n*«Я закрыл дверь. Дневник захлопнулся. Но я всё ещё слышу шёпот. И я знаю, что дверь всегда будет рядом. Просто ждать.»*",
        "buttons": [("В меню", "main_menu")]
    },
    17: {
        "text": "🕯️ **Запись №17**\n\n*«Я понял, что этот дневник — ловушка. Но она работает не так, как я думал. Он не забирает тебя. Он показывает тебе, кем ты мог бы стать. И это страшнее.»*",
        "buttons": [("Дальше", "go_18")]
    },
    18: {
        "text": "🕯️ **Финальная запись**\n\n*«Дневник закрылся. Я сижу в комнате. Всё как обычно. Но я знаю — он всё ещё здесь. Он ждёт. И он не отпустит меня. Никогда.»*",
        "buttons": [("В меню", "main_menu")]
    },
}

# ==========================================
# КОНТЕНТ: НАБЛЮДАТЕЛЬ
# ==========================================
STALKER_MESSAGES = [
    "👁️ Я вижу, что ты сейчас читаешь это. У тебя мурашки?",
    "👁️ Ты был здесь {time} назад. Я ждал.",
    "👁️ Не оборачивайся. Пожалуйста.",
    "👁️ Ты написал {count} сообщений. Я всё помню.",
    "👁️ Я знаю, что ты сейчас улыбаешься. Мне это нравится.",
    "👁️ Ты один в комнате? Точно?",
    "👁️ Я слышал, как ты дышишь. Это было красиво.",
    "👁️ Почему ты перестал писать? Я скучал.",
    "👁️ Ты сейчас посмотрел в экран. Я тоже смотрю на тебя.",
    "👁️ Завтра в это же время я напишу снова. Жди.",
]

# ==========================================
# КОНТЕНТ: ИСПЫТАНИЕ
# ==========================================
TRIAL_WORDS = ["кошмар", "тьма", "крик", "призрак", "кровь", "страх", "проклятие", "тень"]
TRIAL_FAIL_MESSAGES = [
    "💀 Ты ошибся. Комната стала темнее.",
    "💀 Слышишь этот шёпот? Это они смеются.",
    "💀 Ты чувствуешь холод? Это не сквозняк.",
    "💀 Осталось меньше попыток. Ты чувствуешь?",
    "💀 Ещё одна ошибка — и ты останешься здесь.",
    "💀 Они уже рядом.",
]

# ==========================================
# КЛАВИАТУРА
# ==========================================
def main_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        KeyboardButton("🕯️ Дневник"),
        KeyboardButton("👁️ Наблюдатель"),
        KeyboardButton("💀 Испытание"),
        KeyboardButton("ℹ️ Помощь")
    )
    return markup

def diary_keyboard(buttons):
    markup = InlineKeyboardMarkup(row_width=2)
    btns = [InlineKeyboardButton(text, callback_data=data) for text, data in buttons]
    markup.add(*btns)
    return markup

# ==========================================
# СЛУЖЕБНЫЕ ФУНКЦИИ
# ==========================================
def get_user(user_id):
    if user_id not in user_data:
        user_data[user_id] = {
            "last_seen": datetime.now(),
            "messages": [],
            "story_step": 0,
            "blocked_until": None,
            "stalker_started": False,
        }
    return user_data[user_id]

def format_time_ago(dt):
    diff = datetime.now() - dt
    if diff.seconds < 60:
        return "секунды"
    elif diff.seconds < 3600:
        return f"{diff.seconds // 60} минут"
    else:
        return f"{diff.seconds // 3600} часов"

# ==========================================
# НАБЛЮДАТЕЛЬ
# ==========================================
def stalker_loop(user_id, chat_id):
    user = user_data.get(user_id)
    if not user or not user.get("stalker_started"):
        return
    
    while user.get("stalker_started"):
        time.sleep(random.randint(60, 180))
        if not user.get("stalker_started"):
            return
        
        try:
            time_ago = format_time_ago(user["last_seen"])
            count = len(user["messages"])
            msg = random.choice(STALKER_MESSAGES).format(time=time_ago, count=count)
            bot.send_message(chat_id, msg)
        except:
            pass

# ==========================================
# СТАРТ
# ==========================================
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    get_user(user_id)["stalker_started"] = False
    game_state[user_id] = {"mode": None, "data": {}}
    
    bot.reply_to(
        message,
        f"🕯️ **Привет, {message.from_user.first_name or 'смертный'}.**\n\n"
        "Ты попал в место, где не действуют обычные правила.\n\n"
        "Выбери свою судьбу:\n\n"
        "🕯️ **Дневник** — прочти то, что не должен был\n"
        "👁️ **Наблюдатель** — узнай, что за тобой следят\n"
        "💀 **Испытание** — проверь, сможешь ли ты выжить\n\n"
        "⬇️ Кнопки внизу 👇",
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
    user = get_user(user_id)
    user["last_seen"] = datetime.now()
    user["messages"].append(text)
    if len(user["messages"]) > 100:
        user["messages"] = user["messages"][-100:]
    
    if user.get("blocked_until") and datetime.now() < user["blocked_until"]:
        remaining = (user["blocked_until"] - datetime.now()).seconds
        bot.reply_to(message, f"💀 Ты проиграл. Приходи через {remaining} секунд.")
        return
    
    state = game_state.get(user_id, {"mode": None, "data": {}})
    
    # ГЛОБАЛЬНЫЕ
    if text == "/stop" or text == "🛑 Стоп":
        user["stalker_started"] = False
        game_state[user_id] = {"mode": None, "data": {}}
        bot.reply_to(message, "🛑 Игра остановлена. Но я всё ещё здесь...", reply_markup=main_keyboard())
        return
    
    if text == "ℹ️ Помощь" or text == "/help":
        bot.reply_to(
            message,
            "📖 **Что я умею:**\n\n"
            "🕯️ **Дневник** — интерактивная история\n"
            "👁️ **Наблюдатель** — бот следит за тобой\n"
            "💀 **Испытание** — игра на выживание\n\n"
            "⚠️ Бот может писать первым. Это часть игры.",
            parse_mode='Markdown',
            reply_markup=main_keyboard()
        )
        return
    
    # ДНЕВНИК
    if text == "🕯️ Дневник" or text == "/diary":
        user["story_step"] = 0
        step = DIARY_STEPS[0]
        bot.reply_to(message, step["text"], parse_mode='Markdown', reply_markup=diary_keyboard(step["buttons"]))
        return
    
    # НАБЛЮДАТЕЛЬ
    if text == "👁️ Наблюдатель" or text == "/stalker":
        user["stalker_started"] = True
        bot.reply_to(
            message,
            "👁️ **Он теперь наблюдает.**\n\n"
            "Он будет писать тебе. Не удивляйся, если он знает о тебе больше, чем ты думаешь.\n\n"
            "Чтобы остановить — напиши /stop",
            parse_mode='Markdown',
            reply_markup=main_keyboard()
        )
        threading.Thread(target=stalker_loop, args=(user_id, message.chat.id), daemon=True).start()
        return
    
    # ИСПЫТАНИЕ
    if text == "💀 Испытание" or text == "/trial":
        word = random.choice(TRIAL_WORDS)
        game_state[user_id] = {
            "mode": "trial",
            "data": {"word": word, "guessed": [], "wrong": 0, "max_wrong": 3}
        }
        bot.reply_to(
            message,
            f"💀 **Ты в комнате.**\n\n"
            f"У тебя **3 попытки**, чтобы угадать слово.\n"
            f"Ошибёшься 3 раза — останешься здесь.\n\n"
            f"Подсказка: это что-то из тьмы.\n\n"
            f"Слово: `{show_word(word, [])}`\n"
            f"Жизни: ❤️❤️❤️\n\n"
            "Пиши букву.",
            parse_mode='Markdown'
        )
        return
    
    # ЛОГИКА ИСПЫТАНИЯ
    if state["mode"] == "trial":
        data = state["data"]
        word = data["word"]
        guessed = data["guessed"]
        
        if len(text) > 1:
            if text.lower() == word:
                game_state[user_id] = {"mode": None, "data": {}}
                bot.reply_to(
                    message,
                    f"🎉 **Ты выбрался!**\n\nСлово было: **{word.upper()}**\n\nТы выжил. Но он всё ещё помнит тебя...",
                    parse_mode='Markdown',
                    reply_markup=main_keyboard()
                )
            else:
                data["wrong"] += 1
                if data["wrong"] >= data["max_wrong"]:
                    user["blocked_until"] = datetime.now() + timedelta(seconds=60)
                    game_state[user_id] = {"mode": None, "data": {}}
                    bot.reply_to(
                        message,
                        f"💀 **Ты проиграл.**\n\nСлово было: **{word.upper()}**\n\nТы остаёшься здесь на 60 секунд.",
                        parse_mode='Markdown'
                    )
                else:
                    fail = random.choice(TRIAL_FAIL_MESSAGES)
                    bot.reply_to(
                        message,
                        f"❌ Не то слово.\n\n{fail}\n\nЖизни: {'❤️' * (data['max_wrong'] - data['wrong'])}",
                        parse_mode='Markdown'
                    )
            return
        
        letter = text.lower()
        if not letter.isalpha():
            bot.reply_to(message, "🤔 Введи **одну** букву.")
            return
        
        if letter in guessed:
            bot.reply_to(message, "😏 Уже было.")
            return
        
        guessed.append(letter)
        data["guessed"] = guessed
        
        if letter in word:
            if all(c in guessed for c in word):
                game_state[user_id] = {"mode": None, "data": {}}
                bot.reply_to(
                    message,
                    f"🎉 **Ты выбрался!**\n\nСлово: **{word.upper()}**\n\nТы выжил. Но он всё ещё помнит тебя...",
                    parse_mode='Markdown',
                    reply_markup=main_keyboard()
                )
            else:
                bot.reply_to(
                    message,
                    f"✅ Есть буква **{letter.upper()}**!\n\n`{show_word(word, guessed)}`\nЖизни: {'❤️' * (data['max_wrong'] - data['wrong'])}",
                    parse_mode='Markdown'
                )
        else:
            data["wrong"] += 1
            if data["wrong"] >= data["max_wrong"]:
                user["blocked_until"] = datetime.now() + timedelta(seconds=60)
                game_state[user_id] = {"mode": None, "data": {}}
                bot.reply_to(
                    message,
                    f"💀 **Ты проиграл.**\n\nСлово было: **{word.upper()}**\n\nТы остаёшься здесь на 60 секунд.",
                    parse_mode='Markdown'
                )
            else:
                fail = random.choice(TRIAL_FAIL_MESSAGES)
                bot.reply_to(
                    message,
                    f"❌ Буквы **{letter.upper()}** нет.\n\n{fail}\n\n`{show_word(word, guessed)}`\nЖизни: {'❤️' * (data['max_wrong'] - data['wrong'])}",
                    parse_mode='Markdown'
                )
        return
    
    bot.reply_to(message, "🤔 Я не понял. Выбери кнопку внизу или /help", reply_markup=main_keyboard())

# ==========================================
# CALLBACK-КНОПКИ ДНЕВНИКА
# ==========================================
@bot.callback_query_handler(func=lambda call: True)
def diary_callback(call):
    user_id = call.from_user.id
    user = get_user(user_id)
    
    if call.data == "main_menu":
        bot.edit_message_text("🕯️ Возвращайся в меню.", call.message.chat.id, call.message.message_id)
        return
    
    if call.data == "quit":
        bot.edit_message_text("🕯️ Ты закрыл дневник. Но он запомнил тебя.", call.message.chat.id, call.message.message_id)
        return
    
    if call.data.startswith("go_"):
        step_num = int(call.data.split("_")[1])
        user["story_step"] = step_num
        
        if step_num not in DIARY_STEPS:
            bot.edit_message_text("🕯️ Конец истории.", call.message.chat.id, call.message.message_id)
            return
        
        step = DIARY_STEPS[step_num]
        bot.edit_message_text(
            step["text"],
            call.message.chat.id,
            call.message.message_id,
            parse_mode='Markdown',
            reply_markup=diary_keyboard(step["buttons"])
        )
        bot.answer_callback_query(call.id)
        return

# ==========================================
# ВСПОМОГАТЕЛЬНЫЕ
# ==========================================
def show_word(word, guessed):
    result = ""
    for char in word:
        if char in guessed:
            result += char + " "
        else:
            result += "_ "
    return result.strip()

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
    return "🕯️ Тёмный бот работает!"

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