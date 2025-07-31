from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.http import HttpResponseRedirect
import datetime
from django.utils import timezone
from datetime import timedelta

from django.db.models import Sum
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import login_table,Vehicle, Area,City,State,Booking,Complaint,Feedback



from django.contrib import messages

def index(request):
    try:
        uid = request.session['log_id']
        userdata = login_table.objects.get(id=uid)
        Owner = False
        if userdata.usertype == "Lessor":
            Owner = True
            print(userdata.usertype)

        statedetail = State.objects.all()
        citydetail = City.objects.all()
        areadetail = Area.objects.all()

        allcardata = Vehicle.objects.all()


        context = {
            'userdata': userdata,
            'Owner': Owner,
            'statedetail': statedetail,
            'citydetail': citydetail,
            'areadetail': areadetail,
            'allcardata': allcardata,
        }

        return render(request, 'index.html', context)

    except:
        pass
    statedetail = State.objects.all()
    citydetail = City.objects.all()
    areadetail = Area.objects.all()

    allcardata = Vehicle.objects.all()

    context = {
        'statedetail': statedetail,
        'citydetail': citydetail,
        'areadetail': areadetail,
        'allcardata': allcardata,
    }

    return render(request,'index.html', context)

def login(request):
    try:
        uid = request.session['log_id']
        userdata = login_table.objects.get(id=uid)
        Owner = False
        if userdata.usertype == "Lessor":
            Owner = True
            print(userdata.usertype)

        statedetail = State.objects.all()
        citydetail = City.objects.all()
        areadetail = Area.objects.all()


        context = {
            'userdata': userdata,
            'Owner': Owner,
            'statedetail': statedetail,
            'citydetail': citydetail,
            'areadetail': areadetail,
        }

        return render(request, 'login.html', context)

    except:
        pass
    return render(request,'login.html')

def signup(request):
    try:
        uid = request.session['log_id']
        userdata = login_table.objects.get(id=uid)
        Owner = False
        if userdata.usertype == "Lessor":
            Owner = True
            print(userdata.usertype)

        statedetail = State.objects.all()
        citydetail = City.objects.all()
        areadetail = Area.objects.all()


        context = {
            'userdata': userdata,
            'Owner': Owner,
            'statedetail': statedetail,
            'citydetail': citydetail,
            'areadetail': areadetail,
        }

        return render(request, 'signup.html', context)

    except:
        pass
    return render(request,'signup.html')

def viewdata(request):
    if request.method == 'POST':
        name = request.POST.get("name")
        email = request.POST.get("email")
        phone = request.POST.get("phone")
        password = request.POST.get("password")
        dob = request.POST.get("dob")
        role = request.POST.get("usertype")
        address = request.POST.get("address")
        file = request.FILES['pp']

        try:
            alllogins = login_table.objects.get(email_id=email)
        except login_table.DoesNotExist:
            alllogins = None

        if alllogins is None:
            logindata = login_table(name=name,email_id=email, phone_no=phone, password=password, photo=file, dob=dob, address=address, usertype=role, comments="Account Created")
            logindata.save()
            messages.success(request, 'Account Created Successfully. you can login now')
        else:
            messages.error(request, 'Account already exist with same email')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    else:
        messages.error(request, 'error occured')

    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

def checklogin(request):
    if request.method == 'POST':
        username = request.POST['email']
        password = request.POST['password']
        try:
            user = login_table.objects.get(email_id=username, password=password)
            request.session['log_user'] = user.email_id
            request.session['log_id'] = user.id
            request.session.save()

        except login_table.DoesNotExist:
            user = None

        if user is not None:
            print("successfully logged in")
            messages.success(request, 'Successfully Logged In')
            return redirect(index)

        else:
            print("not logged in")
            messages.error(request, 'Invalid USER ID')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

def logout(request):
    try:
        del request.session['log_user']
        del request.session['log_id']
        messages.success(request, 'Logged Out')
    except:
        pass

    return redirect(index)

def profile(request):
    try:
        uid = request.session['log_id']
        userdata = login_table.objects.get(id=uid)
        Owner = False
        if userdata.usertype == "Lessor":
            Owner = True
            print(userdata.usertype)

        statedetail = State.objects.all()
        citydetail = City.objects.all()
        areadetail = Area.objects.all()


        try:
            profiledata = login_table.objects.get(id=uid)
        except login_table.DoesNotExist:
            profiledata = None

        context = {
            'userdata': userdata,
            'Owner': Owner,
            'profiledata': profiledata,
            'statedetail': statedetail,
            'citydetail': citydetail,
            'areadetail': areadetail,
        }

        return render(request, 'profile.html', context)

    except:
        pass
    return render(request,'profile.html')


def forgotpasswordpage(request):
    try:
        uid = request.session['log_id']
        userdata = login_table.objects.get(id=uid)

        Owner = False
        if userdata.usertype == "Lessor":
            Owner = True
            print(userdata.usertype)

        context = {
            'userdata': userdata,
            'Owner': Owner,
        }

        return render(request, 'index.html', context)

    except:
        pass
    return render(request,'forgotpasswordpage.html')



def forgotpassword(request):
    if request.method == 'POST':
        username = request.POST.get('email')

        try:
            user = login_table.objects.get(email_id=username)

        except login_table.DoesNotExist:
            user = None

        if user is not None:
            #################### Password Generation ##########################
            import random
            letters = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's',
                       't', 'u', 'v', 'w', 'x', 'y', 'z', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L',
                       'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']
            numbers = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
            symbols = ['!', '#', '$', '%', '&', '(', ')', '*', '+']

            nr_letters = 6
            nr_symbols = 1
            nr_numbers = 3
            password_list = []

            for char in range(1, nr_letters + 1):
                password_list.append(random.choice(letters))

            for char in range(1, nr_symbols + 1):
                password_list += random.choice(symbols)

            for char in range(1, nr_numbers + 1):
                password_list += random.choice(numbers)

            print(password_list)
            random.shuffle(password_list)
            print(password_list)

            password = ""  #we will get final password in this var.
            for char in password_list:
                password += char

            ##############################################################


            msg = "Hello here it is your new password  "+password   #this variable will be passed as message in mail

            ############ code for sending mail ########################

            from django.core.mail import send_mail

            send_mail(
                'Your New Password',
                msg,
                'pateldeva0165@gmail.com',
                [username],
                fail_silently=False,
            )

            #now update the password in model
            cuser = login_table.objects.get(email_id=username)
            cuser.password = password
            cuser.save(update_fields=['password'])

            print('Mail sent')
            messages.info(request, 'mail is sent successfully to your registered email')
            return redirect(index)
        else:
            messages.info(request, 'This account does not exist')
    return redirect(index)


def changepwdpage(request):
    try:
        uid = request.session['log_id']
        userdata = login_table.objects.get(id=uid)

        Owner = False
        if userdata.usertype == "Lessor":
            Owner = True
            print(userdata.usertype)

        context = {
            'userdata': userdata,
            'Owner': Owner,
        }

        return render(request, "changepwdpage.html", context)
    except:
        return render(request, "changepwdpage.html")

def changepwd(request):
    uid = request.session['log_id']
    userdata = login_table.objects.get(id=uid)
    try:
        pwd = userdata.password
        if request.method == "POST":
            oldpwd = request.POST.get("old")
            newpwd = request.POST.get("password1")
            confirmpwd = request.POST.get("password2")

            if oldpwd == pwd:
                if newpwd == confirmpwd:
                    userdata.password = newpwd
                    userdata.save()
                    messages.success(request, 'Password Updated Successfully.')
                    del request.session['log_id']
                    return redirect(login)
                else:
                    messages.error(request, "New Password and confirm not same")
                    return redirect(changepwdpage)
            else:
                messages.error(request, "Invalid Old Password")
                return redirect(changepwdpage)

    except userdata.DoesNotExist:
        messages.error(request, 'This account does not exist.')
        return redirect(index)

    return render(request, "index.html") # , context



def postacar(request):
    try:
        uid = request.session['log_id']
        userdata = login_table.objects.get(id=uid)
        Owner = False
        if userdata.usertype == "Lessor":
            Owner = True
            print(userdata.usertype)

        statedetail = State.objects.all()
        citydetail = City.objects.all()
        areadetail = Area.objects.all()


        context = {
            'userdata': userdata,
            'Owner': Owner,
            'statedetail': statedetail,
            'citydetail': citydetail,
            'areadetail': areadetail,
        }

        return render(request, 'postacar.html', context)

    except:
        pass
    return render(request,'postacar.html')

def addacar(request):
    uid = request.session['log_id']
    if request.method == 'POST':
        cname = request.POST.get("cname")
        model = request.POST.get("model")
        modelyear = request.POST.get("modelyear")
        rent = request.POST.get("rent")
        address = request.POST.get("address")
        areaname = request.POST.get("area")
        cityname = request.POST.get("city")
        statename = request.POST.get("state")
        file = request.FILES['vp']
        rc = request.FILES['rc']


        addvehicle = Vehicle(vendor=login_table(id=uid),company=cname, model_name=model ,model_year=modelyear, rent_perday=rent, location=address, model_photo=file,
                                        rc_book=rc,city=City(id=cityname), state=State(id=statename), area=Area(id=areaname))
        addvehicle.save()
        messages.success(request, 'Vehicle Added Successfully.')
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    else:
        messages.error(request, 'error occured')
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

def mycars(request):
    try:
        uid = request.session['log_id']
        userdata = login_table.objects.get(id=uid)
        Owner = False
        if userdata.usertype == "Lessor":
            Owner = True
            print(userdata.usertype)

        statedetail = State.objects.all()
        citydetail = City.objects.all()
        areadetail = Area.objects.all()

        mycardata = Vehicle.objects.filter(vendor=login_table(id=uid))


        context = {
            'userdata': userdata,
            'Owner': Owner,
            'statedetail': statedetail,
            'citydetail': citydetail,
            'areadetail': areadetail,
            'mycardata': mycardata,
        }

        return render(request, 'mycars.html', context)

    except:
        pass
    return render(request,'mycars.html')

def allcars(request):
    try:
        uid = request.session['log_id']
        userdata = login_table.objects.get(id=uid)
        Owner = False
        if userdata.usertype == "Lessor":
            Owner = True
            print(userdata.usertype)

        statedetail = State.objects.all()
        citydetail = City.objects.all()
        areadetail = Area.objects.all()

        allcardata = Vehicle.objects.all()

        page = request.GET.get('page', 1)
        paginator = Paginator(allcardata, 3)  # Set the number of items per page
        try:
            allcardata = paginator.page(page)
        except PageNotAnInteger:
            allcardata = paginator.page(1)
        except EmptyPage:
            allcardata = paginator.page(paginator.num_pages)

        context = {
            'userdata': userdata,
            'Owner': Owner,
            'statedetail': statedetail,
            'citydetail': citydetail,
            'areadetail': areadetail,
            'allcardata': allcardata,
            'paginator': paginator,
            'page': int(page),

        }

        return render(request, 'allcars.html', context)

    except:
        pass
    statedetail = State.objects.all()
    citydetail = City.objects.all()
    areadetail = Area.objects.all()

    allcardata = Vehicle.objects.all()

    page = request.GET.get('page', 1)
    paginator = Paginator(allcardata, 3)  # Set the number of items per page
    try:
        allcardata = paginator.page(page)
    except PageNotAnInteger:
        allcardata = paginator.page(1)
    except EmptyPage:
        allcardata = paginator.page(paginator.num_pages)

    context = {
        'statedetail': statedetail,
        'citydetail': citydetail,
        'areadetail': areadetail,
        'allcardata': allcardata,
        'paginator': paginator,
        'page': int(page),
    }
    return render(request,'allcars.html', context)

def viewcar(request, cid):
    try:
        uid = request.session['log_id']
        userdata = login_table.objects.get(id=uid)
        Owner = False
        if userdata.usertype == "Lessor":
            Owner = True
            print(userdata.usertype)

        statedetail = State.objects.all()
        citydetail = City.objects.all()
        areadetail = Area.objects.all()

        try:
            cardata = Vehicle.objects.get(id=cid)
            carownerid = cardata.vendor.id

            Mycar = False
            if carownerid == uid:
                Mycar = True

            context = {
                'userdata': userdata,
                'Owner': Owner,
                'statedetail': statedetail,
                'citydetail': citydetail,
                'areadetail': areadetail,
                'cardata': cardata,
                'Mycar': Mycar,
            }

            return render(request, 'viewcar.html', context)
        except:
            pass
    except:
        pass
    statedetail = State.objects.all()
    citydetail = City.objects.all()
    areadetail = Area.objects.all()

    try:
        cardata = Vehicle.objects.get(id=cid)

        context = {
            'statedetail': statedetail,
            'citydetail': citydetail,
            'areadetail': areadetail,
            'cardata': cardata,
        }
        return render(request, 'viewcar.html', context)

    except:
        pass

    return redirect('/mycars')

def updatecardetails(request):
    try:
        uid = request.session['log_id']

        carid = request.POST.get("carid")
        cname = request.POST.get("cname")
        model = request.POST.get("model")
        modelyear = request.POST.get("modelyear")
        rent = request.POST.get("rent")
        address = request.POST.get("address")
        areaname = request.POST.get("area")
        cityname = request.POST.get("city")
        statename = request.POST.get("state")
        fetcharea = Area.objects.get(name=areaname)
        fetchcity = City.objects.get(name=cityname)
        fetchstate = State.objects.get(name=statename)

        vehdata = Vehicle.objects.get(id=carid)

        vehdata.company = cname
        vehdata.model_name = model
        vehdata.model_year = modelyear
        vehdata.rent_perday = rent
        vehdata.location = address
        vehdata.area = fetcharea
        vehdata.city = fetchcity
        vehdata.state = fetchstate

        if 'vp' in request.FILES:
            file = request.FILES["vp"]
            vehdata.model_photo = file

        if 'rc' in request.FILES:
            rcfile = request.FILES["rc"]
            vehdata.rc_book = rcfile

        vehdata.save()

        messages.success(request, 'Your Car details has been updated successfully.')
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))  # Redirect to the user's profile page after update

    except vehdata.DoesNotExist:
        vehdata = None
    messages.error(request, 'Failed to update')
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

def removecar(request, rcid):
    myveh = Vehicle.objects.get(id=rcid)

    try:
        bookingdata = Booking.objects.filter(vehicle=myveh)
    except Booking.DoesNotExist:
        bookingdata = None

    if bookingdata.exists():
        messages.error(request, 'You Can not remove this vehicle as there are confirmed booking for this.')
    else:
        Vehicle.objects.get(id=rcid).delete()
        messages.error(request, 'Car Removed')

    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


def bookcar(request):
    uid = request.session.get('log_id')

    if request.method == 'POST':
        booking_from = request.POST.get("bookingfrom")
        paymentmode = request.POST.get("payment")
        booking_to = request.POST.get("bookingto")
        totalAmount = request.POST.get("totalAmount")
        vehicle_id = request.POST.get("carid")  # Adjust accordingly
        print(totalAmount)
        try:
            vehicle = Vehicle.objects.get(id=vehicle_id)
        except Vehicle.DoesNotExist:
            messages.error(request, 'Invalid vehicle ID.')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


        # Check for overlapping bookings
        overlapping_bookings = Booking.objects.filter(
            vehicle=vehicle,
            booking_from__lt=booking_to,
            booking_to__gt=booking_from
        )

        if overlapping_bookings.exists():
            messages.error(request, 'This vehicle has already been booked during the selected duration.')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

        if paymentmode == "online":

            # Your existing logic to handle successful booking
            booking = Booking.objects.create(
                user=login_table(id=uid),
                vehicle=vehicle,
                booking_from=booking_from,
                booking_to=booking_to,
                is_confirmed=True,
                payment_mode=paymentmode,
                booking_amount=totalAmount,
                payment_status="Done"
            )
        else:
            booking = Booking.objects.create(
                user=login_table(id=uid),
                vehicle=vehicle,
                booking_from=booking_from,
                booking_to=booking_to,
                is_confirmed=True,
                payment_mode=paymentmode,
                booking_amount=totalAmount,
                payment_status="Offline"
            )

        messages.success(request, 'Vehicle Booked Successfully.')
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    else:
        messages.error(request, 'Invalid request method.')
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

def ownerbookings(request):
    try:
        uid = request.session['log_id']
        userdata = login_table.objects.get(id=uid)
        Owner = False
        if userdata.usertype == "Lessor":
            Owner = True
            print(userdata.usertype)

        statedetail = State.objects.all()
        citydetail = City.objects.all()
        areadetail = Area.objects.all()

        mycardata = Vehicle.objects.filter(vendor=login_table(id=uid))
        print(mycardata)

        try:
            bookingdata = Booking.objects.filter(vehicle__in=mycardata)
        except Booking.DoesNotExist:
            bookingdata = None
        print(bookingdata)

        context = {
            'userdata': userdata,
            'Owner': Owner,
            'statedetail': statedetail,
            'citydetail': citydetail,
            'areadetail': areadetail,
            'bookingdata': bookingdata,
        }

        return render(request, 'ownerbookings.html', context)

    except:
        pass
    return render(request,'ownerbookings.html')


def userbookings(request):
    try:
        uid = request.session['log_id']
        userdata = login_table.objects.get(id=uid)
        Owner = False
        if userdata.usertype == "Lessor":
            Owner = True
            print(userdata.usertype)

        statedetail = State.objects.all()
        citydetail = City.objects.all()
        areadetail = Area.objects.all()

        try:
            bookingdata = Booking.objects.filter(user=login_table(id=uid))
        except Booking.DoesNotExist:
            bookingdata = None
        print(bookingdata)

        context = {
            'userdata': userdata,
            'Owner': Owner,
            'statedetail': statedetail,
            'citydetail': citydetail,
            'areadetail': areadetail,
            'bookingdata': bookingdata,
        }

        return render(request, 'userbookings.html', context)

    except:
        pass
    return render(request,'userbookings.html')


def cancelbooking(request, booking_id):
    try:
        booking = Booking.objects.get(id=booking_id)

        # Calculate the difference between current time and booking_from
        time_difference = booking.booking_from - timezone.now()

        # Check if the difference is at least 24 hours (86400 seconds)
        if time_difference.total_seconds() >= 86400:
            # Allow cancellation

            # Add your cancellation logic here
            # For example, you can update the booking status to canceled:
            booking.cancellation_status = "Cancelled"  # Assuming the booking is canceled offline
            booking.save()
            messages.success(request, 'Booking Cancelled.')
            # Redirect to a success page or display a success message
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        else:
            # Disallow cancellation
            messages.error(request, 'Booking can be cancelled only before 24 hours of the booking date.')
            # Redirect to a page indicating that the booking cannot be canceled
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    except Booking.DoesNotExist:
        messages.error(request, 'Error Occured fetching object.')
        # Handle the case when the booking with the given ID does not exist
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


def givefeedback(request):
    try:
        uid = request.session['log_id']
        userdata = login_table.objects.get(id=uid)
        Owner = False
        if userdata.usertype == "Lessor":
            Owner = True
            print(userdata.usertype)

        statedetail = State.objects.all()
        citydetail = City.objects.all()
        areadetail = Area.objects.all()

        current_date = timezone.now()

        completed_bookings = Booking.objects.filter(user=login_table(id=uid), booking_to__lt=current_date)

        context = {
            'userdata': userdata,
            'Owner': Owner,
            'statedetail': statedetail,
            'citydetail': citydetail,
            'areadetail': areadetail,
            'completed_bookings': completed_bookings,
        }

        return render(request, 'givefeedback.html', context)

    except:
        pass
    return render(request,'givefeedback.html')

def submitfeedback(request):
    if request.method == 'POST':
        uid = request.session['log_id']
        booking_id = request.POST.get("booking_id")
        comment = request.POST.get("comment")
        star_rating = request.POST.get("star_rating")

        bookingobj = Booking.objects.get(id=booking_id)
        fetchvehid = bookingobj.vehicle.id



        savefeedback = Feedback(user=login_table(id=uid),vehicle=Vehicle(id=fetchvehid), rating=star_rating ,comment=comment)
        savefeedback.save()
        messages.success(request, 'Feedback Received.')
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    else:
        messages.error(request, 'error occured')
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

def complain(request):
    try:
        uid = request.session['log_id']
        userdata = login_table.objects.get(id=uid)
        Owner = False
        if userdata.usertype == "Lessor":
            Owner = True
            print(userdata.usertype)

        statedetail = State.objects.all()
        citydetail = City.objects.all()
        areadetail = Area.objects.all()

        current_date = timezone.now()

        completed_bookings = Booking.objects.filter(user=login_table(id=uid), booking_to__lt=current_date)

        context = {
            'userdata': userdata,
            'Owner': Owner,
            'statedetail': statedetail,
            'citydetail': citydetail,
            'areadetail': areadetail,
            'completed_bookings': completed_bookings,
        }

        return render(request, 'complain.html', context)

    except:
        pass
    return render(request,'complain.html')

def submitcomplain(request):
    if request.method == 'POST':
        uid = request.session['log_id']
        booking_id = request.POST.get("booking_id")
        comment = request.POST.get("comment")


        bookingobj = Booking.objects.get(id=booking_id)
        fetchvehid = bookingobj.vehicle.id


        savefeedback = Complaint(user=login_table(id=uid),vehicle=Vehicle(id=fetchvehid),description=comment)
        savefeedback.save()
        messages.success(request, 'Your Complaint is Received. We will work on it and get back to you.')
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    else:
        messages.error(request, 'error occured')
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

def about(request):
    try:
        uid = request.session['log_id']
        userdata = login_table.objects.get(id=uid)
        Owner = False
        if userdata.usertype == "Lessor":
            Owner = True
            print(userdata.usertype)

        statedetail = State.objects.all()
        citydetail = City.objects.all()
        areadetail = Area.objects.all()

        context = {
            'userdata': userdata,
            'Owner': Owner,
            'statedetail': statedetail,
            'citydetail': citydetail,
            'areadetail': areadetail,
        }

        return render(request, 'about.html', context)

    except:
        pass
    statedetail = State.objects.all()
    citydetail = City.objects.all()
    areadetail = Area.objects.all()


    context = {
        'statedetail': statedetail,
        'citydetail': citydetail,
        'areadetail': areadetail,
    }
    return render(request,'about.html', context)


def contact(request):
    try:
        uid = request.session['log_id']
        userdata = login_table.objects.get(id=uid)
        Owner = False
        if userdata.usertype == "Lessor":
            Owner = True
            print(userdata.usertype)

        statedetail = State.objects.all()
        citydetail = City.objects.all()
        areadetail = Area.objects.all()

        context = {
            'userdata': userdata,
            'Owner': Owner,
            'statedetail': statedetail,
            'citydetail': citydetail,
            'areadetail': areadetail,
        }

        return render(request, 'contact.html', context)

    except:
        pass
    statedetail = State.objects.all()
    citydetail = City.objects.all()
    areadetail = Area.objects.all()


    context = {
        'statedetail': statedetail,
        'citydetail': citydetail,
        'areadetail': areadetail,
    }
    return render(request,'contact.html', context)

def submitcontact(request):
    if request.method == 'POST':
        name = request.POST.get("name")
        email = request.POST.get("email")
        subject = request.POST.get("subject")
        message = request.POST.get("message")

 
        from .models import Contactus
        savecontact = Contactus(name=name,email=email,subject=subject,message=message)
        savecontact.save()
        messages.success(request, 'Response Recorded')
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    else:
        messages.error(request, 'error occured')
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


def searchcar(request):
    if request.method == 'POST':
        area = request.POST.get("area")
        city = request.POST.get("city")
        state = request.POST.get("state")

    fetchveh = Vehicle.objects.filter(area=Area(id=area),city=City(id=city),state=State(id=state))

    try:
        uid = request.session['log_id']
        userdata = login_table.objects.get(id=uid)
        Owner = False
        if userdata.usertype == "Lessor":
            Owner = True
            print(userdata.usertype)

        statedetail = State.objects.all()
        citydetail = City.objects.all()
        areadetail = Area.objects.all()

        context = {
            'userdata': userdata,
            'Owner': Owner,
            'fetchveh': fetchveh,
            'statedetail': statedetail,
            'citydetail': citydetail,
            'areadetail': areadetail,
        }

        return render(request, 'searchcar.html', context)

    except:
        pass
    fetchveh = Vehicle.objects.filter(area=Area(id=area), city=City(id=city), state=State(id=state))

    statedetail = State.objects.all()
    citydetail = City.objects.all()
    areadetail = Area.objects.all()


    context = {
        'fetchveh': fetchveh,
        'statedetail': statedetail,
        'citydetail': citydetail,
        'areadetail': areadetail,
    }
    return render(request,'searchcar.html', context)




def edituserprofile(request):
    uid = request.session['log_id']
    try:
        userdata = login_table.objects.get(id=uid)

        Owner = False
        if userdata.usertype == "Lessor":
            Owner = True
            print(userdata.usertype)

        context = {
            'userdata': userdata,
            'Owner': Owner,
        }

        return render(request, 'edituserprofilepage.html', context)
    except:
        pass
    return render(request, 'edituserprofilepage.html',)



def updateprofile(request):
    uid = request.session['log_id']
    try:
        userdata = login_table.objects.get(id=uid)

        Owner = False
        if userdata.usertype == "Lessor":
            Owner = True
            print(userdata.usertype)

        context = {
            'userdata': userdata,
            'Owner': Owner,
        }
    except:
        pass

    if request.method == "POST":
        if 'update' in request.POST:
            uname = request.POST.get("name")
            uemail = request.POST.get("email")
            uphone = request.POST.get("phone")
            uaddress = request.POST.get("address")
            udob = request.POST.get("dob")

            userdata.name = uname
            userdata.phone_no = uphone
            userdata.email_id = uemail
            userdata.dob = udob
            userdata.address = uaddress

            if 'profile' in request.FILES:
                pr = request.FILES["profile"]
                userdata.photo = pr
                userdata.save()

                messages.success(request, 'Your profile has been updated successfully.')
                return redirect(index)
            else:
                userdata.photo = userdata.photo
                userdata.save()

                messages.success(request, 'Your profile has been updated successfully.')
                return redirect('/profile')

        elif 'cancel' in request.POST:
            if context.get("store"):
                return redirect('/profile')
            else:
                return redirect('/profile')

    return render(request, "index.html")


