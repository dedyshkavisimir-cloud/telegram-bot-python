from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter


def create_invoice(data, filename):

    styles = getSampleStyleSheet()

    story = []

    try:
        logo = Image("logo.png", width=120, height=120)
        story.append(logo)
    except:
        pass

    story.append(Spacer(1,20))

    story.append(Paragraph("Cleaning Pros Team", styles["Title"]))
    story.append(Spacer(1,20))

    story.append(Paragraph(f"Client: {data['name']}", styles["Normal"]))
    story.append(Paragraph(f"Phone: {data['phone']}", styles["Normal"]))
    story.append(Paragraph(f"Address: {data['address']}", styles["Normal"]))

    story.append(Spacer(1,20))

    story.append(Paragraph(f"Service: {data['cleaning']}", styles["Normal"]))
    story.append(Paragraph(f"Bedrooms: {data['bedrooms']}", styles["Normal"]))
    story.append(Paragraph(f"Date: {data['date']}", styles["Normal"]))
    story.append(Paragraph(f"Extras: {data['extras']}", styles["Normal"]))

    story.append(Spacer(1,20))

    story.append(Paragraph(f"Total: ${data['price']}", styles["Heading2"]))

    pdf = SimpleDocTemplate(filename, pagesize=letter)

    pdf.build(story)
