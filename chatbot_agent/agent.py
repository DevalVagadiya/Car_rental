import os
import django
import re
from datetime import datetime
import ollama

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myproject.settings")
django.setup()

from myapp.models import Vehicle, Booking, login_table, ChatMessage


# =====================================
# SYSTEM PROMPT (Smarter)
# =====================================
SYSTEM_PROMPT = """
You are an AI assistant for a professional car rental company.

Rules:
- Be clear, short, and professional.
- If question is about cars, pricing, booking, answer as company representative.
- If general knowledge, answer normally.
- If unsure, guide user politely.
"""


# =====================================
# MAIN FUNCTION
# =====================================
def get_response(user_id, message):

    try:
        user = login_table.objects.get(id=user_id)
    except login_table.DoesNotExist:
        return "User not found."

    ChatMessage.objects.create(user=user, message=message, response="")

    response = process_message(user, message)

    chat_message = ChatMessage.objects.filter(user=user, message=message).last()

    if chat_message:
        chat_message.response = response
        chat_message.save()

    return response


# =====================================
# SMART INTENT ROUTER
# =====================================
def process_message(user, message):

    msg = message.lower()

    # Greetings
    if re.search(r"\b(hello|hi|hey)\b", msg):
        return f"Hello {user.name}! How can I assist you today?"

    # Car Listing / Availability
    if re.search(r"\b(list|show|display|available)\b.*\b(car|cars)\b", msg) or \
       re.search(r"\b(car|cars)\b", msg):
        return handle_car_queries(msg)

    # Price Query (FULL WORD ONLY)
    if re.search(r"\b(price|cost|rent)\b", msg):
        return calculate_price(msg)

    # Booking Status
    if re.search(r"\b(booking\sstatus|my\sbooking|status)\b", msg):
        return check_booking_status(user)

    # Cancel Booking
    if re.search(r"\bcancel\b", msg):
        return cancel_booking(user)

    # Booking Request
    if re.search(r"\bbook\b", msg):
        return book_car(user, msg)

    # Thanks
    if re.search(r"\b(thank|thanks)\b", msg):
        return "You're welcome 😊"

    # If asking date/time → let AI answer
    if re.search(r"\b(date|time|today)\b", msg):
        return ai_fallback(message)

    return ai_fallback(message)


# =====================================
# CAR QUERY HANDLER (Smart Filtering)
# =====================================
def handle_car_queries(message):

    vehicles = Vehicle.objects.all()

    if "cheap" in message or "budget" in message:
        vehicles = vehicles.order_by("rent_perday")

    if "suv" in message:
        vehicles = vehicles.filter(model_name__icontains="suv")

    if "7" in message or "7-seater" in message:
        vehicles = vehicles.filter(seats__gte=7)

    if not vehicles.exists():
        return "No matching cars found."

    response = "Available cars:\n"

    for v in vehicles:
        response += f"- {v.company} {v.model_name} (${v.rent_perday}/day)\n"

    return response


# =====================================
# PRICE CALCULATION
# =====================================
def calculate_price(message):

    days_match = re.search(r"(\d+)\s*day", message)

    if not days_match:
        return "Please specify number of days (example: 3 days)."

    days = int(days_match.group(1))

    for vehicle in Vehicle.objects.all():
        if vehicle.model_name.lower() in message:
            total = vehicle.rent_perday * days
            return f"{vehicle.company} {vehicle.model_name} for {days} days will cost ${total}."

    return "Please mention a valid car name."


# =====================================
# BOOKING STATUS
# =====================================
def check_booking_status(user):

    bookings = Booking.objects.filter(user=user)

    if not bookings.exists():
        return "You have no bookings."

    response = "Your bookings:\n"

    for b in bookings:
        status = "Confirmed" if b.is_confirmed else "Pending"
        response += f"- {b.vehicle.model_name} ({b.booking_from} to {b.booking_to}) - {status}\n"

    return response


# =====================================
# CANCEL BOOKING
# =====================================
def cancel_booking(user):

    booking = Booking.objects.filter(user=user, is_confirmed=True).last()

    if not booking:
        return "You have no confirmed bookings."

    booking.is_confirmed = False
    booking.cancellation_status = "Yes"
    booking.save()

    return "Your latest booking has been cancelled."


# =====================================
# BOOK CAR (Regex Based Extraction)
# =====================================
def book_car(user, message):

    date_match = re.search(r"(\d{4}-\d{2}-\d{2})", message)

    if not date_match:
        return "Please provide booking dates in format YYYY-MM-DD to YYYY-MM-DD."

    dates = re.findall(r"\d{4}-\d{2}-\d{2}", message)

    if len(dates) != 2:
        return "Please provide start and end date."

    start_date = datetime.strptime(dates[0], "%Y-%m-%d")
    end_date = datetime.strptime(dates[1], "%Y-%m-%d")

    for vehicle in Vehicle.objects.all():
        if vehicle.model_name.lower() in message:
            overlapping = Booking.objects.filter(
                vehicle=vehicle,
                booking_from__lt=end_date,
                booking_to__gt=start_date
            )

            if overlapping.exists():
                return "Car is already booked for those dates."

            booking = Booking.objects.create(
                user=user,
                vehicle=vehicle,
                booking_from=start_date,
                booking_to=end_date,
                is_confirmed=True,
                payment_status="Pending"
            )

            days = (end_date - start_date).days
            booking.booking_amount = days * vehicle.rent_perday
            booking.save()

            return f"Booking confirmed for {vehicle.model_name}. Total cost: ${booking.booking_amount}"

    return "Please mention a valid car name."


# =====================================
# AI FALLBACK (Context Aware)
# =====================================
def ai_fallback(user_message):

    try:
        # Add available cars context
        car_data = ""
        for v in Vehicle.objects.all():
            car_data += f"{v.company} {v.model_name} (${v.rent_perday}/day), "

        response = ollama.chat(
            model="tinyllama",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "system", "content": f"Available cars: {car_data}"},
                {"role": "user", "content": user_message},
            ],
        )

        return response["message"]["content"]

    except Exception as e:
        print("AI Error:", e)
        return "I can help with rentals, bookings, pricing, and availability."