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

# ---------- INVOICE ----------

def create_invoice(data):

    invoice_number = random.randint(1000,9999)
    filename = f"invoice_{invoice_number}.pdf"

    c = canvas.Canvas(filename)

    c.setFont("Helvetica-Bold",22)
    c.drawCentredString(300,810,"CLEANING PROS TEAM")

    c.setFont("Helvetica",11)
    c.drawCentredString(300,790,"Phone: 253-202-0979")
    c.drawCentredString(300,775,"Email: manager@excellentsolution.online")

    c.line(50,760,550,760)

    c.setFont("Helvetica-Bold",18)
    c.drawString(50,730,"INVOICE")

    c.setFont("Helvetica",12)
    c.drawString(50,705,f"Invoice #: {invoice_number}")
    c.drawString(400,705,f"Date: {datetime.now().strftime('%b %d %Y')}")

    c.setFont("Helvetica-Bold",14)
    c.drawString(50,660,"Customer Information")

    c.setFont("Helvetica",12)
    c.drawString(50,640,f"Name: {data['name']}")
    c.drawString(50,620,f"Phone: {data['phone']}")
    c.drawString(50,600,f"Address: {data['address']}")
    c.drawString(50,580,f"Cleaning Date: {data['date']}")

    c.setFont("Helvetica-Bold",14)
    c.drawString(50,540,"Service Details")

    c.line(50,520,550,520)

    c.setFont("Helvetica-Bold",12)
    c.drawString(50,500,"Service")
    c.drawString(260,500,"Bedrooms")
    c.drawString(450,500,"Price")

    c.line(50,490,550,490)

    c.setFont("Helvetica",12)
    c.drawString(50,470,data['cleaning'])
    c.drawString(280,470,data['bedrooms'])
    c.drawString(450,470,f"${data['price']}")

    c.line(50,450,550,450)

    c.setFont("Helvetica-Bold",15)
    c.drawString(350,420,"TOTAL:")
    c.drawString(450,420,f"${data['price']}")

    c.line(50,400,550,400)

    c.setFont("Helvetica",11)
    c.drawCentredString(300,370,"Thank you for choosing Cleaning Pros Team!")

    c.save()

    return filename


# ---------- START ----------

@bot.message_handler(commands=['start'])
def start(message):

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    markup.add("🧹 Book cleaning")
    markup.add("💰 Prices","📞 Contact")
    markup.add("📅 Change booking","❌ Cancel booking")

    bot.send_message(
        message.chat.id,
        "Welcome to Cleaning Pros Team 🧼",
        reply_markup=markup
    )


# ---------- PRICES ----------

@bot.message_handler(func=lambda m: m.text == "💰 Prices")
def prices_list(message):

    text = """
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


# ---------- CONTACT ----------

@bot.message_handler(func=lambda m: m.text == "📞 Contact")
def contact(message):

    text = """
Cleaning Pros Team

Phone: 253-202-0979
Email: manager@excellentsolution.online
"""

    bot.send_message(message.chat.id,text)


# ---------- BOOK CLEANING ----------

@bot.message_handler(func=lambda m: m.text == "🧹 Book cleaning")
def book(message):

    chat_id = message.chat.id

    user_data[chat_id] = {}

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    markup.add("Regular cleaning")
    markup.add("Deep cleaning")
    markup.add("Move out cleaning")

    bot.send_message(chat_id,"Choose cleaning type",reply_markup=markup)


# ---------- CLEANING TYPE ----------

@bot.message_handler(func=lambda m: m.text in prices)
def cleaning_type(message):

    chat_id = message.chat.id

    user_data[chat_id]["cleaning"] = message.text

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    markup.add("1","2","3")

    bot.send_message(chat_id,"How many bedrooms?",reply_markup=markup)


# ---------- BEDROOMS ----------

@bot.message_handler(func=lambda m: m.text in ["1","2","3"])
def bedrooms(message):

    chat_id = message.chat.id

    bedrooms = message.text
    cleaning = user_data[chat_id]["cleaning"]

    price = prices[cleaning][bedrooms]

    user_data[chat_id]["bedrooms"] = bedrooms
    user_data[chat_id]["price"] = price

    bot.send_message(chat_id,f"Estimated price: ${price}")

    bot.send_message(chat_id,"Send cleaning date (example: March 15)")


# ---------- DATE ----------

@bot.message_handler(func=lambda m: "date" not in user_data.get(m.chat.id, {}))
def date(message):

    chat_id = message.chat.id

    user_data[chat_id]["date"] = message.text

    bot.send_message(chat_id,"Send your address")


# ---------- ADDRESS ----------

@bot.message_handler(func=lambda m: "address" not in user_data.get(m.chat.id, {}))
def address(message):

    chat_id = message.chat.id

    user_data[chat_id]["address"] = message.text

    bot.send_message(chat_id,"What is your name?")


# ---------- NAME ----------

@bot.message_handler(func=lambda m: "name" not in user_data.get(m.chat.id, {}))
def name(message):

    chat_id = message.chat.id

    user_data[chat_id]["name"] = message.text

    bot.send_message(chat_id,"Send phone number")


# ---------- PHONE ----------

@bot.message_handler(func=lambda m: m.text.isdigit())
def phone(message):

    chat_id = message.chat.id

    user_data[chat_id]["phone"] = message.text

    finalize_booking(message)


# ---------- FINALIZE ----------

def finalize_booking(message):

    chat_id = message.chat.id

    data = user_data.get(chat_id)

    text = f"""
NEW BOOKING

Name: {data['name']}
Phone: {data['phone']}

Cleaning: {data['cleaning']}
Bedrooms: {data['bedrooms']}

Date: {data['date']}

Address:
{data['address']}

Price: ${data['price']}
"""

    bot.send_message(ADMIN_ID,text)

    invoice = create_invoice(data)

    with open(invoice,"rb") as f:

        bot.send_document(chat_id,f)

    bot.send_message(chat_id,"✅ Booking confirmed!")

    user_data.pop(chat_id)


# ---------- CANCEL ----------

@bot.message_handler(func=lambda m: m.text == "❌ Cancel booking")
def cancel(message):

    bot.send_message(message.chat.id,"Booking cancelled.")


# ---------- CHANGE DATE ----------

@bot.message_handler(func=lambda m: m.text == "📅 Change booking")
def change(message):

    bot.send_message(message.chat.id,"Send new cleaning date")

bot.infinity_polling()
