import telebot
from telebot import types
import os

print("NEW VERSION RUNNING")

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

ADMIN_ID = 146998462  # сюда потом поставим твой Telegram ID

bot = telebot.TeleBot(TOKEN)

user_data = {}

@bot.message_handler(commands=['start'])
def start(message):

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    btn1 = types.KeyboardButton("Regular cleaning")
    btn2 = types.KeyboardButton("Deep cleaning")
    btn3 = types.KeyboardButton("Move out cleaning")

    markup.add(btn1, btn2, btn3)

    bot.send_message(
        message.chat.id,
        "Welcome to Cleaning Pros Team 🧼\n\nWhat type of cleaning do you need?",
        reply_markup=markup
    )

@bot.message_handler(func=lambda m: m.text in ["Regular cleaning","Deep cleaning","Move out cleaning"])
def cleaning_type(message):

    chat_id = message.chat.id

    user_data[chat_id] = {}
    user_data[chat_id]["cleaning"] = message.text

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    btn1 = types.KeyboardButton("1 bedroom")
    btn2 = types.KeyboardButton("2 bedroom")
    btn3 = types.KeyboardButton("3 bedroom")
    btn4 = types.KeyboardButton("4+ bedroom")

    markup.add(btn1, btn2, btn3, btn4)

    bot.send_message(chat_id,"How many bedrooms?",reply_markup=markup)

@bot.message_handler(func=lambda m: "bedroom" in m.text)
def bedrooms(message):

    chat_id = message.chat.id
    user_data[chat_id]["bedrooms"] = message.text

    bot.send_message(chat_id,"Send your address")

@bot.message_handler(func=lambda m: True)
def address(message):

    chat_id = message.chat.id

    if "address" not in user_data[chat_id]:

        user_data[chat_id]["address"] = message.text

        bot.send_message(chat_id,"Send your phone number")

    else:

        user_data[chat_id]["phone"] = message.text

        data = user_data[chat_id]

        text = f"""
NEW CLEANING REQUEST

Cleaning: {data['cleaning']}
Bedrooms: {data['bedrooms']}
Address: {data['address']}
Phone: {data['phone']}
"""

        bot.send_message(ADMIN_ID,text)

        bot.send_message(chat_id,"✅ Thank you! Your request has been sent.")

        del user_data[chat_id]

bot.infinity_polling()
