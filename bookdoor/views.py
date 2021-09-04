from django.shortcuts import render
from django.shortcuts import redirect
from django.views.generic import TemplateView
from django.contrib.auth import get_user_model
from .models import Book, BookComment, BookCommentGood
from .models import BookCommentReport, FavoriteBook, Category
from .forms import BookSearchForm, BookCreateForm
from django.db.models import Q
import random
import string
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required

class BookDoorView(TemplateView):
  
  def __init__(self,):
    self.params={
      'form':'',
    }

  def get(self,request):
    return render(request,'bookdoor/index.html', self.params)

  def post(self,request):
    return render(request, 'bookdoor/index.html',self.params)


class BookSearchView(TemplateView):
  
  def __init__(self):

    self.params={
      'form':BookSearchForm(),
      'search':'',
      'data':'',
      'count':'',
      'category':Category.objects.all(),
      'category_id':'',
    }

  def get(self,request,category_id):
    if category_id == 0 :
      data=Book.objects.all()
    else:
      data=Book.objects.filter(category_id=category_id)
    self.params['data']=data
    self.params['count']=len(data)
    self.params['category_id']=category_id
    return render(request,'bookdoor/book_search.html', self.params)

  def post(self,request,category_id):
    search=str(request.POST['search'])
    data=Book.objects.filter(Q(title__icontains=search)|Q(author__icontains=search)|Q(illustrator__icontains=search)|Q(translator__icontains=search)|Q(publisher__icontains=search))
    if category_id != 0:
      data=filter(lambda x: x["category_id"] == category_id, data)
    if isinstance(data, filter):
      data=[]
      self.params['count']=0
    self.params['data']=data
    self.params['form']=BookSearchForm(request.POST)
    self.params['search']=request.POST['search']
    self.params['category_id']=category_id
    return render(request, 'bookdoor/book_search.html',self.params)


class BookSearchCategoriView(TemplateView):
  
  def __init__(self):

    self.params={
      'form':BookSearchForm(),
      'search':'',
      'data':'',
      'count':'',
      'category':Category.objects.all(),
      'category_id':'',
    }

  def get(self,request,category_id,search):
    data=Book.objects.filter(Q(title__icontains=search)|Q(author__icontains=search)|Q(illustrator__icontains=search)|Q(translator__icontains=search)|Q(publisher__icontains=search))
    if category_id != 0:
      data=filter(lambda x: x["category_id"] == category_id, data)
    if isinstance(data, filter):
      data=[]
      self.params['count']=0
    self.params['data']=data
    initial_dict=dict(search=search)
    self.params['form']=BookSearchForm(request.GET or None, initial=initial_dict)
    self.params['category_id']=category_id
    return render(request,'bookdoor/book_search.html', self.params)

  def post(self,request,category_id,search):
    return render(request, 'bookdoor/book_search.html',self.params)


class BookCreateView(LoginRequiredMixin,TemplateView):

  def __init__(self):
    self.params={
      'form':BookCreateForm(),
    }

  def get(self,request):
    return render(request,'bookdoor/book_create.html', self.params)

  def post(self,request):
    user=self.request.user
    book=Book()
    book.title=request.POST['title']
    book.author=request.POST['author']
    book.illustrator=request.POST['illustrator']
    book.translator=request.POST['translator']
    book.publisher=request.POST['publisher']
    if request.POST['category'] !=0:
      book.category_id=request.POST['category']
    book.url=request.POST['url']
    book.date=request.POST['date']
    dat=string.digits + string.ascii_lowercase + string.ascii_uppercase
    while True:
      item=''.join([random.choice(dat) for i in range(10)])
      judge=Book.objects.filter(code=item).count()
      if judge==0:
        break
    book.code=item
    if user.code=='aaaaaaaaaa':
      book.save()
    return redirect(to='/book_search/0')