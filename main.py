import telebot
from telebot import types
import os

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

ADMIN_ID = 123456789  # поставим твой Telegram ID

bot = telebot.TeleBot(TOKEN)

user_data = {}

prices = {
    "Regular cleaning": {"1":120,"2":150,"3":180,"4":220},
    "Deep cleaning": {"1":180,"2":220,"3":260,"4":300},
    "Move out cleaning": {"1":200,"2":250,"3":300,"4":350}
}

@bot.message_handler(commands=['start'])
def start(message):

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    btn1 = types.KeyboardButton("Regular cleaning")
    btn2 = types.KeyboardButton("Deep cleaning")
    btn3 = types.KeyboardButton("Move out cleaning")

    markup.add(btn1,btn2,btn3)

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

    markup.add("1 bedroom","2 bedroom","3 bedroom","4+ bedroom")

    bot.send_message(chat_id,"How many bedrooms?",reply_markup=markup)


@bot.message_handler(func=lambda m: "bedroom" in m.text)
def bedrooms(message):

    chat_id = message.chat.id

    bedrooms = message.text[0]

    user_data[chat_id]["bedrooms"] = bedrooms

    cleaning = user_data[chat_id]["cleaning"]

    price = prices[cleaning][bedrooms]

    user_data[chat_id]["price"] = price

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    location_btn = types.KeyboardButton("Send location 📍",request_location=True)

    markup.add(location_btn)

    bot.send_message(
        chat_id,
        f"Estimated price: ${price}\n\nSend your address or location",
        reply_markup=markup
    )


@bot.message_handler(content_types=['location'])
def location(message):

    chat_id = message.chat.id

    lat = message.location.latitude
    lon = message.location.longitude

    user_data[chat_id]["location"] = f"https://maps.google.com/?q={lat},{lon}"

    bot.send_message(chat_id,"Send your phone number")


@bot.message_handler(func=lambda m: True,content_types=['text'])
def text_handler(message):

    chat_id = message.chat.id

    if "phone" not in user_data.get(chat_id,{}):
        user_data[chat_id]["phone"] = message.text

        bot.send_message(chat_id,"You can send photos of the place")

    else:

        data = user_data[chat_id]

        text = f"""
🧼 NEW CLEANING REQUEST

Cleaning: {data['cleaning']}
Bedrooms: {data['bedrooms']}
Price: ${data['price']}

Location: {data.get('location','not sent')}

Phone: {data['phone']}
"""

        bot.send_message(ADMIN_ID,text)

        bot.send_message(chat_id,"✅ Thank you! Your request has been sent.")

        user_data.pop(chat_id)


@bot.message_handler(content_types=['photo'])
def photo(message):

    chat_id = message.chat.id

    bot.forward_message(ADMIN_ID,chat_id,message.message_id)

    bot.send_message(chat_id,"Photo received 👍")


bot.infinity_polling()
