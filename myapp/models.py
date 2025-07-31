from django.db import models
from django.utils.safestring import mark_safe

class login_table(models.Model):
    name = models.CharField(max_length=100)
    email_id=models.EmailField()
    phone_no=models.IntegerField()
    password = models.CharField(max_length=300, default="admin")
    photo = models.ImageField(upload_to="photos")
    dob = models.DateField()
    address = models.TextField()

    def photos(self):
        return mark_safe('<img src ="{}" width ="100"/>'.format(self.photo.url))

    photos.allow_tags = True

    ROLE = (
        ("Lessor", "Lessor"),
        ("Lessee", "Lessee")
    )
    usertype = models.CharField(max_length=100,choices=ROLE)
    is_verified = models.BooleanField(default=False)
    comments = models.CharField(max_length=100,default="")

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.is_verified is None:
            # Set is_verified based on usertype
            if self.usertype == "Lessee":
                self.is_verified = True
            elif self.usertype == "Lessor":
                self.is_verified = False

        super().save(*args, **kwargs)

class State(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class City(models.Model):
    name = models.CharField(max_length=255)
    state = models.ForeignKey(State, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

class Area(models.Model):
    name = models.CharField(max_length=255)
    city = models.ForeignKey(City, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

class Vehicle(models.Model):
    vendor = models.ForeignKey(login_table, on_delete=models.CASCADE)
    company = models.CharField(max_length=255)
    model_name = models.CharField(max_length=255)
    model_year = models.CharField(max_length=255)
    rent_perday = models.IntegerField()
    location = models.CharField(max_length=255)
    area = models.ForeignKey(Area, on_delete=models.CASCADE)
    city = models.ForeignKey(City, on_delete=models.CASCADE)
    state = models.ForeignKey(State, on_delete=models.CASCADE)
    model_photo = models.ImageField(upload_to="photos")
    rc_book = models.FileField(upload_to="pdfs",default="")

    def photos(self):
        return mark_safe('<img src ="{}" width ="100"/>'.format(self.model_photo.url))

    photos.allow_tags = True

    def __str__(self):
        return self.model_name


class Booking(models.Model):
    user = models.ForeignKey(login_table, on_delete=models.CASCADE)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
    booking_date = models.DateTimeField(auto_now_add=True)
    is_confirmed = models.BooleanField(default=False)
    booking_from = models.DateTimeField()
    booking_to = models.DateTimeField()
    booking_amount = models.IntegerField(default=0)
    pmlist = (
        ("online", "online"),
        ("offline", "offline")
    )
    payment_mode = models.CharField(max_length=255, choices=pmlist, default="")
    pslist = (
        ("Pending", "Pending"),
        ("Done", "Done"),
        ("Offline", "Offline"),
    )
    payment_status = models.CharField(max_length=255, choices=pslist, default="")
    cancellation_status = models.CharField(max_length=255, default="No")



class Complaint(models.Model):
    user = models.ForeignKey(login_table, on_delete=models.CASCADE)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
    description = models.TextField()
    date = models.DateTimeField(auto_now_add=True)

class Feedback(models.Model):
    user = models.ForeignKey(login_table, on_delete=models.CASCADE)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
    rating = models.IntegerField()
    comment = models.TextField()
    date = models.DateTimeField(auto_now_add=True)
    # take this feedback after booking end date only.

class Contactus(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField()
    subject = models.CharField(max_length=255)
    message = models.CharField(max_length=500)



