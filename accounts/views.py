from random import choices
from django.views import View
from django.shortcuts import render, redirect
from accounts.models import CustomUser, Profile
from bookdoor.models import BookComment
from accounts.forms import ProfileForm, SignupUserForm,ProfileCreateForm
from allauth.account import views
from django.contrib.auth.mixins import LoginRequiredMixin
import datetime

class ProfileView(LoginRequiredMixin,View):

  def __init__(self,):
    self.params={
      'books':'',
      'user_data':'',
      'form': '',
      'age':'',
    }

  def get(self, request, *args, **kwargs):
    if Profile.objects.filter(owner=request.user).count()==0:
      return redirect(to='/accounts/profile_create')

    user_data=CustomUser.objects.get(id=request.user.id)
    today=datetime.date.today()
    birthday=user_data.birthday
    age=(int(today.strftime("%Y%m%d")) - int(birthday.strftime("%Y%m%d"))) // 10000
    obj=Profile.objects.get(owner=request.user.id)

    books=BookComment.objects.filter(writer=request.user)

    self.params['books']=books
    self.params['user_data']=user_data
    self.params['form']=ProfileForm(instance=obj)
    self.params['age']=age
    return render(request, 'accounts/profile.html',self.params)

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