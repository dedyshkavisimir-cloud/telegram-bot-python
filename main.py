import telebot
from telebot import types
import os
import json
from reportlab.pdfgen import canvas
from datetime import datetime

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

ADMIN_ID = 146998462

bot = telebot.TeleBot(TOKEN)

user_data = {}

prices = {
    "Regular cleaning": {"1":120,"2":150,"3":180},
    "Deep cleaning": {"1":180,"2":220,"3":260},
    "Move out cleaning": {"1":200,"2":250,"3":300}
}

# ---------- COUNTERS ----------

def load_counters():

    with open("counters.json") as f:
        return json.load(f)

def save_counters(data):

    with open("counters.json","w") as f:
        json.dump(data,f)


# ---------- INVOICE ----------

def create_invoice(data):

    counters = load_counters()

    invoice_id = f"INV{counters['invoice']:03}"

    counters["invoice"] += 1

    save_counters(counters)

    filename = f"{invoice_id}.pdf"

    c = canvas.Canvas(filename)

    c.drawImage("logo.png",200,760,width=200,height=80)

    c.setFont("Helvetica-Bold",18)
    c.drawString(50,720,"INVOICE")

    c.setFont("Helvetica",12)

    c.drawString(50,700,f"Invoice ID: {invoice_id}")
    c.drawString(50,680,f"Booking ID: {data['booking_id']}")

    c.drawString(400,700,f"Date: {datetime.now().strftime('%b %d %Y')}")

    c.line(50,660,550,660)

    c.setFont("Helvetica-Bold",14)
    c.drawString(50,630,"Customer")

    c.setFont("Helvetica",12)

    c.drawString(50,610,f"Client ID: {data['client_id']}")
    c.drawString(50,590,f"Name: {data['name']}")
    c.drawString(50,570,f"Phone: {data['phone']}")
    c.drawString(50,550,f"Address: {data['address']}")

    c.drawString(50,530,f"Cleaning date: {data['date']}")

    c.setFont("Helvetica-Bold",14)
    c.drawString(50,490,"Service")

    c.line(50,470,550,470)

    c.setFont("Helvetica-Bold",12)

    c.drawString(50,450,"Service")
    c.drawString(250,450,"Bedrooms")
    c.drawString(450,450,"Price")

    c.line(50,440,550,440)

    c.setFont("Helvetica",12)

    c.drawString(50,420,data['cleaning'])
    c.drawString(270,420,data['bedrooms'])
    c.drawString(450,420,f"${data['price']}")

    c.line(50,400,550,400)

    c.setFont("Helvetica-Bold",14)

    c.drawString(350,370,"TOTAL:")
    c.drawString(450,370,f"${data['price']}")

    c.line(50,350,550,350)

    c.setFont("Helvetica",11)

    c.drawCentredString(300,320,"Phone: 253-202-0979")
    c.drawCentredString(300,305,"Email: manager@excellentsolution.online")

    c.drawCentredString(300,280,"Thank you for choosing Cleaning Pros Team!")

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
def price(message):

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

    bot.send_message(
        message.chat.id,
        "Phone: 2532020979\nEmail: manager@excellentsolution.online"
    )


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


@bot.message_handler(func=lambda m: m.text in prices)
def cleaning(message):

    chat_id = message.chat.id

    user_data[chat_id]["cleaning"] = message.text

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    markup.add("1","2","3")

    bot.send_message(chat_id,"How many bedrooms?",reply_markup=markup)


@bot.message_handler(func=lambda m: m.text in ["1","2","3"])
def bedrooms(message):

    chat_id = message.chat.id

    cleaning = user_data[chat_id]["cleaning"]

    bedrooms = message.text

    price = prices[cleaning][bedrooms]

    user_data[chat_id]["bedrooms"] = bedrooms
    user_data[chat_id]["price"] = price

    bot.send_message(chat_id,f"Estimated price: ${price}")

    bot.send_message(chat_id,"Send cleaning date")


@bot.message_handler(func=lambda m: "date" not in user_data.get(m.chat.id,{}))
def date(message):

    chat_id = message.chat.id

    user_data[chat_id]["date"] = message.text

    bot.send_message(chat_id,"Send address")


@bot.message_handler(func=lambda m: "address" not in user_data.get(m.chat.id,{}))
def address(message):

    chat_id = message.chat.id

    user_data[chat_id]["address"] = message.text

    bot.send_message(chat_id,"Your name?")


@bot.message_handler(func=lambda m: "name" not in user_data.get(m.chat.id,{}))
def name(message):

    chat_id = message.chat.id

    user_data[chat_id]["name"] = message.text

    bot.send_message(chat_id,"Phone number?")


@bot.message_handler(func=lambda m: m.text.isdigit())
def phone(message):

    chat_id = message.chat.id

    user_data[chat_id]["phone"] = message.text

    finalize_booking(message)


# ---------- FINALIZE ----------

def finalize_booking(message):

    chat_id = message.chat.id

    data = user_data[chat_id]

    counters = load_counters()

    client_id = f"C{counters['client']:03}"
    booking_id = f"B{counters['booking']:03}"

    counters["client"] += 1
    counters["booking"] += 1

    save_counters(counters)

    data["client_id"] = client_id
    data["booking_id"] = booking_id

    text = f"""
NEW BOOKING

Booking: {booking_id}

Client: {data['name']}
Phone: {data['phone']}

Service: {data['cleaning']}
Bedrooms: {data['bedrooms']}

Date: {data['date']}

Address:
{data['address']}

Price: ${data['price']}
"""

    bot.send_message(ADMIN_ID,text)

    bot.send_message(
        chat_id,
        "✅ Your request has been received.\n\nWe will contact you shortly to confirm the time."
    )

    user_data.pop(chat_id)


bot.infinity_polling()
