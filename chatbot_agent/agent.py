import os
import django
import re
from datetime import datetime

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myproject.settings")
django.setup()

from myapp.models import Vehicle, Booking, login_table, ChatMessage

# Safely import ollama — not required for core features
try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False


# =====================================
# SYSTEM PROMPT
# =====================================
SYSTEM_PROMPT = """
You are a helpful assistant for Royal Cars, a professional car rental company in India.

Rules:
- All prices are in Indian Rupees (₹). Never use dollars ($).
- Be clear, concise, and professional.
- If asked about cars, pricing, bookings — answer as a company representative.
- For general questions (weather, general knowledge, etc.) — answer helpfully.
- If unsure, guide the user politely.
- Always respond in 2-3 sentences max unless listing items.
"""

# Simple in-memory context to handle multi-turn conversations
# Maps user_id -> {'last_intent': ..., 'pending_car': ...}
_user_context = {}


# =====================================
# MAIN FUNCTION
# =====================================
def get_response(user_id, message):
    try:
        user = login_table.objects.get(id=user_id)
    except login_table.DoesNotExist:
        return "User not found. Please log in again."

    # Save message first (response filled after)
    chat_entry = ChatMessage.objects.create(user=user, message=message, response="")

    response = process_message(user, message)

    chat_entry.response = response
    chat_entry.save()

    return response


# =====================================
# SMART INTENT ROUTER
# =====================================
def process_message(user, message):
    msg = message.lower().strip()
    ctx = _user_context.get(user.id, {})

    # ── Greetings ──
    if re.search(r"\b(hello|hi|hey|namaste)\b", msg):
        _user_context[user.id] = {}
        return f"Hello {user.name}! 👋 How can I assist you today?\nYou can ask me about available cars, pricing, bookings, or anything else."

    # ── Thanks ──
    if re.search(r"\b(thank|thanks|thank you|shukriya)\b", msg):
        _user_context[user.id] = {}
        return "You're welcome! 😊 Is there anything else I can help you with?"

    # ── Goodbye ──
    if re.search(r"\b(bye|goodbye|see you|ok bye)\b", msg):
        _user_context[user.id] = {}
        return "Goodbye! Have a great day! 🚗"

    # ── Pending context: waiting for days (price query) ──
    if ctx.get("last_intent") == "price_days_pending":
        days_match = re.search(r"(\d+)\s*day", msg)
        if days_match:
            days = int(days_match.group(1))
            car_name = ctx.get("pending_car")
            _user_context[user.id] = {}
            for vehicle in Vehicle.objects.all():
                if car_name and car_name in vehicle.model_name.lower():
                    total = vehicle.rent_perday * days
                    return f"{vehicle.company} {vehicle.model_name} for {days} days will cost ₹{total:,}.\n(₹{vehicle.rent_perday}/day × {days} days)"
            # No specific car — give all prices
            response = f"For {days} days, pricing for all cars:\n"
            for v in Vehicle.objects.all():
                response += f"- {v.company} {v.model_name}: ₹{v.rent_perday * days:,}\n"
            return response
        else:
            return "Please tell me the number of days (e.g., 'for 3 days')."

    # ── Pending context: waiting for car name (booking) ──
    if ctx.get("last_intent") == "book_car_name_pending":
        # Check if user mentioned a car name
        for vehicle in Vehicle.objects.all():
            if vehicle.model_name.lower() in msg or vehicle.company.lower() in msg:
                _user_context[user.id] = {"last_intent": "book_car_dates_pending", "pending_car": vehicle.model_name.lower()}
                return f"Great! You want to book {vehicle.company} {vehicle.model_name}.\nPlease provide the dates in format: YYYY-MM-DD to YYYY-MM-DD"
        return "I couldn't find that car. Please choose from our available cars:\n" + _list_cars()

    # ── Pending context: waiting for dates (booking) ──
    if ctx.get("last_intent") == "book_car_dates_pending":
        result = book_car(user, msg, ctx.get("pending_car"))
        if "confirmed" in result.lower() or "booked" in result.lower() or "already" in result.lower():
            _user_context[user.id] = {}
        return result

    # ── Cancel Booking ──
    if re.search(r"\bcancel\b", msg):
        _user_context[user.id] = {}
        return cancel_booking(user, msg)

    # ── Car Listing / Availability ──
    if re.search(r"\b(list|show|display|available|which)\b.*\b(car|cars|vehicle)\b", msg) or \
       re.search(r"\ball\s*(the\s*)?(car|cars|vehicle)\b", msg):
        _user_context[user.id] = {}
        return handle_car_queries(msg)

    # ── Price / Cost Query ──
    if re.search(r"\b(price|cost|rent|rate|charge|how much)\b", msg):
        return calculate_price(user, msg)

    # ── Booking Status ──
    if re.search(r"\b(booking\s+status|my\s+booking|my\s+bookings|status)\b", msg):
        _user_context[user.id] = {}
        return check_booking_status(user)

    # ── Booking Request ──
    if re.search(r"\bbook\b", msg):
        return book_car(user, msg)

    # ── General questions — use AI or simple answers ──
    return smart_general_response(user, message)


# =====================================
# CAR LISTING HELPER
# =====================================
def _list_cars():
    vehicles = Vehicle.objects.all()
    if not vehicles.exists():
        return "No cars available at the moment."
    result = ""
    for v in vehicles:
        result += f"- {v.company} {v.model_name} (₹{v.rent_perday}/day)\n"
    return result


# =====================================
# CAR QUERY HANDLER
# =====================================
def handle_car_queries(message):
    vehicles = Vehicle.objects.all()

    if "cheap" in message or "budget" in message or "affordable" in message:
        vehicles = vehicles.order_by("rent_perday")
    elif "expensive" in message or "luxury" in message or "premium" in message:
        vehicles = vehicles.order_by("-rent_perday")

    if "suv" in message:
        vehicles = vehicles.filter(model_name__icontains="suv")

    if "7" in message or "7-seater" in message or "seven" in message:
        vehicles = vehicles.filter(seats__gte=7)

    if not vehicles.exists():
        return "No matching cars found. Try asking for all available cars."

    response = "Available cars:\n"
    for v in vehicles:
        response += f"- {v.company} {v.model_name} (₹{v.rent_perday}/day)\n"
    return response


# =====================================
# PRICE CALCULATION (Multi-turn aware)
# =====================================
def calculate_price(user, message):
    days_match = re.search(r"(\d+)\s*day", message)
    days = int(days_match.group(1)) if days_match else None

    # Find if a car name is mentioned
    matched_vehicle = None
    for vehicle in Vehicle.objects.all():
        if vehicle.model_name.lower() in message or vehicle.company.lower() in message:
            matched_vehicle = vehicle
            break

    if matched_vehicle and days:
        total = matched_vehicle.rent_perday * days
        _user_context[user.id] = {}
        return (f"{matched_vehicle.company} {matched_vehicle.model_name} for {days} days will cost "
                f"₹{total:,}.\n(₹{matched_vehicle.rent_perday}/day × {days} days)")

    if matched_vehicle and not days:
        # Remember car, ask for days
        _user_context[user.id] = {"last_intent": "price_days_pending", "pending_car": matched_vehicle.model_name.lower()}
        return f"The rent for {matched_vehicle.company} {matched_vehicle.model_name} is ₹{matched_vehicle.rent_perday}/day.\nHow many days do you need it? (e.g., 'for 3 days')"

    if not matched_vehicle and days:
        # Give all prices for those days
        _user_context[user.id] = {}
        response = f"For {days} days, here are all available cars:\n"
        for v in Vehicle.objects.all():
            response += f"- {v.company} {v.model_name}: ₹{v.rent_perday * days:,}\n"
        return response

    # No car, no days — ask for clarification
    _user_context[user.id] = {"last_intent": "price_days_pending", "pending_car": None}
    return "Sure! Which car are you interested in, and for how many days?\n\nOur cars:\n" + _list_cars()


# =====================================
# BOOKING STATUS
# =====================================
def check_booking_status(user):
    bookings = Booking.objects.filter(user=user).order_by('-booking_from')

    if not bookings.exists():
        return "You have no bookings yet."

    response = "Your bookings:\n"
    for b in bookings:
        if b.cancellation_status == "Cancelled":
            booking_label = "❌ Cancelled"
        elif b.is_confirmed and b.payment_status in ["Done", "Offline"]:
            booking_label = "✅ Confirmed (Paid)"
        elif b.is_confirmed:
            booking_label = "📋 Booked (Payment Pending)"
        else:
            booking_label = "⏳ Pending"

        # Format dates cleanly
        date_from = b.booking_from.strftime("%d %b %Y") if hasattr(b.booking_from, 'strftime') else str(b.booking_from)[:10]
        date_to = b.booking_to.strftime("%d %b %Y") if hasattr(b.booking_to, 'strftime') else str(b.booking_to)[:10]

        response += f"- {b.vehicle.company} {b.vehicle.model_name}: {date_from} → {date_to}\n  Status: {booking_label} | Payment: {b.payment_status}\n"
    return response


# =====================================
# CANCEL BOOKING
# =====================================
def cancel_booking(user, message=""):
    bookings = Booking.objects.filter(user=user, is_confirmed=True).exclude(cancellation_status="Cancelled")

    if not bookings.exists():
        return "You have no active bookings to cancel."

    # Try to match car name in message
    for booking in bookings:
        if booking.vehicle.model_name.lower() in message or booking.vehicle.company.lower() in message:
            booking.cancellation_status = "Cancelled"
            booking.is_confirmed = False
            booking.save()
            return f"Your booking for {booking.vehicle.company} {booking.vehicle.model_name} has been cancelled."

    # Cancel latest
    latest = bookings.last()
    latest.cancellation_status = "Cancelled"
    latest.is_confirmed = False
    latest.save()
    return f"Your latest booking ({latest.vehicle.company} {latest.vehicle.model_name}) has been cancelled."


# =====================================
# BOOK CAR
# =====================================
def book_car(user, message, car_hint=None):
    dates = re.findall(r"\d{4}-\d{2}-\d{2}", message)

    if len(dates) < 2:
        # Check if car is mentioned
        for vehicle in Vehicle.objects.all():
            if vehicle.model_name.lower() in message or vehicle.company.lower() in message:
                _user_context[user.id] = {"last_intent": "book_car_dates_pending", "pending_car": vehicle.model_name.lower()}
                return f"Please provide the booking dates for {vehicle.company} {vehicle.model_name} in format:\nYYYY-MM-DD to YYYY-MM-DD"
        # No car and no dates
        _user_context[user.id] = {"last_intent": "book_car_name_pending"}
        return "Which car would you like to book?\n\n" + _list_cars()

    start_date = datetime.strptime(dates[0], "%Y-%m-%d")
    end_date = datetime.strptime(dates[1], "%Y-%m-%d")

    if end_date <= start_date:
        return "End date must be after start date. Please provide valid dates."

    # Find car in message or use hint
    search_text = message if not car_hint else message + " " + car_hint
    for vehicle in Vehicle.objects.all():
        if vehicle.model_name.lower() in search_text or vehicle.company.lower() in search_text:
            overlapping = Booking.objects.filter(
                vehicle=vehicle,
                booking_from__lt=end_date,
                booking_to__gt=start_date
            )
            if overlapping.exists():
                return f"Sorry, {vehicle.company} {vehicle.model_name} is already booked for those dates. Please choose different dates or another car."

            days = (end_date - start_date).days
            amount = days * vehicle.rent_perday

            booking = Booking.objects.create(
                user=user,
                vehicle=vehicle,
                booking_from=start_date,
                booking_to=end_date,
                is_confirmed=True,   # Booking is recorded
                payment_status="Pending",
                payment_mode="offline",
                booking_amount=amount
            )
            _user_context[user.id] = {}
            return (f"📋 Booking Received!\n"
                    f"Car: {vehicle.company} {vehicle.model_name}\n"
                    f"Dates: {dates[0]} to {dates[1]} ({days} days)\n"
                    f"Total: ₹{amount:,}\n"
                    f"Payment: Pending — please complete payment on the bookings page.")

    return "Please mention a valid car name. Type 'list cars' to see available cars."


# =====================================
# SMART GENERAL RESPONSE (AI or rule-based)
# =====================================
def smart_general_response(user, user_message):
    msg = user_message.lower()

    # Rule-based quick answers (no AI needed)
    if re.search(r"\b(who are you|what are you|your name)\b", msg):
        return "I'm the Royal Cars AI Assistant 🚗. I can help you with car rentals, bookings, pricing, and general questions!"

    if re.search(r"\b(contact|phone|number|email|address)\b", msg):
        return "You can contact Royal Cars at our office or use the Contact page on our website. Is there anything specific I can help you with?"

    if re.search(r"\b(payment|pay|upi|card|cash|online)\b", msg):
        return "We accept online payments (UPI, Card) and offline cash payments. Payment details are provided at the time of booking."

    if re.search(r"\b(fuel|petrol|diesel|cng|electric)\b", msg):
        return "Our fleet includes petrol, diesel, and CNG vehicles. Would you like to see cars filtered by fuel type?"

    if re.search(r"\b(help|what can you do|features|options)\b", msg):
        return ("I can help you with:\n"
                "🚗 List available cars\n"
                "💰 Check prices & calculate costs\n"
                "📅 Book a car\n"
                "📋 Check booking status\n"
                "❌ Cancel a booking\n"
                "💬 Answer general questions\n\n"
                "What would you like to do?")

    # Try Ollama AI for truly general questions
    if OLLAMA_AVAILABLE:
        return ai_fallback(user, user_message)

    # Friendly fallback when Ollama is not available
    return ("I'm not sure about that, but I'm here to help with car rentals! 😊\n"
            "You can ask me about available cars, pricing, bookings, or type 'help' for options.")


# =====================================
# AI FALLBACK (Ollama)
# =====================================
def ai_fallback(user, user_message):
    try:
        car_data = ""
        for v in Vehicle.objects.all():
            car_data += f"{v.company} {v.model_name} (₹{v.rent_perday}/day), "

        response = ollama.chat(
            model="tinyllama",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "system", "content": f"Available cars at Royal Cars: {car_data}"},
                {"role": "user", "content": user_message},
            ],
        )
        return response["message"]["content"]

    except Exception as e:
        print("AI Error:", e)
        return ("I can help with car rentals, bookings, pricing, and availability. "
                "Type 'help' to see what I can do!")