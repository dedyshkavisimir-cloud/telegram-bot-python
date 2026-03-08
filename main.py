import telebot
from telebot import types
import os
from datetime import datetime, timedelta
from reportlab.pdfgen import canvas

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_ID = 146998462

bot = telebot.TeleBot(TOKEN)

user_data = {}
bookings = {}

prices = {
    "Regular cleaning": {"1":120,"2":150,"3":180,"4":200},
    "Deep cleaning": {"1":180,"2":220,"3":260,"4":300},
    "Move out cleaning": {"1":200,"2":250,"3":300,"4":350}
}

extras_prices = {
    "Inside oven":25,
    "Inside fridge":45,
    "Pet hair":40
}

# START

@bot.message_handler(commands=['start'])
def start(message):

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    markup.add("Book cleaning")
    markup.add("Prices","Contact")

    bot.send_message(
        message.chat.id,
        "Welcome to Cleaning Pros Team 🧼",
        reply_markup=markup
    )

# BOOK CLEANING

@bot.message_handler(func=lambda m: m.text == "Book cleaning")
def choose_cleaning(message):

    chat_id = message.chat.id
    user_data[chat_id] = {}

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    markup.add("Regular cleaning","Deep cleaning")
    markup.add("Move out cleaning")

    bot.send_message(chat_id,"What type of cleaning do you need?",reply_markup=markup)

# CLEANING TYPE

@bot.message_handler(func=lambda m: m.text in prices)
def bedrooms(message):

    chat_id = message.chat.id
    user_data[chat_id]["cleaning"] = message.text

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("1","2","3","4")

    bot.send_message(chat_id,"How many bedrooms?",reply_markup=markup)

# BEDROOMS

@bot.message_handler(func=lambda m: m.text in ["1","2","3","4"])
def price_calc(message):

    chat_id = message.chat.id

    bedrooms = message.text
    cleaning = user_data[chat_id]["cleaning"]

    price = prices[cleaning][bedrooms]

    user_data[chat_id]["bedrooms"] = bedrooms
    user_data[chat_id]["price"] = price

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    tomorrow = (datetime.now()+timedelta(days=1)).strftime("%b %d")
    day2 = (datetime.now()+timedelta(days=2)).strftime("%b %d")
    day3 = (datetime.now()+timedelta(days=3)).strftime("%b %d")

    markup.add(tomorrow,day2,day3,"Another day")

    bot.send_message(
        chat_id,
        f"Estimated price: ${price}\n\nChoose cleaning date",
        reply_markup=markup
    )

# DATE

@bot.message_handler(func=lambda m: True)
def handle_date(message):

    chat_id = message.chat.id

    if chat_id not in user_data:
        return

    if "date" not in user_data[chat_id]:

        user_data[chat_id]["date"] = message.text

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("Inside oven","Inside fridge")
        markup.add("Pet hair","No extras")

        bot.send_message(chat_id,"Add extras?",reply_markup=markup)

        return

    if "extras" not in user_data[chat_id]:

        extras = message.text

        extra_cost = extras_prices.get(extras,0)

        user_data[chat_id]["extras"] = extras
        user_data[chat_id]["price"] += extra_cost

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

        location = types.KeyboardButton("Send location 📍",request_location=True)

        markup.add(location)

        bot.send_message(
            chat_id,
            f"Updated price: ${user_data[chat_id]['price']}\n\nSend address or location",
            reply_markup=markup
        )

        return

    if "location" not in user_data[chat_id]:

        user_data[chat_id]["location"] = message.text
        bot.send_message(chat_id,"Send phone number")

        return

    if "phone" not in user_data[chat_id]:

        user_data[chat_id]["phone"] = message.text

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("Skip photo")

        bot.send_message(chat_id,"Send photos or Skip",reply_markup=markup)

        return

# LOCATION

@bot.message_handler(content_types=['location'])
def location(message):

    chat_id = message.chat.id

    if chat_id not in user_data:
        user_data[chat_id] = {}

    user_data[chat_id]["location"] = f"{message.location.latitude},{message.location.longitude}"

    bot.send_message(chat_id, "Send phone number")

# SKIP PHOTO

@bot.message_handler(func=lambda m: m.text == "Skip photo")
def skip_photo(message):

    finalize_booking(message)

# PHOTO

@bot.message_handler(content_types=['photo'])
def photo(message):

    chat_id = message.chat.id
    bot.forward_message(ADMIN_ID,chat_id,message.message_id)

    finalize_booking(message)

# FINALIZE BOOKING

def finalize_booking(message):

    chat_id = message.chat.id
    data = user_data[chat_id]

    bookings[chat_id] = data

    text = f"""
🧼 NEW CLEANING REQUEST

Cleaning: {data['cleaning']}
Bedrooms: {data['bedrooms']}
Extras: {data['extras']}
Price: ${data['price']}
Date: {data['date']}

Location: {data['location']}
Phone: {data['phone']}
"""

    bot.send_message(ADMIN_ID,text)

    bot.send_message(
        chat_id,
        "✅ Your cleaning request has been received.\n\nCommands:\n/reschedule\n/cancel"
    )

    user_data.pop(chat_id)

# CANCEL

@bot.message_handler(commands=['cancel'])
def cancel(message):

    chat_id = message.chat.id

    if chat_id in bookings:
        bookings.pop(chat_id)
        bot.send_message(chat_id,"❌ Booking cancelled")

# RESCHEDULE

@bot.message_handler(commands=['reschedule'])
def reschedule(message):

    chat_id = message.chat.id

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    tomorrow = (datetime.now()+timedelta(days=1)).strftime("%b %d")
    day2 = (datetime.now()+timedelta(days=2)).strftime("%b %d")

    markup.add(tomorrow,day2)

    bot.send_message(chat_id,"Choose new date",reply_markup=markup)

# INVOICE

@bot.message_handler(commands=['invoice'])
def invoice(message):

    if message.from_user.id != ADMIN_ID:
        return

    args = message.text.split()

    client_id = int(args[1])
    data = bookings[client_id]

    file_name = f"invoice_{client_id}.pdf"

    c = canvas.Canvas(file_name)

    c.drawString(100,750,"Cleaning Pros Team")
    c.drawString(100,720,"Invoice")

    c.drawString(100,680,f"Service: {data['cleaning']}")
    c.drawString(100,660,f"Bedrooms: {data['bedrooms']}")
    c.drawString(100,640,f"Extras: {data['extras']}")
    c.drawString(100,620,f"Date: {data['date']}")
    c.drawString(100,600,f"Total: ${data['price']}")

    c.save()

    bot.send_document(client_id,open(file_name,"rb"))

# PRICES

@bot.message_handler(func=lambda m: m.text == "Prices")
def prices_show(message):

    bot.send_message(
        message.chat.id,
"""
Regular cleaning
1 bed $120
2 bed $150
3 bed $180

Deep cleaning
1 bed $180
2 bed $220
3 bed $260
"""
)

# CONTACT

@bot.message_handler(func=lambda m: m.text == "Contact")
def contact(message):

    bot.send_message(message.chat.id,"Phone: 253-000-0000")

bot.delete_webhook()
bot.infinity_polling()
