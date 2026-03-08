import telebot
from telebot import types
from datetime import datetime, timedelta

from config import TOKEN, ADMIN_ID
from storage import load_bookings, save_bookings
from invoice import create_invoice

bot = telebot.TeleBot(TOKEN)

user_data = {}

prices = {
"Regular cleaning":{"1":120,"2":150,"3":180},
"Deep cleaning":{"1":180,"2":220,"3":260},
"Move out cleaning":{"1":200,"2":250,"3":300}
}


def main_menu(user_id=None):

    m = types.ReplyKeyboardMarkup(resize_keyboard=True)

    m.add("🧹 Book cleaning")
    m.add("💲 Prices","📞 Contact")

    if user_id == ADMIN_ID:
        m.add("⚙ Admin panel")

    return m


@bot.message_handler(commands=['start'])
def start(message):

    bot.send_message(
        message.chat.id,
        "Welcome to Cleaning Pros Team 🧼",
        reply_markup=main_menu(message.chat.id)
    )


@bot.message_handler(func=lambda m: m.text == "💲 Prices")
def prices_menu(message):

    bot.send_message(
        message.chat.id,
"""
Regular cleaning
1 bedroom $120
2 bedrooms $150
3 bedrooms $180

Deep cleaning
1 bedroom $180
2 bedrooms $220
3 bedrooms $260

Move out cleaning
1 bedroom $200
2 bedrooms $250
3 bedrooms $300
"""
)


@bot.message_handler(func=lambda m: m.text == "📞 Contact")
def contact(message):

    bot.send_message(
        message.chat.id,
"""
Cleaning Pros Team

Phone: 2532020979
Email: manager@excellentsolution.online
"""
)


@bot.message_handler(func=lambda m: m.text == "🧹 Book cleaning")
def cleaning_type(message):

    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)

    kb.add("Regular cleaning")
    kb.add("Deep cleaning")
    kb.add("Move out cleaning")

    bot.send_message(message.chat.id,"Choose cleaning type",reply_markup=kb)


@bot.message_handler(func=lambda m: m.text in prices.keys())
def bedrooms(message):

    chat = message.chat.id

    user_data[chat] = {}
    user_data[chat]["cleaning"] = message.text

    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("1","2","3")

    bot.send_message(chat,"How many bedrooms?",reply_markup=kb)


@bot.message_handler(func=lambda m: m.text in ["1","2","3"])
def date_step(message):

    chat = message.chat.id

    user_data[chat]["bedrooms"] = message.text

    price = prices[user_data[chat]["cleaning"]][message.text]
    user_data[chat]["price"] = price

    today = datetime.now()
    d1 = (today + timedelta(days=1)).strftime("%b %d")
    d2 = (today + timedelta(days=2)).strftime("%b %d")

    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(d1)
    kb.add(d2)

    bot.send_message(chat,f"Estimated price ${price}\nChoose date",reply_markup=kb)


@bot.message_handler(func=lambda m: True)
def extras(message):

    chat = message.chat.id

    if chat not in user_data:
        return

    if "date" not in user_data[chat]:

        user_data[chat]["date"] = message.text

        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add("Inside fridge")
        kb.add("Inside oven")
        kb.add("No extras")

        bot.send_message(chat,"Add extras?",reply_markup=kb)

        return


    if "extras" not in user_data[chat]:

        user_data[chat]["extras"] = message.text

        bot.send_message(chat,"Send address")

        return


    if "address" not in user_data[chat]:

        user_data[chat]["address"] = message.text

        bot.send_message(chat,"Send phone number")

        return


    if "phone" not in user_data[chat]:

        user_data[chat]["phone"] = message.text

        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add("Skip photo")

        bot.send_message(chat,"Send photos or Skip",reply_markup=kb)

        return


@bot.message_handler(func=lambda m: m.text == "Skip photo")
def skip_photo(message):

    finalize_booking(message)


@bot.message_handler(content_types=['photo'])
def photo(message):

    bot.forward_message(ADMIN_ID,message.chat.id,message.message_id)

    finalize_booking(message)


def finalize_booking(message):

    chat = message.chat.id
    data = user_data.get(chat)

    if not data:
        return

    bookings = load_bookings()

    booking_id = f"B{len(bookings)+1:03}"

    data["id"] = booking_id
    data["name"] = message.from_user.first_name

    bookings.append(data)

    save_bookings(bookings)

    bot.send_message(
        chat,
        "✅ Thank you! Your request has been sent.\nWe will contact you soon.",
        reply_markup=main_menu(chat)
    )

    bot.send_message(
        ADMIN_ID,
f"""
🧼 NEW CLEANING REQUEST

Cleaning: {data['cleaning']}
Bedrooms: {data['bedrooms']}
Price: ${data['price']}

Date: {data['date']}
Extras: {data['extras']}

Address: {data['address']}
Phone: {data['phone']}

Client: {data['name']}
"""
)

    user_data.pop(chat)


@bot.message_handler(func=lambda m: m.text == "⚙ Admin panel")
def admin_panel(message):

    if message.chat.id != ADMIN_ID:
        return

    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)

    kb.add("📋 Today")
    kb.add("📅 Tomorrow")
    kb.add("📂 All bookings")
    kb.add("💰 Income")
    kb.add("🧾 Invoice")

    bot.send_message(message.chat.id,"Admin panel",reply_markup=kb)


@bot.message_handler(func=lambda m: m.text == "📋 Today")
def today(message):

    bookings = load_bookings()

    today = datetime.now().strftime("%b %d")

    text = "TODAY BOOKINGS\n\n"

    for b in bookings:
        if b["date"] == today:
            text += f"{b['id']} {b['name']} ${b['price']}\n"

    bot.send_message(message.chat.id,text)


@bot.message_handler(func=lambda m: m.text == "📅 Tomorrow")
def tomorrow(message):

    bookings = load_bookings()

    tomorrow = (datetime.now()+timedelta(days=1)).strftime("%b %d")

    text = "TOMORROW BOOKINGS\n\n"

    for b in bookings:
        if b["date"] == tomorrow:
            text += f"{b['id']} {b['name']} ${b['price']}\n"

    bot.send_message(message.chat.id,text)


@bot.message_handler(func=lambda m: m.text == "📂 All bookings")
def all_bookings(message):

    bookings = load_bookings()

    text = "ALL BOOKINGS\n\n"

    for b in bookings:
        text += f"{b['id']} {b['date']} {b['name']} ${b['price']}\n"

    bot.send_message(message.chat.id,text)


@bot.message_handler(func=lambda m: m.text == "💰 Income")
def income(message):

    bookings = load_bookings()

    total = sum(b["price"] for b in bookings)

    bot.send_message(message.chat.id,f"Total income ${total}")


@bot.message_handler(func=lambda m: m.text == "🧾 Invoice")
def invoice(message):

    bookings = load_bookings()

    if not bookings:
        bot.send_message(message.chat.id,"No bookings")
        return

    data = bookings[-1]

    filename = f"invoice_{data['id']}.pdf"

    create_invoice(data,filename)

    with open(filename,"rb") as f:
        bot.send_document(message.chat.id,f)


bot.infinity_polling()
