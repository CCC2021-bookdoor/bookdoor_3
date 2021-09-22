from django.urls import path
from accounts import views

app_name='accounts'
urlpatterns = [
    path('profile/<int:category_id>/<int:page>', views.ProfileView.as_view(), name='profile'),
    path('login/', views.LoginView.as_view(), name='account_login'),
    path('logout/', views.LogoutView.as_view(), name='account_logout'),
    path('signup/', views.SignupView.as_view(), name='account_signup'),
    path('profile_create/', views.ProfileCreateView.as_view(), name='profile_create'),
]