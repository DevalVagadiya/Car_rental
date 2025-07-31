from django.urls import path, include
from . import views

urlpatterns = [
   path("", views.index, name="index"),
   path("login", views.login, name="login"),
   path("about", views.about, name="about"),
   path("contact", views.contact, name="contact"),
   path("searchcar", views.searchcar, name="searchcar"),
   path("submitcontact", views.submitcontact, name="submitcontact"),
   path("signup", views.signup, name="signup"),
   path("viewdata", views.viewdata, name="viewdata"),

   path('checkuser', views.checklogin, name='checkuser'),
   path('logout', views.logout, name='logout'),
   path('profile', views.profile, name='profile'),
   path('postacar', views.postacar, name='postacar'),
   path('addacar', views.addacar, name='addacar'),
   path('mycars', views.mycars, name='mycars'),
   path('listings', views.allcars, name='listings'),
   path('updatecar', views.updatecardetails, name='updatecar'),
   path('bookcar', views.bookcar, name='bookcar'),
   path('ownerbookings', views.ownerbookings, name='ownerbookings'),
   path('userbookings', views.userbookings, name='userbookings'),
   path('givefeedback', views.givefeedback, name='givefeedback'),
   path('submitfeedback', views.submitfeedback, name='submitfeedback'),
   path('complain', views.complain, name='complain'),
   path('submitcomplain', views.submitcomplain, name='submitcomplain'),
   
   path("viewcar/<int:cid>", views.viewcar, name="viewcar"),
   path("removecar/<int:rcid>", views.removecar, name="removecar"),
   path("cancelbooking/<int:booking_id>", views.cancelbooking, name="cancelbooking"),
   path("edituserprofile", views.edituserprofile, name="edituserprofile"),
   path("updateprofile", views.updateprofile, name="updateprofile"),
   path("forgotpasswordpage", views.forgotpasswordpage, name="forgotpasswordpage"),
   path("forgotpassword", views.forgotpassword, name="forgotpassword"),
   path("changepwdpage", views.changepwdpage, name="changepwdpage"),
   path("changepwd", views.changepwd, name="changepwd"),
]