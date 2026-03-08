import telebot
from telebot import types
import os
import json
from datetime import datetime, timedelta
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
def prices(message):

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
"""
Cleaning Pros Team

Phone: 2532020979
Email: manager@excellentsolution.online
"""
    )

# ---------- BOOK ----------

@bot.message_handler(func=lambda m: m.text=="🧹 Book cleaning")
def book(message):

    chat_id = message.chat.id

    user_data[chat_id]={"step":"cleaning"}

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    markup.add("Regular cleaning")
    markup.add("Deep cleaning")
    markup.add("Move out cleaning")

    bot.send_message(chat_id,"Choose cleaning type",reply_markup=markup)

# ---------- FLOW ----------

@bot.message_handler(func=lambda message: message.chat.id in user_data)
def flow(message):

    chat_id = message.chat.id
    step = user_data[chat_id]["step"]

    if step=="cleaning":

        if message.text not in prices:
            return

        user_data[chat_id]["cleaning"]=message.text
        user_data[chat_id]["step"]="bedrooms"

        markup=types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("1","2","3")

        bot.send_message(chat_id,"How many bedrooms?",reply_markup=markup)

    elif step=="bedrooms":

        cleaning=user_data[chat_id]["cleaning"]
        bedrooms=message.text

        price=prices[cleaning][bedrooms]

        user_data[chat_id]["bedrooms"]=bedrooms
        user_data[chat_id]["price"]=price
        user_data[chat_id]["step"]="date"

        markup=types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("Tomorrow","In 2 days","In 3 days")

        bot.send_message(chat_id,f"Estimated price ${price}")
        bot.send_message(chat_id,"Choose cleaning date",reply_markup=markup)

    elif step=="date":

        today=datetime.today()

        if message.text=="Tomorrow":
            date=today+timedelta(days=1)

        elif message.text=="In 2 days":
            date=today+timedelta(days=2)

        else:
            date=today+timedelta(days=3)

        user_data[chat_id]["date"]=date.strftime("%B %d")
        user_data[chat_id]["step"]="address"

        bot.send_message(chat_id,"Send address")

    elif step=="address":

        user_data[chat_id]["address"]=message.text
        user_data[chat_id]["step"]="name"

        bot.send_message(chat_id,"Your name")

    elif step=="name":

        user_data[chat_id]["name"]=message.text
        user_data[chat_id]["step"]="phone"

        bot.send_message(chat_id,"Phone number")

    elif step=="phone":

        user_data[chat_id]["phone"]=message.text
        user_data[chat_id]["step"]="photo"

        markup=types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("Skip photo")

        bot.send_message(chat_id,"Send photos or Skip",reply_markup=markup)

    elif step=="photo":

        if message.text=="Skip photo":

            finalize_booking(chat_id)

# ---------- PHOTO ----------

@bot.message_handler(content_types=['photo'])
def photo(message):

    chat_id=message.chat.id

    if chat_id not in user_data:
        return

    bot.forward_message(ADMIN_ID,chat_id,message.message_id)

    finalize_booking(chat_id)

# ---------- FINALIZE ----------

def finalize_booking(chat_id):

    data=user_data[chat_id]

    counters=load_json("counters.json")

    booking_id=f"B{counters['booking']:03}"

    counters["booking"]+=1

    save_json("counters.json",counters)

    bookings=load_json("bookings.json")

    bookings.append({
        "booking_id":booking_id,
        "chat_id":chat_id,
        "name":data["name"],
        "phone":data["phone"],
        "date":data["date"],
        "price":data["price"]
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

{booking_id}

Client: {data['name']}
Phone: {data['phone']}
Date: {data['date']}
Price: ${data['price']}
"""
    )

    user_data.pop(chat_id)

# ---------- CANCEL ----------

@bot.message_handler(func=lambda m: m.text=="❌ Cancel booking")
def cancel(message):

    if message.chat.id in user_data:
        user_data.pop(message.chat.id)

    bot.send_message(
        message.chat.id,
        "Booking cancelled",
        reply_markup=main_menu()
    )

# ---------- CHANGE ----------

@bot.message_handler(func=lambda m: m.text=="📅 Change booking")
def change(message):

    book(message)

# ---------- ADMIN ----------

@bot.message_handler(commands=['admin'])
def admin(message):

    if message.from_user.id!=ADMIN_ID:
        return

    markup=types.ReplyKeyboardMarkup(resize_keyboard=True)

    markup.add("📋 Today")
    markup.add("📅 Tomorrow")
    markup.add("📂 All bookings")
    markup.add("💰 Income")

    bot.send_message(message.chat.id,"Admin panel",reply_markup=markup)

# ---------- TODAY ----------

@bot.message_handler(func=lambda m: m.text=="📋 Today")
def today(message):

    bookings=load_json("bookings.json")

    today=datetime.today().strftime("%B %d")

    text="TODAY BOOKINGS\n\n"

    for b in bookings:

        if b["date"]==today:

            text+=f"{b['booking_id']} {b['name']}\n"

    bot.send_message(message.chat.id,text)

# ---------- TOMORROW ----------

@bot.message_handler(func=lambda m: m.text=="📅 Tomorrow")
def tomorrow(message):

    bookings=load_json("bookings.json")

    tomorrow=(datetime.today()+timedelta(days=1)).strftime("%B %d")

    text="TOMORROW BOOKINGS\n\n"

    for b in bookings:

        if b["date"]==tomorrow:

            text+=f"{b['booking_id']} {b['name']}\n"

    bot.send_message(message.chat.id,text)

# ---------- ALL BOOKINGS ----------

@bot.message_handler(func=lambda m: m.text=="📂 All bookings")
def all_bookings(message):

    bookings=load_json("bookings.json")

    text="ALL BOOKINGS\n\n"

    for b in bookings:

        text+=f"{b['booking_id']} {b['date']} {b['name']}\n"

    bot.send_message(message.chat.id,text)

# ---------- INCOME ----------

@bot.message_handler(func=lambda m: m.text=="💰 Income")
def income(message):

    bookings=load_json("bookings.json")

    total=0

    for b in bookings:
        total+=b["price"]

    bot.send_message(message.chat.id,f"Total income ${total}")

bot.infinity_polling()
