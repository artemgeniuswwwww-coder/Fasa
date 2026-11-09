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

user_data = {}

# ==========================================
# ОЧЕРЕДИ ДЛЯ НЕПОВТОРЯЮЩИХСЯ СООБЩЕНИЙ
# ==========================================
stalker_questions_queue = []
stalker_yes_queue = []
stalker_no_queue = []
passive_messages_queue = []

def get_next_from_queue(queue, source_list):
    """Берёт следующий элемент из перемешанной очереди без повторов"""
    if not queue:
        queue.extend(source_list)
        random.shuffle(queue)
    return queue.pop(0)

# ==========================================
# ДНЕВНИК (25+ ШАГОВ, 5 КОНЦОВОК)
# ==========================================
DIARY_STEPS = {
    0: {"text": "🕯️ **Запись №1**\n\n*«Я нашёл этот дневник на чердаке старого дома. Он пахнет сыростью и... чем-то ещё. Кожа обложки холодная, будто её только что держали в морге.»*", "buttons": [("Открыть дневник", "go_1"), ("Бросить его", "quit")]},
    1: {"text": "🕯️ **Запись №2**\n\n*«Первая страница пуста. Вторая — тоже. Но когда я провёл пальцем по бумаге, я почувствовал, как что-то шевельнулось под кожей.»*", "buttons": [("Перелистнуть", "go_2"), ("Закрыть", "quit")]},
    2: {"text": "🕯️ **Запись №3**\n\n*«На третьей странице — каракули. Они похожи на... моё имя. Я не писал этого. Я никогда не был в этом доме. Почему моё имя здесь?»*", "buttons": [("Дальше", "go_3"), ("Закрыть", "quit")]},
    3: {"text": "🕯️ **Запись №4**\n\n*«Я слышу шорох за спиной. Но когда оборачиваюсь — никого. Только тень, которая движется чуть медленнее, чем должна.»*", "buttons": [("Обернуться", "go_4"), ("Не обращать внимания", "go_5")]},
    4: {"text": "🕯️ **Запись №5 (А)**\n\n*«Я обернулся. В углу комнаты — фигура. Она не двигается. Она просто стоит и смотрит. И улыбается. У неё нет лица, но я знаю, что она улыбается.»*", "buttons": [("Спросить, кто она", "go_6"), ("Бежать", "go_7")]},
    5: {"text": "🕯️ **Запись №5 (Б)**\n\n*«Я не обернулся. Но шорох стал громче. Теперь он прямо за спиной. Я чувствую холодное дыхание на шее.»*", "buttons": [("Всё-таки обернуться", "go_4"), ("Закрыть глаза", "go_8")]},
    6: {"text": "🕯️ **Запись №6**\n\n*«Я спросил: \"Кто ты?\" Фигура не ответила. Но в голове прозвучало: \"Я — тот, кто всегда был рядом. Ты просто не замечал.\"»*", "buttons": [("Дальше", "go_9"), ("Закрыть дневник", "quit")]},
    7: {"text": "🕯️ **Запись №7**\n\n*«Я побежал. Дверь не открылась. Окно не разбилось. Я заперт здесь. С ней. С ним. С ними.»*", "buttons": [("Оглядеться", "go_9"), ("Сдаться", "quit")]},
    8: {"text": "🕯️ **Запись №8**\n\n*«Я закрыл глаза. Но я всё равно вижу. Оно внутри меня. Оно шепчет: \"Теперь ты — часть дневника.\"»*", "buttons": [("Открыть глаза", "go_9")]},
    9: {"text": "🕯️ **Запись №9**\n\n*«Страницы начали перелистываться сами. Я вижу имена. Много имён. И моё — в самом конце. Оно ещё не написано. Но оно появится.»*", "buttons": [("Что это за имена?", "go_10"), ("Вырвать страницу", "go_11")]},
    10: {"text": "🕯️ **Запись №10**\n\n*«Это люди, которые нашли дневник до меня. Все они исчезли. Все до единого. Теперь я понимаю, почему дом был заброшен.»*", "buttons": [("Что мне делать?", "go_12"), ("Принять судьбу", "go_13")]},
    11: {"text": "🕯️ **Запись №11**\n\n*«Я попытался вырвать страницу. Из неё вырвалась рука и схватила меня за запястье. На коже остался след.»*", "buttons": [("Дальше", "go_12")]},
    12: {"text": "🕯️ **Запись №12**\n\n*«Дневник открылся на последней странице: \"Ты — следующий. Закрой и забудь, или дочитай и узнай правду.\"»*", "buttons": [("Дочитать", "go_14"), ("Закрыть", "quit")]},
    13: {"text": "🕯️ **Запись №13 (Конец 1: Судьба)**\n\n*«Я принял судьбу. Теперь я — часть истории. И когда-нибудь кто-то найдёт этот дневник и увидит моё имя.»*", "buttons": [("В меню", "main_menu")]},
    14: {"text": "🕯️ **Запись №14**\n\n*«Я дочитал. Дневник — это не книга. Это дверь. И я её открыл. За дверью — комната, в которой я сижу. И я вижу себя, читающего этот дневник.»*", "buttons": [("Что за дверью?", "go_15"), ("Закрыть дверь", "go_16")]},
    15: {"text": "🕯️ **Запись №15**\n\n*«За дверью — ничего. Или всё сразу. Время сломалось. И я понимаю — я всегда был здесь.»*", "buttons": [("Дальше", "go_17")]},
    16: {"text": "🕯️ **Запись №16 (Конец 2: Дверь)**\n\n*«Я закрыл дверь. Дневник захлопнулся. Но я всё ещё слышу шёпот. И я знаю, что дверь всегда будет рядом. Просто ждать.»*", "buttons": [("В меню", "main_menu")]},
    17: {"text": "🕯️ **Запись №17**\n\n*«Дневник — ловушка. Он не забирает тебя. Он показывает, кем ты мог бы стать. И это страшнее.»*", "buttons": [("Дальше", "go_18")]},
    18: {"text": "🕯️ **Запись №18**\n\n*«Я вижу ещё одну страницу. Она пуста. Но я знаю — это моя страница. И я должен её заполнить. Чем? Своей жизнью? Своей смертью? Или чем-то средним?»*", "buttons": [("Написать имя", "go_19"), ("Оставить пустой", "go_20")]},
    19: {"text": "🕯️ **Запись №19 (Конец 3: Имя)**\n\n*«Я написал своё имя. Дневник закрылся. И я почувствовал... облегчение. Теперь я часть истории. И я не один. Нас много. Мы все здесь.»*", "buttons": [("В меню", "main_menu")]},
    20: {"text": "🕯️ **Запись №20 (Конец 4: Пустота)**\n\n*«Я оставил страницу пустой. Дневник не закрылся. Он просто исчез. И я остался один. В пустой комнате. С пустой страницей. Навсегда.»*", "buttons": [("В меню", "main_menu")]},
    21: {"text": "🕯️ **Запись №21**\n\n*«Я вижу ещё одну фигуру. Она стоит в углу. Она не двигается. Но я знаю — она ждёт. Ждёт, когда я закрою дневник. Ждёт, когда я стану одним из них.»*", "buttons": [("Закрыть дневник", "go_22"), ("Заговорить с ней", "go_23")]},
    22: {"text": "🕯️ **Запись №22 (Конец 5: Тишина)**\n\n*«Я закрыл дневник. Фигура исчезла. Но я знаю — она вернётся. Когда я снова открою дневник. И я открою. Рано или поздно. Все открывают.»*", "buttons": [("В меню", "main_menu")]},
    23: {"text": "🕯️ **Запись №23**\n\n*«Я заговорил с ней. Она ответила. Её голос — как шёпот в пустой комнате. Она сказала: \"Ты не первый. И не последний. Но ты — единственный, кто спросил.\"»*", "buttons": [("Что это значит?", "go_24")]},
    24: {"text": "🕯️ **Финал**\n\n*«Дневник закрылся. Всё как обычно. Но я знаю — он всё ещё здесь. Он ждёт. И он не отпустит меня. Никогда.»*", "buttons": [("В меню", "main_menu")]},
}

# ==========================================
# НАБЛЮДАТЕЛЬ (ПАССИВНЫЙ)
# ==========================================
STALKER_PASSIVE = [
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
# СЛЕЖКА (ИНТЕРАКТИВ)
# ==========================================
STALKER_QUESTIONS = [
    "👁️ Ты один в комнате? Напиши «да» или «нет».",
    "👁️ Посмотри в окно. Что ты видишь? Напиши одно слово.",
    "👁️ Выйди на балкон. Ты видишь машину во дворе? Напиши «да» или «нет».",
    "👁️ Прислушайся. Ты слышишь шорох? Напиши «да» или «нет».",
    "👁️ Посмотри на дверь. Она открыта? Напиши «да» или «нет».",
    "👁️ Ты чувствуешь холод? Напиши «да» или «нет».",
    "👁️ Ты сейчас улыбаешься? Напиши «да» или «нет».",
    "👁️ Ты веришь, что я рядом? Напиши «да» или «нет».",
    "👁️ Ты боишься меня? Напиши «да» или «нет».",
    "👁️ Ты хочешь, чтобы я ушёл? Напиши «да» или «нет».",
]

STALKER_YES = ["👁️ Хорошо. Я тоже тебя вижу.", "👁️ Ты чувствуешь это? Я — да.", "👁️ Не бойся. Я не сделаю тебе больно. Пока что.", "👁️ Ты молодец. Продолжай.", "👁️ Я знал, что ты ответишь."]
STALKER_NO = ["👁️ Ты уверен? Я вижу иначе.", "👁️ Не ври мне. Я всё знаю.", "👁️ Ты думаешь, это поможет?", "👁️ Мне не нравится, когда мне лгут.", "👁️ Я подожду. Я умею ждать."]

# ==========================================
# КЛАВИАТУРА
# ==========================================
def main_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        KeyboardButton("🕯️ Дневник"),
        KeyboardButton("👁️ Наблюдатель"),
        KeyboardButton("🩸 Слежка"),
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
            "observer_active": False,
            "stalker_active": False,
            "last_question_time": None,
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
# ФОНОВЫЕ ЦИКЛЫ (БЕЗ ПОВТОРОВ)
# ==========================================
def observer_loop(user_id, chat_id):
    user = user_data.get(user_id)
    while user.get("observer_active"):
        time.sleep(random.randint(300, 900)) 
        if not user.get("observer_active"):
            return
        try:
            time_ago = format_time_ago(user["last_seen"])
            count = len(user["messages"])
            # Берём из очереди без повторов
            msg_template = get_next_from_queue(passive_messages_queue, STALKER_PASSIVE)
            msg = msg_template.format(time=time_ago, count=count)
            bot.send_message(chat_id, msg)
        except:
            pass

def stalker_loop(user_id, chat_id):
    user = user_data.get(user_id)
    while user.get("stalker_active"):
        time.sleep(random.randint(120, 240))
        if not user.get("stalker_active"):
            return
        # Берём вопрос из очереди без повторов
        q = get_next_from_queue(stalker_questions_queue, STALKER_QUESTIONS)
        user["last_question_time"] = datetime.now()
        try:
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("Да", callback_data="stalker_yes"), InlineKeyboardButton("Нет", callback_data="stalker_no"))
            bot.send_message(chat_id, q, reply_markup=markup)
        except:
            pass

# ==========================================
# СТАРТ
# ==========================================
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    user = get_user(user_id)
    user["observer_active"] = False
    user["stalker_active"] = False
    user["blocked_until"] = None
    
    bot.reply_to(
        message,
        f"🕯️ **Привет, {message.from_user.first_name or 'смертный'}.**\n\n"
        "Ты попал в место, где не действуют обычные правила.\n\n"
        "Выбери свою судьбу:\n\n"
        "🕯️ **Дневник** — прочти то, что не должен был\n"
        "👁️ **Наблюдатель** — он будет писать тебе в фоне\n"
        "🩸 **Слежка** — он будет задавать вопросы и ждать ответа\n\n"
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
        rem = (user["blocked_until"] - datetime.now()).seconds
        bot.reply_to(message, f"💀 Ты наказан. Приходи через {rem} секунд.")
        return
    
    # ГЛОБАЛЬНЫЕ
    if text == "/stop" or text == "🛑 Стоп":
        user["observer_active"] = False
        user["stalker_active"] = False
        bot.reply_to(message, "🛑 Игра остановлена. Но он всё ещё здесь...", reply_markup=main_keyboard())
        return
    
    if text == "ℹ️ Помощь" or text == "/help":
        bot.reply_to(
            message,
            "📖 **Что я умею:**\n\n"
            "🕯️ **Дневник** — интерактивная история\n"
            "👁️ **Наблюдатель** — он пишет в фоне\n"
            "🩸 **Слежка** — он задаёт вопросы (накажет за игнор)\n\n"
            "⚠️ Чтобы остановить — /stop",
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
    if text == "👁️ Наблюдатель" or text == "/observer":
        user["observer_active"] = True
        bot.reply_to(
            message,
            "👁️ **Наблюдатель включён.**\n\n"
            "Он будет писать тебе. Но не часто. Он умеет ждать.\n\n"
            "Чтобы остановить — /stop",
            parse_mode='Markdown',
            reply_markup=main_keyboard()
        )
        threading.Thread(target=observer_loop, args=(user_id, message.chat.id), daemon=True).start()
        return
    
    # СЛЕЖКА
    if text == "🩸 Слежка" or text == "/stalker":
        user["stalker_active"] = True
        bot.reply_to(
            message,
            "🩸 **Слежка началась.**\n\n"
            "Он будет задавать вопросы. Отвечай быстро, иначе он обидится.\n\n"
            "Чтобы остановить — /stop",
            parse_mode='Markdown',
            reply_markup=main_keyboard()
        )
        threading.Thread(target=stalker_loop, args=(user_id, message.chat.id), daemon=True).start()
        return
    
    bot.reply_to(message, "🤔 Я не понял. Выбери кнопку внизу или /help", reply_markup=main_keyboard())

# ==========================================
# CALLBACK-КНОПКИ
# ==========================================
@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    user_id = call.from_user.id
    user = get_user(user_id)
    
    # ДНЕВНИК
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
        bot.edit_message_text(step["text"], call.message.chat.id, call.message.message_id, parse_mode='Markdown', reply_markup=diary_keyboard(step["buttons"]))
        bot.answer_callback_query(call.id)
        return
    
    # СЛЕЖКА
    if call.data in ["stalker_yes", "stalker_no"]:
        if user.get("last_question_time"):
            elapsed = (datetime.now() - user["last_question_time"]).seconds
            if elapsed > 60:
                user["blocked_until"] = datetime.now() + timedelta(seconds=120)
                user["stalker_active"] = False
                bot.edit_message_text("💀 Ты слишком долго думал. Я обиделся. Другие режимы закрыты на 2 минуты.", call.message.chat.id, call.message.message_id)
                bot.answer_callback_query(call.id)
                return
        
        # БЕЗ ПОВТОРОВ
        if call.data == "stalker_yes":
            reaction = get_next_from_queue(stalker_yes_queue, STALKER_YES)
        else:
            reaction = get_next_from_queue(stalker_no_queue, STALKER_NO)
        bot.edit_message_text(f"{call.message.text}\n\n{reaction}", call.message.chat.id, call.message.message_id)
        bot.answer_callback_query(call.id)
        return

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