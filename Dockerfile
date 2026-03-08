FROM python:3.11

WORKDIR /app

COPY . .

RUN pip install pyTelegramBotAPI

CMD ["python", "main.py"]
