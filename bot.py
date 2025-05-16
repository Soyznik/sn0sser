
import telebot
import threading
import time
import random
import re
import json
from datetime import datetime, timedelta

TOKEN = "7972756138:AAEltSgPcSWzzbjNWgjfRtBybvJ8uRX5D-A"
ADMIN_ID = 7879105271

bot = telebot.TeleBot(TOKEN)

subscriptions_file = "subscriptions.json"
active_attacks = {}

def load_subscriptions():
    try:
        with open(subscriptions_file, "r") as f:
            data = json.load(f)
            for user_id in data:
                data[user_id]["expiry"] = datetime.fromisoformat(data[user_id]["expiry"])
            return data
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_subscriptions(subs):
    data_to_save = {}
    for user_id, sub in subs.items():
        data_to_save[user_id] = {"expiry": sub["expiry"].isoformat()}
    with open(subscriptions_file, "w") as f:
        json.dump(data_to_save, f)

subscriptions = load_subscriptions()

def is_subscription_active(user_id):
    user_id = str(user_id)
    if user_id in subscriptions:
        expiry = subscriptions[user_id]["expiry"]
        if expiry > datetime.now():
            return True
    return False

def get_subscription_expiry(user_id):
    user_id = str(user_id)
    if user_id in subscriptions:
        return subscriptions[user_id]["expiry"]
    return None

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    if is_subscription_active(user_id):
        expiry = get_subscription_expiry(user_id)
        bot.reply_to(message, f"Ваша подписка активна до {expiry.strftime('%Y-%m-%d %H:%M:%S')}.")
    else:
        bot.reply_to(message, "У вас нет активной подписки. Чтобы посмотреть доступные команды, напишите /help")

@bot.message_handler(commands=['help'])
def help_cmd(message):
    user_id = message.from_user.id
    text = (
        "Доступные команды:\n"
        "/start - Проверить подписку\n"
        "/help - Показать это сообщение\n"
        "/attack <ссылка_на_сообщение> - Запустить жалобы на сообщение (требуется подписка)\n"
        "/cancel - Отменить текущую атаку\n"
        "\nЧтобы купить подписку напишите в личные сообщения @mostardon\n"
    )
    if user_id == ADMIN_ID:
        text += (
            "\nАдминские команды:\n"
            "/sub <user_id> <дней> - Выдать подписку пользователю\n"
            "/subs - Показать список всех подписок\n"
        )
    bot.reply_to(message, text)

@bot.message_handler(commands=['sub'])
def sub(message):
    user_id = message.from_user.id
    if user_id != ADMIN_ID:
        bot.reply_to(message, "Команда доступна только администратору.")
        return

    args = message.text.split()
    if len(args) != 3:
        bot.reply_to(message, "Использование: /sub <user_id> <дней>")
        return

    target_id, days_str = args[1], args[2]

    if not target_id.isdigit() or not days_str.isdigit():
        bot.reply_to(message, "Ошибка: user_id и дни должны быть числами.")
        return

    days = int(days_str)
    expiry = datetime.now() + timedelta(days=days)
    subscriptions[target_id] = {"expiry": expiry}
    save_subscriptions(subscriptions)
    bot.reply_to(message, f"Подписка для {target_id} выдана на {days} дней (до {expiry.strftime('%Y-%m-%d %H:%M:%S')}).")

@bot.message_handler(commands=['subs'])
def subs_list(message):
    user_id = message.from_user.id
    if user_id != ADMIN_ID:
        bot.reply_to(message, "Команда доступна только администратору.")
        return

    if not subscriptions:
        bot.reply_to(message, "Список подписок пуст.")
        return

    sub_list = "Список подписок:\n"
    for uid, sub in subscriptions.items():
        expiry = sub["expiry"].strftime('%Y-%m-%d %H:%M:%S')
        sub_list += f"ID: {uid}, Истекает: {expiry}\n"

    bot.reply_to(message, sub_list)

@bot.message_handler(commands=['attack'])
def attack(message):
    user_id = message.from_user.id
    if not is_subscription_active(user_id):
        bot.reply_to(message, "У вас нет активной подписки. Чтобы купить — напишите в личные сообщения @mostardon")
        return
