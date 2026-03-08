from reportlab.pdfgen import canvas
from config import COMPANY, PHONE, EMAIL


def create_invoice(booking):

    file = f"{booking['booking_id']}.pdf"

    c = canvas.Canvas(file)

    try:
        c.drawImage("logo.png", 40, 740, width=120, height=60)
    except:
        pass

    c.setFont("Helvetica-Bold", 22)
    c.drawString(200, 760, "INVOICE")

    c.setFont("Helvetica", 12)

    c.drawString(40, 700, COMPANY)
    c.drawString(40, 680, PHONE)
    c.drawString(40, 660, EMAIL)

    c.line(40, 640, 550, 640)

    c.drawString(40, 610, f"Invoice: {booking['booking_id']}")
    c.drawString(40, 590, f"Client: {booking['name']}")
    c.drawString(40, 570, f"Phone: {booking['phone']}")
    c.drawString(40, 550, f"Date: {booking['date']}")

    c.drawString(40, 500, f"Service: Cleaning")
    c.drawString(40, 480, f"Total: ${booking['price']}")

    c.save()

    return file
