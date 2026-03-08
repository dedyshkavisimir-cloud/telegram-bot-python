import telebot
from telebot import types
import os
import json
from datetime import datetime, timedelta
import schedule
import time
import threading
from reportlab.pdfgen import canvas

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_ID = 146998462

bot = telebot.TeleBot(TOKEN)

user_data = {}

prices = {
"Regular cleaning":{"1":120,"2":150,"3":180},
"Deep cleaning":{"1":180,"2":220,"3":260},
"Move out cleaning":{"1":200,"2":250,"3":300}
}

# ---------- JSON ----------

def load_json(file):

    with open(file) as f:
        return json.load(f)

def save_json(file,data):

    with open(file,"w") as f:
        json.dump(data,f,indent=2)

# ---------- MENU ----------

def main_menu():

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    markup.add("🧹 Book cleaning")
    markup.add("💰 Prices","📞 Contact")
    markup.add("📅 Change booking","❌ Cancel booking")

    return markup

# ---------- START ----------

@bot.message_handler(commands=['start'])
def start(message):

    bot.send_message(
        message.chat.id,
        "Welcome to Cleaning Pros Team",
        reply_markup=main_menu()
    )

# ---------- PRICES ----------

@bot.message_handler(func=lambda m: m.text=="💰 Prices")
def prices_menu(message):

    bot.send_message(message.chat.id,
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
""")

# ---------- CONTACT ----------

@bot.message_handler(func=lambda m: m.text=="📞 Contact")
def contact(message):

    bot.send_message(
        message.chat.id,
"""Cleaning Pros Team

Phone: 2532020979
Email: manager@excellentsolution.online"""
    )

# ---------- BOOK ----------

@bot.message_handler(func=lambda m: m.text=="🧹 Book cleaning")
def book(message):

    chat_id = message.chat.id

    user_data[chat_id]={"step":"cleaning"}

    markup=types.ReplyKeyboardMarkup(resize_keyboard=True)

    markup.add("Regular cleaning")
    markup.add("Deep cleaning")
    markup.add("Move out cleaning")

    bot.send_message(chat_id,"Choose cleaning type",reply_markup=markup)

# ---------- FLOW ----------

@bot.message_handler(func=lambda message: True)
def booking_flow(message):

    chat_id=message.chat.id

    if chat_id not in user_data:
        return

    step=user_data[chat_id]["step"]

    # cleaning
    if step=="cleaning":

        if message.text not in prices:
            return

        user_data[chat_id]["cleaning"]=message.text
        user_data[chat_id]["step"]="bedrooms"

        markup=types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("1","2","3")

        bot.send_message(chat_id,"How many bedrooms?",reply_markup=markup)

    # bedrooms
    elif step=="bedrooms":

        cleaning=user_data[chat_id]["cleaning"]

        bedrooms=message.text

        price=prices[cleaning][bedrooms]

        user_data[chat_id]["bedrooms"]=bedrooms
        user_data[chat_id]["price"]=price
        user_data[chat_id]["step"]="date"

        bot.send_message(chat_id,f"Estimated price ${price}")
        bot.send_message(chat_id,"Cleaning date YYYY-MM-DD")

    # date
    elif step=="date":

        user_data[chat_id]["date"]=message.text
        user_data[chat_id]["step"]="address"

        bot.send_message(chat_id,"Send address")

    # address
    elif step=="address":

        user_data[chat_id]["address"]=message.text
        user_data[chat_id]["step"]="name"

        bot.send_message(chat_id,"Your name")

    # name
    elif step=="name":

        user_data[chat_id]["name"]=message.text
        user_data[chat_id]["step"]="phone"

        bot.send_message(chat_id,"Phone number")

    # phone
    elif step=="phone":

        user_data[chat_id]["phone"]=message.text
        user_data[chat_id]["step"]="photo"

        markup=types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("Skip photo")

        bot.send_message(chat_id,"Send photo or Skip",reply_markup=markup)

# ---------- PHOTO ----------

@bot.message_handler(content_types=['photo'])
def photo(message):

    chat_id=message.chat.id

    if chat_id not in user_data:
        return

    bot.forward_message(ADMIN_ID,chat_id,message.message_id)

    finalize_booking(message)

@bot.message_handler(func=lambda m: m.text=="Skip photo")
def skip(message):

    finalize_booking(message)

# ---------- FINALIZE ----------

def finalize_booking(message):

    chat_id=message.chat.id

    data=user_data[chat_id]

    counters=load_json("counters.json")

    booking_id=f"B{counters['booking']:03}"

    counters["booking"]+=1

    save_json("counters.json",counters)

    data["booking_id"]=booking_id

    bookings=load_json("bookings.json")

    bookings.append({
        "booking_id":booking_id,
        "chat_id":chat_id,
        "date":data["date"]
    })

    save_json("bookings.json",bookings)

    bot.send_message(
        chat_id,
        "Your request has been received.\nWe will contact you to confirm the time.",
        reply_markup=main_menu()
    )

    bot.send_message(
        ADMIN_ID,
f"""
NEW BOOKING

Booking {booking_id}

Client: {data['name']}
Phone: {data['phone']}
Address: {data['address']}

Service: {data['cleaning']}
Bedrooms: {data['bedrooms']}

Price: ${data['price']}
Date: {data['date']}
"""
    )

    user_data.pop(chat_id)

# ---------- INVOICE ----------

def create_invoice(data):

    counters=load_json("counters.json")

    invoice_id=f"INV{counters['invoice']:03}"

    counters["invoice"]+=1

    save_json("counters.json",counters)

    filename=f"{invoice_id}.pdf"

    c=canvas.Canvas(filename)

    c.drawImage("logo.png",200,750,width=200,height=80)

    c.setFont("Helvetica-Bold",18)
    c.drawString(50,700,"INVOICE")

    c.setFont("Helvetica",12)

    c.drawString(50,670,f"Invoice ID: {invoice_id}")
    c.drawString(50,650,f"Booking ID: {data['booking_id']}")

    c.drawString(50,620,f"Client: {data['name']}")
    c.drawString(50,600,f"Phone: {data['phone']}")
    c.drawString(50,580,f"Address: {data['address']}")

    c.drawString(50,540,f"Service: {data['cleaning']}")
    c.drawString(50,520,f"Bedrooms: {data['bedrooms']}")

    c.drawString(50,490,f"Total: ${data['price']}")

    c.drawCentredString(300,430,"Phone 2532020979")
    c.drawCentredString(300,410,"manager@excellentsolution.online")

    c.save()

    return filename

# ---------- REMINDER ----------

def reminder():

    bookings=load_json("bookings.json")

    now=datetime.now()

    for booking in bookings:

        date=datetime.strptime(booking["date"],"%Y-%m-%d")

        if date-timedelta(hours=24)<=now<=date-timedelta(hours=23):

            bot.send_message(
                booking["chat_id"],
                "Reminder\nYour cleaning is tomorrow"
            )

def scheduler():

    schedule.every(1).hours.do(reminder)

    while True:

        schedule.run_pending()
        time.sleep(10)

threading.Thread(target=scheduler).start()

bot.infinity_polling()
