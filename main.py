import telebot
from telebot import types
import os
import json
from datetime import datetime, timedelta
from reportlab.pdfgen import canvas

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_ID = 146998462

bot = telebot.TeleBot(TOKEN, parse_mode=None)

# ---------- DATA ----------

user_data = {}

prices = {
    "Regular cleaning": {"1":120,"2":150,"3":180},
    "Deep cleaning": {"1":180,"2":220,"3":260},
    "Move out cleaning": {"1":200,"2":250,"3":300}
}

# ---------- JSON ----------

def load_json(file):
    try:
        with open(file) as f:
            return json.load(f)
    except:
        return []

def save_json(file,data):
    with open(file,"w") as f:
        json.dump(data,f,indent=2)

# ---------- MENU ----------

def main_menu():
    m = types.ReplyKeyboardMarkup(resize_keyboard=True)
    m.add("🧹 Book cleaning")
    m.add("💰 Prices","📞 Contact")
    m.add("📅 Change booking","❌ Cancel booking")
    return m

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

    bot.send_message(message.chat.id,
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

    user_data[chat_id] = {"step":"cleaning"}

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Regular cleaning")
    markup.add("Deep cleaning")
    markup.add("Move out cleaning")

    bot.send_message(chat_id,"Choose cleaning type",reply_markup=markup)

# ---------- FLOW ----------

@bot.message_handler(func=lambda m: m.chat.id in user_data)
def flow(message):

    chat_id = message.chat.id
    step = user_data[chat_id]["step"]

    text = (message.text or "").strip()

    # cleaning
    if step=="cleaning":

        if text not in prices:
            bot.send_message(chat_id,"Choose cleaning type from buttons")
            return

        user_data[chat_id]["cleaning"] = text
        user_data[chat_id]["step"] = "bedrooms"

        m = types.ReplyKeyboardMarkup(resize_keyboard=True)
        m.add("1","2","3")

        bot.send_message(chat_id,"How many bedrooms?",reply_markup=m)
        return

    # bedrooms
    if step=="bedrooms":

        if text not in ["1","2","3"]:
            bot.send_message(chat_id,"Choose bedrooms from buttons")
            return

        cleaning = user_data[chat_id]["cleaning"]
        price = prices[cleaning][text]

        user_data[chat_id]["bedrooms"] = text
        user_data[chat_id]["price"] = price
        user_data[chat_id]["step"] = "date"

        bot.send_message(chat_id,f"Estimated price ${price}")

        m = types.ReplyKeyboardMarkup(resize_keyboard=True)

        today = datetime.today()

        for i in range(1,5):
            d = today + timedelta(days=i)
            m.add(d.strftime("%b %d"))

        bot.send_message(chat_id,"Choose cleaning date",reply_markup=m)
        return

    # date
    if step=="date":

        user_data[chat_id]["date"] = text
        user_data[chat_id]["step"] = "address"

        bot.send_message(chat_id,"Send address")
        return

    # address
    if step=="address":

        user_data[chat_id]["address"] = text
        user_data[chat_id]["step"] = "name"

        bot.send_message(chat_id,"Your name")
        return

    # name
    if step=="name":

        user_data[chat_id]["name"] = text
        user_data[chat_id]["step"] = "phone"

        bot.send_message(chat_id,"Phone number")
        return

    # phone
    if step=="phone":

        user_data[chat_id]["phone"] = text
        user_data[chat_id]["step"] = "photo"

        m = types.ReplyKeyboardMarkup(resize_keyboard=True)
        m.add("⏭ Skip photo")

        bot.send_message(chat_id,"Send photos or Skip",reply_markup=m)
        return

    # skip photo
    if step=="photo":

        if text == "⏭ Skip photo":
            finalize_booking(chat_id)
            return

# ---------- PHOTO ----------

@bot.message_handler(content_types=['photo'])
def photo(message):

    chat_id = message.chat.id

    if chat_id not in user_data:
        return

    if user_data[chat_id]["step"] != "photo":
        return

    bot.forward_message(ADMIN_ID,chat_id,message.message_id)

    finalize_booking(chat_id)

# ---------- FINALIZE ----------

def finalize_booking(chat_id):

    data = user_data[chat_id]

    counters = load_json("counters.json")

    booking_id = f"B{counters['booking']:03}"

    counters["booking"] += 1
    save_json("counters.json",counters)

    bookings = load_json("bookings.json")

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
{data['name']}
{data['phone']}
{data['date']}
${data['price']}
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

    if message.from_user.id != ADMIN_ID:
        return

    m = types.ReplyKeyboardMarkup(resize_keyboard=True)
    m.add("📋 Today")
    m.add("📅 Tomorrow")
    m.add("📂 All bookings")
    m.add("💰 Income")

    bot.send_message(message.chat.id,"Admin panel",reply_markup=m)

# ---------- TODAY ----------

@bot.message_handler(func=lambda m: m.text=="📋 Today")
def today(message):

    bookings = load_json("bookings.json")
    today = datetime.today().strftime("%b %d")

    text="TODAY BOOKINGS\n\n"

    for b in bookings:
        if b["date"]==today:
            text+=f"{b['booking_id']} {b['name']}\n"

    bot.send_message(message.chat.id,text)

# ---------- TOMORROW ----------

@bot.message_handler(func=lambda m: m.text=="📅 Tomorrow")
def tomorrow(message):

    bookings = load_json("bookings.json")
    tomorrow=(datetime.today()+timedelta(days=1)).strftime("%b %d")

    text="TOMORROW BOOKINGS\n\n"

    for b in bookings:
        if b["date"]==tomorrow:
            text+=f"{b['booking_id']} {b['name']}\n"

    bot.send_message(message.chat.id,text)

# ---------- ALL ----------

@bot.message_handler(func=lambda m: m.text=="📂 All bookings")
def all_bookings(message):

    bookings = load_json("bookings.json")

    text="ALL BOOKINGS\n\n"

    for b in bookings:
        text+=f"{b['booking_id']} {b['date']} {b['name']}\n"

    bot.send_message(message.chat.id,text)

# ---------- INCOME ----------

@bot.message_handler(func=lambda m: m.text=="💰 Income")
def income(message):

    bookings = load_json("bookings.json")

    total = sum(b["price"] for b in bookings)

    bot.send_message(message.chat.id,f"Total income ${total}")

# ---------- INVOICE ----------

@bot.message_handler(commands=['invoice'])
def send_invoice(message):

    if message.from_user.id != ADMIN_ID:
        return

    args = message.text.split()

    if len(args) < 2:
        bot.send_message(message.chat.id,"Usage: /invoice B001")
        return

    booking_id = args[1]

    bookings = load_json("bookings.json")

    for b in bookings:

        if b["booking_id"] == booking_id:

            filename=f"{booking_id}.pdf"

            c = canvas.Canvas(filename)

            c.drawString(50,800,"Cleaning Pros Team Invoice")
            c.drawString(50,760,f"Booking: {booking_id}")
            c.drawString(50,740,f"Client: {b['name']}")
            c.drawString(50,720,f"Phone: {b['phone']}")
            c.drawString(50,700,f"Date: {b['date']}")
            c.drawString(50,680,f"Total: ${b['price']}")

            c.save()

            with open(filename,"rb") as f:
                bot.send_document(b["chat_id"],f)

            bot.send_message(message.chat.id,"Invoice sent")
            return

    bot.send_message(message.chat.id,"Booking not found")

bot.infinity_polling()
