from django.shortcuts import render
from django.shortcuts import redirect
from django.views.generic import TemplateView
from django.contrib.auth import get_user_model
from accounts.models import Profile
from .models import Book, BookComment, BookCommentGood
from .models import BookCommentReport, FavoriteBook, Category
from .forms import BookSearchForm, BookCreateForm,BookCommentForm
from django.db.models import Q
import datetime
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


class BookDetailView(TemplateView):

  def __init__(self):
    self.params={
      'form':BookSearchForm(),
      'comment':'',
      'book':'',
    }

  def get(self,request,book_code):
    book=Book.objects.get(code=book_code)
    comment_item=BookComment.objects.filter(book=book.id)
    comment=[]
    for item in comment_item:
      if len(item.comment) != 0:
        profile=Profile.objects.get(owner=request.user)
        item.nickname=profile.nickname
        # if request.user.is_authenticated:
        #   owner=self.request.user
        #   count_comment=BookComment.objects.get(code=item['code'])
        #   count_good=BookCommentGood.objects.filter(owner=owner,comment=count_comment).count()
        #   count_report=BookCommentReport.objects.filter(owner=owner,comment=count_comment).count()
        #   item['count_good']=count_good
        #   item['count_report']=count_report
        comment.append(item)
    self.params['comment']=comment
    self.params['book']=book
    return render(request,'bookdoor/book_detail.html', self.params)

  def post(self,request,book_code):
    return render(request,'bookdoor/book_detail.html', self.params)


class BookCommentView(LoginRequiredMixin,TemplateView):

  def __init__(self):
    self.params={
      'form':BookCommentForm(),
      'book':'',
      'attention':'',
    }

  def get(self,request,book_code):
    book=Book.objects.get(code=book_code)
    writer=self.request.user
    value_count=BookComment.objects.filter(book=book,writer=writer).count()
    if value_count >= 1:
      self.params['attention']='あなたはこの本をすでに評価しています。評価やコメントの内容が更新されます。'
      value=BookComment.objects.filter(book=book,writer=writer)
      value=value[0]
      self.params['create']=BookCommentForm(instance=value)
    self.params['book']=book
    return render(request,'bookdoor/book_comment.html', self.params)

  def post(self,request,book_code):
    book=Book.objects.get(code=book_code)
    writer=self.request.user
    value_count=BookComment.objects.filter(book=book,writer=writer).count()
    if value_count >= 1:
      value=BookComment.objects.filter(book=book,writer=writer)
      value=value[0]
      comment=BookCommentForm(request.POST,instance=value)
      comment.save()
    else:
      date=datetime.date.today()
      date_count=BookComment.objects.filter(date=date,writer=writer,\
        comment__isnull = False).count()
      evaluation=request.POST['evaluation']
      comment=request.POST['comment']
      if date_count >= 3 and comment is not None:
        return render(request,'bookdoor/comment_attention.html', self.params)
      dat=string.digits + string.ascii_lowercase + string.ascii_uppercase
      while True:
        item=''.join([random.choice(dat) for i in range(10)])
        judge=BookComment.objects.filter(code=item).count()
        if judge==0:
          break
      code=item
      value=BookComment(book=book,writer=writer,evaluation=evaluation,comment=comment,\
        code=code,date=date)
      value.save()
    return redirect(to='/book_detail/'+str(book_code))


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