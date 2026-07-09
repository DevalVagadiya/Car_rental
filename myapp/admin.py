from django.contrib import admin
from .models import login_table, State, City, Area, Vehicle, Booking, Complaint, Feedback, Contactus, ChatMessage

@admin.register(login_table)
class LoginTableAdmin(admin.ModelAdmin):
    list_display = ['name', 'email_id', 'phone_no', 'usertype','photos', 'is_verified']
    list_filter = ['usertype', 'is_verified']
    search_fields = ['name', 'email_id']

@admin.register(State)
class StateAdmin(admin.ModelAdmin):
    list_display = ['name']

@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ['name', 'state']

@admin.register(Area)
class AreaAdmin(admin.ModelAdmin):
    list_display = ['name', 'city']

@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ['model_name', 'company', 'model_year', 'rent_perday', 'location', 'vendor','photos','rc_book']
    list_filter = ['location', 'vendor']
    search_fields = ['model_name', 'company']

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['user', 'vehicle', 'booking_date', 'is_confirmed', 'booking_from', 'booking_to','booking_amount','payment_mode','payment_status','cancellation_status']

@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ['user', 'vehicle', 'description', 'date']

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ['user', 'vehicle', 'rating', 'comment', 'date']

@admin.register(Contactus)
class ContactusAdmin(admin.ModelAdmin):
    list_display = ['name', 'email','subject','message']

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['user', 'short_message', 'short_response', 'created_at']
    list_filter = ['user', 'created_at']
    search_fields = ['user__name', 'message', 'response']
    readonly_fields = ['user', 'message', 'response', 'created_at']
    ordering = ['-created_at']

    def short_message(self, obj):
        return obj.message[:60] + '...' if len(obj.message) > 60 else obj.message
    short_message.short_description = 'User Message'

    def short_response(self, obj):
        return obj.response[:60] + '...' if len(obj.response) > 60 else obj.response
    short_response.short_description = 'Bot Response'