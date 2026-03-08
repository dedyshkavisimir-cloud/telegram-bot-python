import json

BOOKINGS_FILE = "bookings.json"
COUNTERS_FILE = "counters.json"


def load_bookings():

    try:
        with open(BOOKINGS_FILE) as f:
            return json.load(f)
    except:
        return []


def save_bookings(data):

    with open(BOOKINGS_FILE, "w") as f:
        json.dump(data, f, indent=2)


def get_booking_counter():

    try:
        with open(COUNTERS_FILE) as f:
            data = json.load(f)
    except:
        data = {"booking": 1}

    booking = data["booking"]

    data["booking"] += 1

    with open(COUNTERS_FILE, "w") as f:
        json.dump(data, f, indent=2)

    return booking
