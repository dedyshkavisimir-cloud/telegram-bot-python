import telebot
from telebot import types
import os
import json
import schedule
import threading
import time
from datetime import datetime, timedelta
from reportlab.pdfgen import canvas

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_ID = 146998462

bot = telebot.TeleBot(TOKEN)

user_data = {}

prices = {
    "Regular cleaning": {"1":120,"2":150,"3":180},
    "Deep cleaning": {"1":180,"2":220,"3":260},
    "Move out cleaning": {"1":200,"2":250,"3":300}
}

# ---------- FILES ----------

def load_json(file):

    with open(file) as f:
        return json.load(f)

def save_json(file,data):

    with open(file,"w") as f:
        json.dump(data,f,indent=2)


# ---------- INVOICE ----------

def create_invoice(data):

    counters = load_json("counters.json")

    invoice_id = f"INV{counters['invoice']:03}"

    counters["invoice"] += 1
    save_json("counters.json",counters)

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

    c.drawString(50,610,f"Client: {data['name']}")
    c.drawString(50,590,f"Phone: {data['phone']}")
    c.drawString(50,570,f"Address: {data['address']}")
    c.drawString(50,550,f"Cleaning date: {data['date']}")

    c.setFont("Helvetica-Bold",14)
    c.drawString(50,510,"Service")

    c.line(50,490,550,490)

    c.drawString(50,470,data["cleaning"])
    c.drawString(250,470,data["bedrooms"])
    c.drawString(450,470,f"${data['price']}")

    c.line(50,450,550,450)

    c.setFont("Helvetica-Bold",14)
    c.drawString(350,420,"TOTAL:")
    c.drawString(450,420,f"${data['price']}")

    c.drawCentredString(300,380,"Phone: 2532020979")
    c.drawCentredString(300,360,"Email: manager@excellentsolution.online")

    c.save()

    return filename


# ---------- REMINDER SYSTEM ----------

def check_reminders():

    bookings = load_json("bookings.json")

    now = datetime.now()

    for booking in bookings:

        date = datetime.strptime(booking["date"],"%Y-%m-%d")

        if date - timedelta(hours=24) <= now <= date - timedelta(hours=23):

            bot.send_message(
                booking["chat_id"],
                "Reminder\n\nYour cleaning is scheduled tomorrow."
            )


def run_scheduler():

    schedule.every(30).minutes.do(check_reminders)

    while True:

        schedule.run_pending()
        time.sleep(10)


threading.Thread(target=run_scheduler).start()


# ---------- START ----------

@bot.message_handler(commands=['start'])
def start(message):

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    markup.add("🧹 Book cleaning")
    markup.add("💰 Prices","📞 Contact")
    markup.add("📅 Change booking","❌ Cancel booking")

    bot.send_message(
        message.chat.id,
        "Welcome to Cleaning Pros Team",
        reply_markup=markup
    )


# ---------- BOOK ----------

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
    bot.send_message(chat_id,"Send cleaning date YYYY-MM-DD")


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

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    markup.add("Skip photo")

    bot.send_message(chat_id,"Send photo or Skip",reply_markup=markup)


@bot.message_handler(content_types=['photo'])
def photo(message):

    bot.forward_message(ADMIN_ID,message.chat.id,message.message_id)

    finalize_booking(message)


@bot.message_handler(func=lambda m: m.text == "Skip photo")
def skip(message):

    finalize_booking(message)


# ---------- FINALIZE ----------

def finalize_booking(message):

    chat_id = message.chat.id

    data = user_data[chat_id]

    counters = load_json("counters.json")

    booking_id = f"B{counters['booking']:03}"

    counters["booking"] += 1
    save_json("counters.json",counters)

    data["booking_id"] = booking_id

    bookings = load_json("bookings.json")

    bookings.append({
        "booking_id":booking_id,
        "chat_id":chat_id,
        "date":data["date"]
    })

    save_json("bookings.json",bookings)

    bot.send_message(
        chat_id,
        "Your request has been received.\n\nWe will contact you to confirm the time."
    )

    bot.send_message(ADMIN_ID,f"NEW BOOKING {booking_id}\n{data}")

    user_data.pop(chat_id)


bot.infinity_polling()
