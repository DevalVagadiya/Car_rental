import os
import django
import re
from datetime import datetime

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myproject.settings")
django.setup()

from myapp.models import Vehicle, Booking, login_table, ChatMessage

try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

# Per-user conversation context
_user_context = {}


# ─────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────

def _list_cars():
    vehicles = Vehicle.objects.all()
    if not vehicles.exists():
        return "No cars available at the moment."
    return "".join(f"- {v.company} {v.model_name} (₹{v.rent_perday}/day)\n" for v in vehicles)


def _find_vehicle(text):
    """Return first Vehicle whose model or company name appears in text."""
    for v in Vehicle.objects.all():
        if v.model_name.lower() in text or v.company.lower() in text:
            return v
    return None


def _parse_dates(text):
    """
    Accept both DD-MM-YYYY and YYYY-MM-DD formats.
    Returns list of datetime objects (up to 2).
    """
    dates = []
    # DD-MM-YYYY or DD/MM/YYYY
    for m in re.finditer(r"(\d{2})[-/](\d{2})[-/](\d{4})", text):
        try:
            dates.append(datetime(int(m.group(3)), int(m.group(2)), int(m.group(1))))
        except ValueError:
            pass
    # YYYY-MM-DD
    for m in re.finditer(r"(\d{4})-(\d{2})-(\d{2})", text):
        try:
            dates.append(datetime(int(m.group(1)), int(m.group(2)), int(m.group(3))))
        except ValueError:
            pass
    return dates[:2]


def _fmt_date(dt):
    return dt.strftime("%d-%m-%Y")


# ─────────────────────────────────────────
# MAIN ENTRY
# ─────────────────────────────────────────

def get_response(user_id, message):
    try:
        user = login_table.objects.get(id=user_id)
    except login_table.DoesNotExist:
        return "User not found. Please log in again."

    entry = ChatMessage.objects.create(user=user, message=message, response="")
    response = process_message(user, message)
    entry.response = response
    entry.save()
    return response


# ─────────────────────────────────────────
# ROUTER
# ─────────────────────────────────────────

def process_message(user, message):
    msg = message.lower().strip()
    ctx = _user_context.get(user.id, {})

    # ── Greetings ──
    if re.search(r"\b(hello|hi|hey|namaste)\b", msg):
        _user_context[user.id] = {}
        return (f"Hello {user.name}! 👋 How can I assist you today?\n"
                "You can ask me about available cars, pricing, bookings, features, or city availability.")

    # ── Thanks ──
    if re.search(r"\b(thank|thanks|thank you)\b", msg):
        _user_context[user.id] = {}
        return "You're welcome! 😊 Anything else I can help with?"

    # ── Bye ──
    if re.search(r"\b(bye|goodbye|see you)\b", msg):
        _user_context[user.id] = {}
        return "Goodbye! Have a great day! 🚗"

    # ─── MULTI-TURN: price — waiting for days ───
    if ctx.get("last_intent") == "price_days_pending":
        m = re.search(r"(\d+)\s*day", msg)
        if m:
            days = int(m.group(1))
            car_name = ctx.get("pending_car")
            _user_context[user.id] = {}
            for v in Vehicle.objects.all():
                if car_name and car_name in v.model_name.lower():
                    total = v.rent_perday * days
                    return f"{v.company} {v.model_name} for {days} days = ₹{total:,}\n(₹{v.rent_perday}/day × {days} days)"
            resp = f"For {days} days:\n"
            for v in Vehicle.objects.all():
                resp += f"- {v.company} {v.model_name}: ₹{v.rent_perday * days:,}\n"
            return resp
        return "Please tell me the number of days (e.g., 'for 3 days')."

    # ─── MULTI-TURN: booking — waiting for car name ───
    if ctx.get("last_intent") == "book_car_name_pending":
        v = _find_vehicle(msg)
        if v:
            _user_context[user.id] = {"last_intent": "book_car_dates_pending", "pending_car": v.model_name.lower()}
            return (f"Great! You want to book {v.company} {v.model_name}.\n"
                    "Please provide the dates:\nDD-MM-YYYY to DD-MM-YYYY")
        return "I couldn't find that car. Available cars:\n" + _list_cars()

    # ─── MULTI-TURN: booking — waiting for dates ───
    if ctx.get("last_intent") == "book_car_dates_pending":
        dates = _parse_dates(msg)
        if len(dates) == 2:
            result = _do_booking(user, dates[0], dates[1], ctx.get("pending_car"))
            _user_context[user.id] = {}
            return result
        return ("Please send the dates in format DD-MM-YYYY to DD-MM-YYYY\n"
                "Example: 15-07-2026 to 18-07-2026")

    # ── Cancel ──
    if re.search(r"\bcancel\b", msg):
        _user_context[user.id] = {}
        return cancel_booking(user, msg)

    # ── Features / Specs of a car ──
    if re.search(r"\b(feature|features|detail|details|spec|specs|info|information|about)\b", msg):
        v = _find_vehicle(msg)
        if v:
            _user_context[user.id] = {}
            return car_features(v)
        # generic features question
        return ("I can show you details for any of our cars:\n" + _list_cars() +
                "\nAsk: 'features of Toyota Innova'")

    # ── City / availability query ──
    if re.search(r"\b(available|availability|in my city|in city|my area|my location)\b", msg):
        v = _find_vehicle(msg)
        if v:
            _user_context[user.id] = {}
            return (f"{v.company} {v.model_name} is available in:\n"
                    f"📍 Location: {v.location}\n"
                    f"🏘 Area: {v.area}\n"
                    f"🏙 City: {v.city}\n"
                    f"🗺 State: {v.state}\n"
                    f"💰 Rent: ₹{v.rent_perday}/day\n"
                    "To book, type: 'book [car name]'")
        # No car mentioned — list all with cities
        _user_context[user.id] = {}
        return handle_city_listing()

    # ── Car Listing ──
    if re.search(r"\b(list|show|display|which|what)\b.*\b(car|cars|vehicle|vehicles)\b", msg) or \
       re.search(r"\ball\s*(the\s*)?(car|cars|vehicle)\b", msg) or \
       re.search(r"\b(latest|new|current|stock)\b.*\b(car|model)\b", msg):
        _user_context[user.id] = {}
        return handle_car_queries(msg)

    # ── Price ──
    if re.search(r"\b(price|cost|rent|rate|charge|how much|on.road)\b", msg):
        return calculate_price(user, msg)

    # ── Booking status ──
    if re.search(r"\b(booking\s+status|my\s+booking|my\s+bookings|status)\b", msg):
        _user_context[user.id] = {}
        return check_booking_status(user)

    # ── Book ──
    if re.search(r"\bbook\b", msg):
        return book_car(user, msg)

    # ── Test drive ──
    if re.search(r"\btest\s*drive\b", msg):
        _user_context[user.id] = {}
        return ("We offer car rentals, not test drives.\n"
                "You can rent any car for a day to experience it! 🚗\n"
                "Type 'book [car name]' to get started.")

    # ── General Q&A ──
    return general_qa(user, msg, message)


# ─────────────────────────────────────────
# CAR FEATURES
# ─────────────────────────────────────────

def car_features(v):
    return (f"🚗 {v.company} {v.model_name}\n"
            f"📅 Model Year: {v.model_year}\n"
            f"💰 Rent: ₹{v.rent_perday}/day\n"
            f"📍 Location: {v.location}\n"
            f"🏘 Area: {v.area}\n"
            f"🏙 City: {v.city}\n"
            f"🗺 State: {v.state}\n"
            "To book this car, type: 'book [car name]'")


# ─────────────────────────────────────────
# CITY LISTING
# ─────────────────────────────────────────

def handle_city_listing():
    vehicles = Vehicle.objects.all()
    if not vehicles.exists():
        return "No cars available."
    resp = "Our cars and their locations:\n"
    for v in vehicles:
        resp += f"- {v.company} {v.model_name} → {v.city} (₹{v.rent_perday}/day)\n"
    return resp


# ─────────────────────────────────────────
# CAR LISTING
# ─────────────────────────────────────────

def handle_car_queries(message):
    vehicles = Vehicle.objects.all()

    if any(w in message for w in ["cheap", "budget", "affordable", "low price"]):
        vehicles = vehicles.order_by("rent_perday")
    elif any(w in message for w in ["expensive", "luxury", "premium", "high"]):
        vehicles = vehicles.order_by("-rent_perday")

    if "latest" in message or "new" in message:
        vehicles = vehicles.order_by("-model_year")

    if not vehicles.exists():
        return "No matching cars found."

    resp = "Available cars:\n"
    for v in vehicles:
        resp += f"- {v.company} {v.model_name} ({v.model_year}) — ₹{v.rent_perday}/day | {v.city}\n"
    return resp


# ─────────────────────────────────────────
# PRICE CALC
# ─────────────────────────────────────────

def calculate_price(user, message):
    m = re.search(r"(\d+)\s*day", message)
    days = int(m.group(1)) if m else None
    matched = _find_vehicle(message)

    if matched and days:
        _user_context[user.id] = {}
        total = matched.rent_perday * days
        return (f"{matched.company} {matched.model_name} for {days} days = ₹{total:,}\n"
                f"(₹{matched.rent_perday}/day × {days} days)")

    if matched:
        _user_context[user.id] = {"last_intent": "price_days_pending", "pending_car": matched.model_name.lower()}
        return (f"{matched.company} {matched.model_name}: ₹{matched.rent_perday}/day\n"
                "How many days do you need it? (e.g., 'for 3 days')")

    if days:
        _user_context[user.id] = {}
        resp = f"For {days} days:\n"
        for v in Vehicle.objects.all():
            resp += f"- {v.company} {v.model_name}: ₹{v.rent_perday * days:,}\n"
        return resp

    _user_context[user.id] = {"last_intent": "price_days_pending", "pending_car": None}
    return "Which car and how many days?\n\nOur cars:\n" + _list_cars()


# ─────────────────────────────────────────
# BOOKING STATUS
# ─────────────────────────────────────────

def check_booking_status(user):
    bookings = Booking.objects.filter(user=user).order_by("-booking_from")
    if not bookings.exists():
        return "You have no bookings yet."

    resp = "Your bookings:\n"
    for b in bookings:
        if b.cancellation_status == "Cancelled":
            label = "❌ Cancelled"
        elif b.is_confirmed and b.payment_status in ["Done", "Offline"]:
            label = "✅ Confirmed (Paid)"
        elif b.is_confirmed:
            label = "📋 Booked (Payment Pending)"
        else:
            label = "⏳ Pending"

        df = b.booking_from.strftime("%d-%m-%Y") if hasattr(b.booking_from, "strftime") else str(b.booking_from)[:10]
        dt = b.booking_to.strftime("%d-%m-%Y") if hasattr(b.booking_to, "strftime") else str(b.booking_to)[:10]
        resp += f"- {b.vehicle.company} {b.vehicle.model_name}: {df} → {dt}\n  {label} | Payment: {b.payment_status}\n"
    return resp


# ─────────────────────────────────────────
# CANCEL
# ─────────────────────────────────────────

def cancel_booking(user, message=""):
    bookings = Booking.objects.filter(user=user, is_confirmed=True).exclude(cancellation_status="Cancelled")
    if not bookings.exists():
        return "You have no active bookings to cancel."

    for b in bookings:
        if b.vehicle.model_name.lower() in message or b.vehicle.company.lower() in message:
            b.cancellation_status = "Cancelled"
            b.is_confirmed = False
            b.save()
            return f"Booking for {b.vehicle.company} {b.vehicle.model_name} has been cancelled."

    latest = bookings.last()
    latest.cancellation_status = "Cancelled"
    latest.is_confirmed = False
    latest.save()
    return f"Your latest booking ({latest.vehicle.company} {latest.vehicle.model_name}) has been cancelled."


# ─────────────────────────────────────────
# BOOK CAR (entry point)
# ─────────────────────────────────────────

def book_car(user, message, car_hint=None):
    msg = message.lower()
    dates = _parse_dates(msg)
    v = _find_vehicle(msg) or (
        _find_vehicle(car_hint) if car_hint else None
    )

    if len(dates) == 2 and v:
        _user_context[user.id] = {}
        return _do_booking(user, dates[0], dates[1], v.model_name.lower())

    if v and len(dates) < 2:
        _user_context[user.id] = {"last_intent": "book_car_dates_pending", "pending_car": v.model_name.lower()}
        return (f"Please provide the booking dates for {v.company} {v.model_name}:\n"
                "DD-MM-YYYY to DD-MM-YYYY\nExample: 15-07-2026 to 18-07-2026")

    if len(dates) == 2 and not v:
        _user_context[user.id] = {"last_intent": "book_car_name_pending",
                                   "pending_dates": [_fmt_date(d) for d in dates]}
        return "Which car would you like to book?\n\n" + _list_cars()

    _user_context[user.id] = {"last_intent": "book_car_name_pending"}
    return "Which car would you like to book?\n\n" + _list_cars()


def _do_booking(user, start_date, end_date, car_name_hint):
    if end_date <= start_date:
        return "End date must be after start date. Please provide valid dates."

    v = _find_vehicle(car_name_hint) if car_name_hint else None
    if not v:
        return "Please mention a valid car name. Type 'list cars' to see available cars."

    overlap = Booking.objects.filter(
        vehicle=v, booking_from__lt=end_date, booking_to__gt=start_date
    )
    if overlap.exists():
        return (f"Sorry, {v.company} {v.model_name} is already booked for those dates.\n"
                "Please choose different dates or another car.")

    days = (end_date - start_date).days
    amount = days * v.rent_perday

    Booking.objects.create(
        user=user, vehicle=v,
        booking_from=start_date, booking_to=end_date,
        is_confirmed=True, payment_status="Pending",
        payment_mode="offline", booking_amount=amount
    )
    return (f"📋 Booking Received!\n"
            f"Car: {v.company} {v.model_name}\n"
            f"Dates: {_fmt_date(start_date)} to {_fmt_date(end_date)} ({days} days)\n"
            f"Total: ₹{amount:,}\n"
            "Our team will contact you to confirm the booking.")


# ─────────────────────────────────────────
# GENERAL Q&A (data-backed only)
# ─────────────────────────────────────────

def general_qa(user, msg, original):

    # ── Who are we ──
    if re.search(r"\b(who are you|what are you|your name|about you)\b", msg):
        return "I'm the Royal Cars AI Assistant 🚗. I help with car rentals, bookings, pricing, features, and city availability."

    # ── Help ──
    if re.search(r"\b(help|what can you do|options)\b", msg):
        return ("I can help you with:\n"
                "🚗 List available cars\n"
                "🔍 Car features & details\n"
                "📍 Car availability in your city\n"
                "💰 Pricing & cost calculation\n"
                "📅 Book a car\n"
                "📋 Booking status\n"
                "❌ Cancel a booking\n\n"
                "Try: 'show all cars', 'features of Tata Harrier', 'book Maruti Swift'")

    # ── Family / best car ──
    if re.search(r"\b(family|families|spacious|7.seater|seven.seater)\b", msg):
        vehicles = Vehicle.objects.all().order_by("-rent_perday")
        if vehicles.exists():
            top = vehicles.first()
            return (f"For families, we recommend our premium options.\n"
                    f"Our highest-spec car is {top.company} {top.model_name} ({top.model_year}) at ₹{top.rent_perday}/day in {top.city}.\n"
                    "Type 'show all cars' to compare all options.")
        return "Type 'show all cars' to see all available vehicles."

    # ── City driving / best for city ──
    if re.search(r"\b(city.driving|city drive|urban|hatchback)\b", msg):
        vehicles = Vehicle.objects.all().order_by("rent_perday")
        if vehicles.exists():
            budget = vehicles.first()
            return (f"For city driving, budget-friendly cars work best.\n"
                    f"Our most affordable option: {budget.company} {budget.model_name} at ₹{budget.rent_perday}/day.\n"
                    "Type 'show all cars' for more options.")
        return "Type 'show all cars' to see all available vehicles."

    # ── Latest models ──
    if re.search(r"\b(latest|newest|new model|recent)\b", msg):
        vehicles = Vehicle.objects.all().order_by("-model_year")
        if vehicles.exists():
            v = vehicles.first()
            return (f"Our latest model is the {v.company} {v.model_name} ({v.model_year}) at ₹{v.rent_perday}/day in {v.city}.\n"
                    "Type 'show all cars' to see all models with years.")
        return "Type 'show all cars' to see all vehicles."

    # ── Stock / in stock ──
    if re.search(r"\b(in stock|currently|stock|inventory)\b", msg):
        count = Vehicle.objects.count()
        return f"We currently have {count} car(s) available for rental.\nType 'show all cars' to see the full list."

    # ── Compare ──
    if re.search(r"\bcompar\b", msg):
        vehicles = list(Vehicle.objects.all()[:2])
        if len(vehicles) >= 2:
            a, b = vehicles[0], vehicles[1]
            return (f"Comparison:\n"
                    f"🚗 {a.company} {a.model_name} ({a.model_year}) — ₹{a.rent_perday}/day in {a.city}\n"
                    f"🚗 {b.company} {b.model_name} ({b.model_year}) — ₹{b.rent_perday}/day in {b.city}\n"
                    "To compare specific cars, ask: 'compare Toyota Innova and Maruti Swift'")
        return "Type 'show all cars' to see all available vehicles."

    # ── Budget / best under price ──
    if re.search(r"\b(budget|under|affordable|cheapest|lowest)\b", msg):
        m = re.search(r"(\d+)", msg)
        budget_amt = int(m.group(1)) if m else None
        if budget_amt:
            vehicles = Vehicle.objects.filter(rent_perday__lte=budget_amt).order_by("rent_perday")
            if vehicles.exists():
                resp = f"Cars available under ₹{budget_amt}/day:\n"
                for v in vehicles:
                    resp += f"- {v.company} {v.model_name}: ₹{v.rent_perday}/day\n"
                return resp
            return f"No cars available under ₹{budget_amt}/day. Type 'show all cars' for full pricing."
        vehicles = Vehicle.objects.all().order_by("rent_perday")
        if vehicles.exists():
            v = vehicles.first()
            return f"Our most affordable car is {v.company} {v.model_name} at ₹{v.rent_perday}/day."

    # ── Payment ──
    if re.search(r"\b(payment|pay|upi|card|cash|online payment|offline)\b", msg):
        return "We accept both online (UPI/Card) and offline (cash) payments. Payment is completed on the bookings page after booking."

    # ── Booking fee ──
    if re.search(r"\bbooking\s*fee\b", msg):
        return "There is no separate booking fee. You only pay the rental amount for your selected days."

    # ── Delivery ──
    if re.search(r"\bdelivery\b", msg):
        return "Car delivery timelines depend on availability. Please contact us directly after booking for delivery details."

    # ── Contact / showroom ──
    if re.search(r"\b(contact|phone|email|showroom|location|where|hours)\b", msg):
        return "Please use the Contact page on our website to reach us. Our team is happy to assist!"

    # ── Discount / offer / festive ──
    if re.search(r"\b(discount|offer|festive|deal|coupon|promo)\b", msg):
        return "We don't currently have active discount information in our system. Please contact us directly for any ongoing offers."

    # ── EMI / loan / finance ──
    if re.search(r"\b(emi|loan|finance|down payment|bank|financing)\b", msg):
        return "We're a car rental service — EMI/loan options are not applicable here. You simply pay the daily rent for your booking."

    # ── Exchange / trade-in ──
    if re.search(r"\b(exchange|trade.in|old car|value)\b", msg):
        return "We are a rental service and do not offer car exchange or trade-in services."

    # ── Warranty / service / service center ──
    if re.search(r"\b(warranty|service|servicing|service center|maintenance)\b", msg):
        return "All our rental cars are well-maintained. For service-related queries, please contact us directly."

    # ── Colors / colour ──
    if re.search(r"\b(color|colour|white|black|red|blue|silver|grey)\b", msg):
        return "We don't have color information for our cars in the system. Please contact us to check specific color availability."

    # ── Mileage / fuel / engine / specs not in DB ──
    if re.search(r"\b(mileage|kmpl|fuel|petrol|diesel|cng|electric|engine|cc|transmission|automatic|boot|space|airbag|sunroof|android auto|apple carplay|safety)\b", msg):
        v = _find_vehicle(msg)
        if v:
            return (f"Detailed spec information for {v.company} {v.model_name} is not available in our system.\n"
                    f"What I can tell you: {v.model_year} model, ₹{v.rent_perday}/day in {v.city}.\n"
                    "For full specs, please contact us.")
        return "Detailed specifications are not available in our system. Please contact us for more information."

    # ── How to book ──
    if re.search(r"\b(how.*(book|rent)|booking process)\b", msg):
        return ("To book a car:\n"
                "1\u20e3 Type: 'book [car name]'\n"
                "2\u20e3 Provide dates: DD-MM-YYYY to DD-MM-YYYY\n"
                "3\u20e3 Our team will confirm your booking\n\n"
                "Example: 'book Toyota Innova'\nOr: 'book Maruti Swift from 15-07-2026 to 18-07-2026'")

    # ── Electric cars ──
    if re.search(r"\b(electric|ev)\b", msg):
        return "We don't currently have electric vehicles in our fleet. Type 'show all cars' to see available options."

    # ── Unrecognised — friendly fallback ──
    return ("I'm here to help with car rentals! 😊\n"
            "You can ask me:\n"
            "• 'Show all cars'\n"
            "• 'Features of Tata Harrier'\n"
            "• 'Is Toyota Innova available in Bengaluru?'\n"
            "• 'Book Maruti Swift from 15-07-2026 to 18-07-2026'\n"
            "• 'What is the price of Kia Seltos for 3 days?'")