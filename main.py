import telebot
from telebot import types
import os
from reportlab.pdfgen import canvas
from datetime import datetime
import random

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

ADMIN_ID = 146998462

bot = telebot.TeleBot(TOKEN)

user_data = {}

prices = {
    "Regular cleaning": {"1":120,"2":150,"3":180},
    "Deep cleaning": {"1":180,"2":220,"3":260},
    "Move out cleaning": {"1":200,"2":250,"3":300}
}

# -------- INVOICE -------- #

def create_invoice(data):

    invoice_number = random.randint(1000,9999)

    filename = f"invoice_{invoice_number}.pdf"

    c = canvas.Canvas(filename)

    c.setFont("Helvetica-Bold",16)
    c.drawString(200,800,"CLEANING PROS TEAM")

    c.setFont("Helvetica",12)
    c.drawString(200,780,"Professional Cleaning Service")

    c.setFont("Helvetica-Bold",14)
    c.drawString(50,730,"INVOICE")

    c.setFont("Helvetica",12)

    c.drawString(50,700,f"Invoice #: {invoice_number}")
    c.drawString(50,680,f"Date: {datetime.now().strftime('%B %d %Y')}")

    c.drawString(50,640,"Customer:")

    c.drawString(50,620,f"Phone: {data['phone']}")
    c.drawString(50,600,f"Location: {data.get('location','N/A')}")

    c.drawString(50,560,"Service:")

    c.drawString(50,540,f"Cleaning: {data['cleaning']}")
    c.drawString(50,520,f"Bedrooms: {data['bedrooms']}")

    c.setFont("Helvetica-Bold",12)
    c.drawString(50,480,f"Total: ${data['price']}")

    c.drawString(50,440,"Thank you for choosing Cleaning Pros Team!")

    c.save()

    return filename

# -------- START -------- #

@bot.message_handler(commands=['start'])
def start(message):

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    markup.add("🧹 Book cleaning")
    markup.add("💰 Prices","📞 Contact")

    bot.send_message(
        message.chat.id,
        "Welcome to Cleaning Pros Team 🧼\n\nChoose option:",
        reply_markup=markup
    )

# -------- PRICE -------- #

@bot.message_handler(func=lambda m: m.text == "💰 Prices")
def price(message):

    text = """
💰 CLEANING PRICES

Regular cleaning
1 bedroom — $120
2 bedroom — $150
3 bedroom — $180

Deep cleaning
1 bedroom — $180
2 bedroom — $220
3 bedroom — $260

Move out cleaning
1 bedroom — $200
2 bedroom — $250
3 bedroom — $300
"""

    bot.send_message(message.chat.id,text)

# -------- CONTACT -------- #

@bot.message_handler(func=lambda m: m.text == "📞 Contact")
def contact(message):

    text = """
📞 Cleaning Pros Team

Phone: +1 (253) 202-0979

Service area: Washington

We will contact you to confirm time after booking.
"""

    bot.send_message(message.chat.id,text)

# -------- BOOK CLEANING -------- #

@bot.message_handler(func=lambda m: m.text == "🧹 Book cleaning")
def book(message):

    chat_id = message.chat.id

    user_data[chat_id] = {}

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    markup.add("Regular cleaning")
    markup.add("Deep cleaning")
    markup.add("Move out cleaning")

    bot.send_message(chat_id,"Choose cleaning type",reply_markup=markup)

# -------- CLEANING TYPE -------- #

@bot.message_handler(func=lambda m: m.text in prices)
def cleaning_type(message):

    chat_id = message.chat.id

    user_data[chat_id]["cleaning"] = message.text

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    markup.add("1","2","3")

    bot.send_message(chat_id,"How many bedrooms?",reply_markup=markup)

# -------- BEDROOMS -------- #

@bot.message_handler(func=lambda m: m.text in ["1","2","3"])
def bedrooms(message):

    chat_id = message.chat.id

    bedrooms = message.text

    cleaning = user_data[chat_id]["cleaning"]

    price = prices[cleaning][bedrooms]

    user_data[chat_id]["bedrooms"] = bedrooms
    user_data[chat_id]["price"] = price

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    button = types.KeyboardButton("Send location 📍",request_location=True)

    markup.add(button)

    bot.send_message(
        chat_id,
        f"Estimated price: ${price}\n\nSend address or location",
        reply_markup=markup
    )

# -------- LOCATION -------- #

@bot.message_handler(content_types=['location'])
def location(message):

    chat_id = message.chat.id

    if chat_id not in user_data:
        user_data[chat_id] = {}

    user_data[chat_id]["location"] = f"{message.location.latitude},{message.location.longitude}"

    bot.send_message(chat_id,"Send phone number")

# -------- PHONE -------- #

@bot.message_handler(func=lambda m: m.text.isdigit())
def phone(message):

    chat_id = message.chat.id

    user_data[chat_id]["phone"] = message.text

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    markup.add("Skip photo")

    bot.send_message(chat_id,"Send photos or Skip",reply_markup=markup)

# -------- SKIP PHOTO -------- #

@bot.message_handler(func=lambda m: m.text == "Skip photo")
def skip_photo(message):

    finalize_booking(message)

# -------- PHOTO -------- #

@bot.message_handler(content_types=['photo'])
def photo(message):

    chat_id = message.chat.id

    bot.forward_message(ADMIN_ID,chat_id,message.message_id)

    finalize_booking(message)

# -------- FINALIZE -------- #

def finalize_booking(message):

    chat_id = message.chat.id

    data = user_data.get(chat_id)

    if not data:
        return

    text = f"""
🧼 NEW CLEANING REQUEST

Cleaning: {data['cleaning']}
Bedrooms: {data['bedrooms']}
Price: ${data['price']}

Location: {data.get('location','not sent')}

Phone: {data['phone']}
"""

    bot.send_message(ADMIN_ID,text)

    invoice = create_invoice(data)

    with open(invoice,"rb") as f:

        bot.send_document(chat_id,f)

    bot.send_message(
        chat_id,
        "✅ Thank you! Your request has been sent.\n\nWe will contact you soon."
    )

    user_data.pop(chat_id)

bot.infinity_polling()
