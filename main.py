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
    try:
        with open(file) as f:
            return json.load(f)
    except:
        return []

def save_json(file,data):
    with open(file,"w") as f:
        json.dump(data,f,indent=2)

# ---------- MENU ----------

def main_menu(user_id=None):

    m = types.ReplyKeyboardMarkup(resize_keyboard=True)

    m.add("🧹 Book cleaning")
    m.add("💰 Prices","📞 Contact")
    m.add("📅 Change booking","❌ Cancel booking")

    if user_id == ADMIN_ID:
        m.add("⚙️ Admin panel")

    return m

# ---------- START ----------

@bot.message_handler(commands=['start'])
def start(message):

    bot.send_message(
        message.chat.id,
        "Welcome to Cleaning Pros Team! 🧼\n\nWhat type of cleaning do you need?",
        reply_markup=main_menu(message.from_user.id)
    )

# ---------- PRICES ----------

@bot.message_handler(func=lambda m: m.text=="💰 Prices")
def price(message):

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
""")

# ---------- BOOK ----------

@bot.message_handler(func=lambda m: m.text=="🧹 Book cleaning")
def book(message):

    chat_id=message.chat.id

    user_data[chat_id]={"step":"cleaning"}

    markup=types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Regular cleaning","Deep cleaning","Move out cleaning")

    bot.send_message(chat_id,"Choose cleaning type",reply_markup=markup)

# ---------- FLOW ----------

@bot.message_handler(func=lambda m: m.chat.id in user_data)
def flow(message):

    chat_id=message.chat.id
    step=user_data[chat_id]["step"]
    text=message.text

    if step=="cleaning":

        if text not in prices:
            return

        user_data[chat_id]["cleaning"]=text
        user_data[chat_id]["step"]="bedrooms"

        m=types.ReplyKeyboardMarkup(resize_keyboard=True)
        m.add("1","2","3")

        bot.send_message(chat_id,"How many bedrooms?",reply_markup=m)

    elif step=="bedrooms":

        if text not in ["1","2","3"]:
            return

        cleaning=user_data[chat_id]["cleaning"]
        price=prices[cleaning][text]

        user_data[chat_id]["bedrooms"]=text
        user_data[chat_id]["price"]=price
        user_data[chat_id]["step"]="date"

        bot.send_message(chat_id,f"Estimated price: ${price}")

        m=types.ReplyKeyboardMarkup(resize_keyboard=True)

        today=datetime.today()

        for i in range(1,5):
            d=today+timedelta(days=i)
            m.add(d.strftime("%b %d"))

        bot.send_message(chat_id,"Choose cleaning date",reply_markup=m)

    elif step=="date":

        user_data[chat_id]["date"]=text
        user_data[chat_id]["step"]="address"

        bot.send_message(chat_id,"Send address or location")

    elif step=="address":

        user_data[chat_id]["address"]=text
        user_data[chat_id]["step"]="name"

        bot.send_message(chat_id,"Your name")

    elif step=="name":

        user_data[chat_id]["name"]=text
        user_data[chat_id]["step"]="phone"

        bot.send_message(chat_id,"Phone number")

    elif step=="phone":

        user_data[chat_id]["phone"]=text
        user_data[chat_id]["step"]="photo"

        m=types.ReplyKeyboardMarkup(resize_keyboard=True)
        m.add("⏭ Skip photo")

        bot.send_message(chat_id,"Send photos or Skip",reply_markup=m)

    elif step=="photo":

        if text=="⏭ Skip photo":
            finalize(chat_id)

# ---------- PHOTO ----------

@bot.message_handler(content_types=['photo'])
def photo(message):

    chat_id=message.chat.id

    if chat_id not in user_data:
        return

    if user_data[chat_id]["step"]!="photo":
        return

    bot.forward_message(ADMIN_ID,chat_id,message.message_id)

    finalize(chat_id)

# ---------- FINALIZE ----------

def finalize(chat_id):

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

    location_link=f"https://maps.google.com/?q={data['address']}"

    bot.send_message(chat_id,
"We will contact you to confirm the time.",
    reply_markup=main_menu(chat_id)
)

    bot.send_message(
    ADMIN_ID,
f"""
🧼 NEW CLEANING REQUEST

Cleaning: {data['cleaning']}
Bedrooms: {data['bedrooms']}
Price: ${data['price']}

Location:
{location_link}

Phone:
{data['phone']}

Client:
{data['name']}
"""
)

    user_data.pop(chat_id)

# ---------- ADMIN PANEL ----------

@bot.message_handler(func=lambda m: m.text=="⚙️ Admin panel")
def admin(message):

    if message.from_user.id!=ADMIN_ID:
        return

    m=types.ReplyKeyboardMarkup(resize_keyboard=True)
    m.add("📋 Today","📅 Tomorrow")
    m.add("📂 All bookings")
    m.add("💰 Income")
    m.add("🧾 Send invoice")

    bot.send_message(message.chat.id,"Admin panel",reply_markup=m)

# ---------- TODAY ----------

@bot.message_handler(func=lambda m:m.text=="📋 Today")
def today(message):

    bookings=load_json("bookings.json")

    today=datetime.today().strftime("%b %d")

    text="TODAY BOOKINGS\n\n"

    for b in bookings:
        if b["date"]==today:
            text+=f"{b['booking_id']} {b['name']}\n"

    bot.send_message(message.chat.id,text)

# ---------- TOMORROW ----------

@bot.message_handler(func=lambda m:m.text=="📅 Tomorrow")
def tomorrow(message):

    bookings=load_json("bookings.json")

    tomorrow=(datetime.today()+timedelta(days=1)).strftime("%b %d")

    text="TOMORROW BOOKINGS\n\n"

    for b in bookings:
        if b["date"]==tomorrow:
            text+=f"{b['booking_id']} {b['name']}\n"

    bot.send_message(message.chat.id,text)

# ---------- ALL ----------

@bot.message_handler(func=lambda m:m.text=="📂 All bookings")
def all_bookings(message):

    bookings=load_json("bookings.json")

    text="ALL BOOKINGS\n\n"

    for b in bookings:
        text+=f"{b['booking_id']} {b['date']} {b['name']}\n"

    bot.send_message(message.chat.id,text)

# ---------- INCOME ----------

@bot.message_handler(func=lambda m:m.text=="💰 Income")
def income(message):

    bookings=load_json("bookings.json")

    total=sum(b["price"] for b in bookings)

    bot.send_message(message.chat.id,f"Total income ${total}")

# ---------- INVOICE ----------

@bot.message_handler(func=lambda m:m.text=="🧾 Send invoice")
def invoice_menu(message):

    bookings=load_json("bookings.json")

    m=types.ReplyKeyboardMarkup(resize_keyboard=True)

    for b in bookings[-10:]:
        m.add(b["booking_id"])

    bot.send_message(message.chat.id,"Choose booking",reply_markup=m)

@bot.message_handler(func=lambda m:m.text.startswith("B"))
def send_invoice(message):

    booking_id=message.text

    bookings=load_json("bookings.json")

    for b in bookings:

        if b["booking_id"]==booking_id:

            file=f"{booking_id}.pdf"

            c=canvas.Canvas(file)

            c.drawString(50,800,"Cleaning Pros Team")
            c.drawString(50,770,"Phone: 2532020979")
            c.drawString(50,750,"Email: manager@excellentsolution.online")

            c.drawString(50,700,f"Invoice {booking_id}")
            c.drawString(50,680,f"Client: {b['name']}")
            c.drawString(50,660,f"Phone: {b['phone']}")
            c.drawString(50,640,f"Date: {b['date']}")

            c.drawString(50,600,f"Total: ${b['price']}")

            c.save()

            with open(file,"rb") as f:
                bot.send_document(b["chat_id"],f)

            bot.send_message(message.chat.id,"Invoice sent")

            return

bot.infinity_polling()
