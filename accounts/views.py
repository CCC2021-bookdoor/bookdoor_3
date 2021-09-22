from random import choices
from django.views import View
from django.shortcuts import render, redirect
from accounts.models import CustomUser, Profile
from bookdoor.models import BookComment, Category
from accounts.forms import ProfileForm, SignupUserForm,ProfileCreateForm
from allauth.account import views
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
import datetime

class ProfileView(LoginRequiredMixin,View):

  def __init__(self):
    self.params={
      'books':'',
      'user_data':'',
      'form': '',
      'age':'',
      'category':Category.objects.all(),
      'category_id':'',
      'page_range':'',
    }

  def get(self, request, category_id, page=1, *args, **kwargs):
    if Profile.objects.filter(owner=request.user).count()==0:
      return redirect(to='/accounts/profile_create')

    user_data=CustomUser.objects.get(id=request.user.id)
    today=datetime.date.today()
    birthday=user_data.birthday
    age=(int(today.strftime("%Y%m%d")) - int(birthday.strftime("%Y%m%d"))) // 10000
    obj=Profile.objects.get(owner=request.user.id)

    books=BookComment.objects.filter(writer=request.user)

    book=[]
    if category_id !=0:
      for item in books:
        if item.book.category_id == category_id:
          book.append(item)
    else:
      book=books

    book=Paginator(book,12)
    page_count=book.num_pages
    page_range=[]
    if page != page_count and page !=1 :
      page_range=[page-1,page,page+1]
    elif page == page_count:
      for i in range(3):
        if page-2+i >= 1:
          page_range.append(page-2+i)
    else:
      if page_count >2:
        page_range=[1,2,3]
      else:
        for i in range(page_count):
          page_range.append(i+1)

    self.params['page_range']=page_range
    self.params['category_id']=category_id
    self.params['books']=book.get_page(page)
    self.params['user_data']=user_data
    self.params['form']=ProfileForm(instance=obj)
    self.params['age']=age
    return render(request, 'accounts/profile.html',self.params)

  def post(self, request, category_id, *args, **kwargs):
    obj=Profile.objects.get(owner=request.user.id)
    profile=ProfileForm(request.POST, instance=obj)
    profile.save()
    return redirect(to='/accounts/profile/0/1')


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
    return redirect(to='/accounts/profile/0/1')
