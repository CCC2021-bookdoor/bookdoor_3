from random import choices
from django.views import View
from django.shortcuts import render, redirect
from accounts.models import CustomUser, Profile
from accounts.forms import ProfileForm, SignupUserForm,ProfileCreateForm
from allauth.account import views
from django.contrib.auth.mixins import LoginRequiredMixin
import datetime

class ProfileView(LoginRequiredMixin,View):
  def get(self, request, *args, **kwargs):
    if Profile.objects.filter(owner=request.user).count()==0:
      return redirect(to='/accounts/profile_create')
    user_data=CustomUser.objects.get(id=request.user.id)
    today=datetime.date.today()
    birthday=user_data.birthday
    age=(int(today.strftime("%Y%m%d")) - int(birthday.strftime("%Y%m%d"))) // 10000
    user_profile=Profile.objects.filter(owner=request.user).values('nickname','email')
    return render(request, 'accounts/profile.html',{
      'user_data':user_data,
      'user_profile':user_profile[0],
      'age':age,
    })


class ProfileEditView(View):
  def get(self, request, *args, **kwargs):
    obj=Profile.objects.get(owner=request.user.id)
    return render(request, 'accounts/profile_edit.html', {
      'form': ProfileForm(instance=obj),
    })

  def post(self, request, *args, **kwargs):
    obj=Profile.objects.get(owner=request.user.id)
    profile=ProfileForm(request.POST, instance=obj)
    profile.save()
    return redirect(to='/accounts/profile')


class LoginView(views.LoginView):
  template_name='accounts/login.html'


class LogoutView(views.LogoutView):
  template_name='accounts/logout.html'

  def post(self,*args, **kwargs):
    if self.request.user.is_authenticated:
      self.logout()
    return redirect('/')


class SignupView(views.SignupView):
  template_name='accounts/signup.html'
  form_class=SignupUserForm

class ProfileCreateView(LoginRequiredMixin,View):
  def get(self, request, *args, **kwargs):

    return render(request, 'accounts/profile_create.html', {
      'form': ProfileCreateForm,
    })

  def post(self, request, *args, **kwargs):
    profile=Profile()
    profile.owner=request.user
    profile.nickname=request.POST['nickname']
    profile.choices=request.POST['choices']
    profile.save()
    return redirect(to='/accounts/profile')