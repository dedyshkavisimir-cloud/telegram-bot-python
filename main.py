import telebot
from telebot import types
from datetime import datetime, timedelta

from config import TOKEN, ADMIN_ID
from storage import load_bookings, save_bookings
from invoice import create_invoice

bot = telebot.TeleBot(TOKEN)

user_data = {}

prices = {
    "Regular cleaning": {"1":120,"2":150,"3":180},
    "Deep cleaning": {"1":180,"2":220,"3":260},
    "Move out cleaning": {"1":200,"2":250,"3":300}
}

# ---------- MAIN MENU ----------

def main_menu(user_id=None):

    m = types.ReplyKeyboardMarkup(resize_keyboard=True)

    m.add("🧹 Book cleaning")
    m.add("💰 Prices","📞 Contact")

    if user_id == ADMIN_ID:
        m.add("⚙️ Admin panel")

    return m


# ---------- START ----------

@bot.message_handler(commands=['start'])
def start(message):

    bot.send_message(
        message.chat.id,
        "Welcome to Cleaning Pros Team 🧼",
        reply_markup=main_menu(message.chat.id)
    )


# ---------- PRICES ----------

@bot.message_handler(func=lambda m: m.text == "💰 Prices")
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


# ---------- CONTACT ----------

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


# ---------- BOOK CLEANING ----------

@bot.message_handler(func=lambda m: m.text == "🧹 Book cleaning")
def choose_cleaning(message):

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    markup.add("Regular cleaning")
    markup.add("Deep cleaning")
    markup.add("Move out cleaning")
    markup.add("❌ Cancel booking")

    bot.send_message(message.chat.id,"Choose cleaning type",reply_markup=markup)


# ---------- BEDROOMS ----------

@bot.message_handler(func=lambda m: m.text in prices.keys())
def bedrooms(message):

    chat_id = message.chat.id

    user_data[chat_id] = {"cleaning": message.text}

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    markup.add("1","2","3")
    markup.add("❌ Cancel booking")

    bot.send_message(chat_id,"How many bedrooms?",reply_markup=markup)


# ---------- PRICE + DATE ----------

@bot.message_handler(func=lambda m: m.text in ["1","2","3"])
def choose_date(message):

    chat_id = message.chat.id

    bedrooms = message.text

    cleaning = user_data[chat_id]["cleaning"]

    price = prices[cleaning][bedrooms]

    user_data[chat_id]["bedrooms"] = bedrooms
    user_data[chat_id]["price"] = price

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    today = datetime.now()

    for i in range(1,7):
        d = today + timedelta(days=i)
        markup.add(d.strftime("%b %d"))

    markup.add("❌ Cancel booking")

    bot.send_message(
        chat_id,
        f"Estimated price: ${price}\nChoose cleaning date",
        reply_markup=markup
    )


# ---------- DATE ----------

@bot.message_handler(func=lambda m: len(m.text)==6 and m.text[3]==" ")
def extras(message):

    chat_id = message.chat.id

    user_data[chat_id]["date"] = message.text

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    markup.add("Inside fridge")
    markup.add("Inside oven")
    markup.add("No extras")
    markup.add("📅 Change date","❌ Cancel booking")

    bot.send_message(chat_id,"Add extras?",reply_markup=markup)


# ---------- EXTRAS ----------

@bot.message_handler(func=lambda m: m.text in ["Inside fridge","Inside oven","No extras"])
def address(message):

    chat_id = message.chat.id

    user_data[chat_id]["extras"] = message.text

    bot.send_message(chat_id,"Send address or location")


# ---------- LOCATION ----------

@bot.message_handler(content_types=['location'])
def location(message):

    chat_id = message.chat.id

    loc = message.location

    user_data[chat_id]["location"] = f"https://maps.google.com/?q={loc.latitude},{loc.longitude}"

    bot.send_message(chat_id,"Send phone number")


# ---------- ADDRESS TEXT ----------

@bot.message_handler(func=lambda m: "http" not in m.text and m.text[0].isdigit())
def phone(message):

    chat_id = message.chat.id

    user_data[chat_id]["phone"] = message.text

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    markup.add("Skip photo")
    markup.add("📅 Change date","❌ Cancel booking")

    bot.send_message(chat_id,"Send photos or Skip",reply_markup=markup)


# ---------- PHOTO ----------

@bot.message_handler(content_types=['photo'])
def photo(message):

    finalize_booking(message)


# ---------- SKIP PHOTO ----------

@bot.message_handler(func=lambda m: m.text == "Skip photo")
def skip_photo(message):

    finalize_booking(message)


# ---------- FINALIZE BOOKING ----------

def finalize_booking(message):

    chat_id = message.chat.id

    data = user_data.get(chat_id)

    if not data:
        return

    save_booking(data)

    bot.send_message(
        chat_id,
        "✅ Thank you! Your request has been sent.\nWe will contact you soon.",
        reply_markup=main_menu(chat_id)
    )

    text = f"""
🧼 NEW CLEANING REQUEST

Cleaning: {data['cleaning']}
Bedrooms: {data['bedrooms']}
Price: ${data['price']}

Date: {data['date']}
Extras: {data['extras']}

Phone: {data['phone']}
"""

    bot.send_message(ADMIN_ID,text)

    user_data.pop(chat_id)


# ---------- CANCEL ----------

@bot.message_handler(func=lambda m: m.text == "❌ Cancel booking")
def cancel(message):

    chat_id = message.chat.id

    if chat_id in user_data:
        user_data.pop(chat_id)

    bot.send_message(chat_id,"Booking cancelled",reply_markup=main_menu(chat_id))


# ---------- CHANGE DATE ----------

@bot.message_handler(func=lambda m: m.text == "📅 Change date")
def change_date(message):

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    today = datetime.now()

    for i in range(1,7):
        d = today + timedelta(days=i)
        markup.add(d.strftime("%b %d"))

    bot.send_message(message.chat.id,"Choose new date",reply_markup=markup)


# ---------- ADMIN PANEL ----------

@bot.message_handler(func=lambda m: m.text == "⚙️ Admin panel")
def admin_panel(message):

    if message.chat.id != ADMIN_ID:
        return

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    markup.add("🧾 Invoice")

    bot.send_message(message.chat.id,"Admin panel",reply_markup=markup)


# ---------- INVOICE ----------

@bot.message_handler(func=lambda m: m.text == "🧾 Invoice")
def invoice(message):

    if message.chat.id != ADMIN_ID:
        return

    bookings = load_bookings()

    if not bookings:
        bot.send_message(message.chat.id,"No bookings yet")
        return

    last = bookings[-1]

    file = create_invoice(last)

    with open(file,"rb") as f:
        bot.send_document(message.chat.id,f)


# ---------- RUN BOT ----------

bot.infinity_polling()
