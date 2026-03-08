import json

BOOKINGS_FILE = "bookings.json"


def load_bookings():

    try:
        with open(BOOKINGS_FILE, "r") as f:
            return json.load(f)

    except:
        return []


def save_bookings(bookings):

    with open(BOOKINGS_FILE, "w") as f:
        json.dump(bookings, f, indent=4)
