from django.shortcuts import render
from django.shortcuts import redirect
from django.views.generic import TemplateView
from accounts.models import CustomUser ,Profile
from .models import Book, BookComment, BookCommentGood
from .models import BookCommentReport, FavoriteBook, Category
from .forms import BookSearchForm, BookCreateForm,BookCommentForm
from django.db.models import Q
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
import datetime
import random
import string
import numpy as np


class BookDoorView(TemplateView):
  
  def __init__(self,):
    self.params={
      'books':'',
      'comment':'',
      'attention':'',
      'category':Category.objects.all(),
      'age_range':range(15),
    }

  def get(self,request):

    def default_ranking():
      ranking=[]

      books=Book.objects.all()
      today=datetime.date.today()
      if request.user.is_authenticated:
        birthday=request.user.birthday
        age=(int(today.strftime("%Y%m%d")) - int(birthday.strftime("%Y%m%d"))) // 10000

      for book in books:
        average=0.0
        total=0
        count=0
        book_comments=BookComment.objects.filter(book=book)
        if request.user.is_authenticated:
          book_comments=BookComment.objects.filter(book=book,\
            age__gte=age-1,age__lte=age+1)
        for book_comment in book_comments:
          if (int(today.strftime("%Y%m%d")) - \
            int(book_comment.date.strftime("%Y%m%d"))) <=100:
            item=1.25
          else:
            item=1
          total+=book_comment.evaluation*item
          count+=1
        if count == 0:
          count=1
        average=total/count
        ranking.append((book.id-1,average))
      
      return sorted(ranking, key=lambda r: r[1], reverse=True)

    def first_scores(user,book_count):
      book_comments=BookComment.objects.filter(writer=user)
      item=np.zeros(book_count)
      for book_comment in book_comments:
        id=book_comment.book_id
        item[id-1]=book_comment.evaluation

      return item

    def create_scores(target_user,book_count):
      scores=[]
      scores.append(first_scores(target_user,book_count))

      users=CustomUser.objects.all()
      for user in users:
        
        if user == target_user:
          continue

        book_comments=BookComment.objects.filter(writer=user)
        if len(book_comments) == 0:
          continue

        item=np.zeros(book_count)
        for book_comment in book_comments:
          id=book_comment.book_id
          item[id-1]=book_comment.evaluation

        scores.append(item)

      return np.array(scores)

    def create_age_scores(target_user,book_count):
      scores=[]
      scores.append(first_scores(target_user,book_count))

      today=datetime.date.today()
      birthday=request.user.birthday
      age=(int(today.strftime("%Y%m%d")) - int(birthday.strftime("%Y%m%d"))) // 10000

      users=CustomUser.objects.all()
      for user in users:
        
        if user == target_user:
          continue

        book_comments=BookComment.objects.filter(writer=user,\
          age__gte=age-1,age__lte=age+1)

        if len(book_comments) == 0:
          continue

        item=np.zeros(book_count)
        for book_comment in book_comments:
          id=book_comment.book_id
          item[id-1]=book_comment.evaluation

        scores.append(item)

      return np.array(scores)

    def get_correlation_coefficents(scores, target_user_index):
      similarities = []
      target = scores[target_user_index]
      
      for i, score in enumerate(scores):
        indices = np.where((target * score ) != 0)[0]
        if len(indices) < 3 or i == target_user_index:
          continue
        
        similarity = np.corrcoef(target[indices], score[indices])[0, 1]
        if np.isnan(similarity):
          continue
    
        similarities.append((i, similarity))
      
      return sorted(similarities, key=lambda s: s[1], reverse=True)

    def predict(scores, similarities, target_user_index, target_item_index):
      target = scores[target_user_index]
      
      avg_target = np.mean(target[np.where(target > 0)])
      
      numerator = 0.0
      denominator = 0.0
      k = 0
      
      for similarity in similarities:
        if k > 5 or similarity[1] <= 0.0:
          break
            
        score = scores[similarity[0]]
        if score[target_item_index] >= 0:
          denominator += similarity[1]
          numerator += similarity[1] * (score[target_item_index] - np.mean(score[np.where(score >= 0)]))
          k += 1
              
      return avg_target + (numerator / denominator) if denominator > 0 else -1

    def rank_items(scores, similarities, target_user_index,book_count):
      rankings = []
      target = scores[target_user_index]
      for i in range(book_count):
        if target[i] >= 1:
          continue

        rankings.append((i, predict(scores, similarities, target_user_index, i)))
          
      return sorted(rankings, key=lambda r: r[1], reverse=True)

    def mean_adjustment(scores):
      scores_nan = np.copy(scores)
      scores_nan[scores_nan == 0] = np.nan
      
      adjusted_scores = np.ndarray(shape=scores_nan.shape)
      for i, score in enumerate(scores_nan):
          adjusted_scores[i] = score - np.nanmean(score)
      return np.nan_to_num(adjusted_scores)

    def item_get_cos_similarities(scores, target_item_index):
      similarities = []

      items = mean_adjustment(scores).transpose()
      target_item = items[target_item_index]
      
      for i, item in enumerate(items):
        if i == target_item_index:
          continue
            
        similarity = np.dot(target_item, item.T) / (np.linalg.norm(target_item) * np.linalg.norm(item))
        similarities.append((i, similarity))

      return sorted(similarities, key=lambda s: s[1], reverse=True)

    def item_predict(scores, similarities, target_user_index):
      numerator = 0.0
      denominator = 0.0
      k = 0
      
      target = scores[target_user_index]
      
      for similarity in similarities:

          if (k >= 5 or similarity[1] <= 0):
              break
          if (target[similarity[0]] == 0):
              continue
              
          numerator += similarity[1] * target[similarity[0]]
          denominator += similarity[1]
          k += 1
      
      return numerator / denominator if denominator != 0.0 else -1

    def item_rank_items(scores, similarities, target_user_index,book_count):
      ranking = []

      for i in range(book_count):
        if scores[target_user_index][i] > 0:
          continue
        
        similarities =  item_get_cos_similarities(scores, i)
        
        predict_score = item_predict(scores, similarities, target_user_index)
        
        ranking.append((i, predict_score))
          
      return sorted(ranking, key=lambda r: r[1], reverse=True)

    def youser_filter(ranking_origin,target_user):
      comments=BookComment.objects.filter(writer=target_user)
      number_list=[]
      ranking=[]
      for comment in comments:
        number_list.append(comment.book_id-1)

      for rank in ranking_origin:
        if rank[0] not in number_list:
          ranking.append(rank)
      
      return ranking

    if request.user.is_authenticated:
      target_user=self.request.user
      last_book = Book.objects.all().last()
      book_count = last_book.id

      scores=create_scores(target_user,book_count)
      age_scores=create_age_scores(target_user,book_count)

      target_user_index = 0
      similarities = get_correlation_coefficents(scores, target_user_index)

      if len(similarities) !=0 and similarities[0][1] > 0:
        rank = rank_items(age_scores, similarities, target_user_index,book_count)
      else:
        rank = item_rank_items(age_scores, similarities, target_user_index,book_count)
        if len(rank) == 0:
          self.params['attention'] = 1
        elif np.isnan(rank[0][1]):
          ranking_origin=default_ranking()
          rank=youser_filter(ranking_origin,target_user)
    else:
      rank=default_ranking()


    books = []

    for id in rank:
      book=Book.objects.filter(id=id[0]+1)
      if len(book) != 0:
        books.append(book[0])
        

    if len(books) == 0:
      books=Book.objects.all().order_by('date').reverse()

    comment=BookComment.objects.filter(good__gte=10,title=True,comment=True).order_by('date', 'good')
    if len(comment) < 9:
      comment=BookComment.objects.order_by('date', 'good')

    k=0
    comment_loop=[]
    for item in comment:
      if k >= 9:
        break
      if item.comment != None and item.title != None:
        comment_loop.append(item)
        k+=1

    comment_set=[]
    for i in range(len(comment_loop)//3):
      item={}
      item['a']=comment_loop[i*3]
      item['b']=comment_loop[i*3+1]
      item['c']=comment_loop[i*3+2]
      comment_set.append(item)

    self.params['comment']=comment_set
    self.params['books']=books
    return render(request,'bookdoor/index.html', self.params)

  def post(self,request):

    return render(request, 'bookdoor/index.html',self.params)


class BookConditionView(TemplateView):
  
  def __init__(self,):
    self.params={
      'books':'',
      'attention':'',
      'category':Category.objects.all(),
      'category_id':'',
      'age':'',
      'age_range':range(15),
    }

  def get(self,request,category_id,age):

    def default_ranking(age):
      ranking=[]

      books=Book.objects.all()
      today=datetime.date.today()

      for book in books:
        average=0.0
        total=0
        count=0
        if age != 0:
          book_comments=BookComment.objects.filter(book=book,age__lte=age*3, age__gte=age*3-2)
        else:
          book_comments=BookComment.objects.filter(book=book)

        for book_comment in book_comments:
          if (int(today.strftime("%Y%m%d")) - \
            int(book_comment.date.strftime("%Y%m%d"))) <=100:
            item=1.25
          else:
            item=1
          total+=book_comment.evaluation*item
          count+=1
        if count == 0:
          count=1
        average=total/count
        ranking.append((book.id-1,average))
      
      return sorted(ranking, key=lambda r: r[1], reverse=True)

    def first_scores(user,book_count):
      book_comments=BookComment.objects.filter(writer=user)
      item=np.zeros(book_count)
      for book_comment in book_comments:
        id=book_comment.book_id
        item[id-1]=book_comment.evaluation

      return item

    def create_scores(target_user,book_count):
      scores=[]
      scores.append(first_scores(target_user,book_count))

      users=CustomUser.objects.all()
      for user in users:
        
        if user == target_user:
          continue

        book_comments=BookComment.objects.filter(writer=user)
        if len(book_comments) == 0:
          continue

        item=np.zeros(book_count)
        for book_comment in book_comments:
          id=book_comment.book_id
          item[id-1]=book_comment.evaluation

        scores.append(item)

      return np.array(scores)

    def create_age_scores(target_user,book_count,age):
      scores=[]
      scores.append(first_scores(target_user,book_count))

      today=datetime.date.today()

      users=CustomUser.objects.all()
      for user in users:
        
        if user == target_user:
          continue

        if age != 0:
          book_comments=BookComment.objects.filter(writer=user,age__lte=age*3, age__gte=age*3-2)
        else:
          book_comments=BookComment.objects.filter(writer=user)

        if len(book_comments) == 0:
          continue

        item=np.zeros(book_count)
        for book_comment in book_comments:
          id=book_comment.book_id
          item[id-1]=book_comment.evaluation

        scores.append(item)

      return np.array(scores)

    def get_correlation_coefficents(scores, target_user_index):
      similarities = []
      target = scores[target_user_index]
      
      for i, score in enumerate(scores):
        indices = np.where((target * score ) != 0)[0]
        if len(indices) < 3 or i == target_user_index:
          continue
        
        similarity = np.corrcoef(target[indices], score[indices])[0, 1]
        if np.isnan(similarity):
          continue
    
        similarities.append((i, similarity))
      
      return sorted(similarities, key=lambda s: s[1], reverse=True)

    def predict(scores, similarities, target_user_index, target_item_index):
      target = scores[target_user_index]
      
      avg_target = np.mean(target[np.where(target > 0)])
      
      numerator = 0.0
      denominator = 0.0
      k = 0
      
      for similarity in similarities:
        if k > 5 or similarity[1] <= 0.0:
          break
            
        score = scores[similarity[0]]
        if score[target_item_index] >= 0:
          denominator += similarity[1]
          numerator += similarity[1] * (score[target_item_index] - np.mean(score[np.where(score >= 0)]))
          k += 1
              
      return avg_target + (numerator / denominator) if denominator > 0 else -1

    def rank_items(scores, similarities, target_user_index,book_count):
      rankings = []
      target = scores[target_user_index]
      for i in range(book_count):
        if target[i] >= 1:
          continue

        rankings.append((i, predict(scores, similarities, target_user_index, i)))
          
      return sorted(rankings, key=lambda r: r[1], reverse=True)

    def mean_adjustment(scores):
      scores_nan = np.copy(scores)
      scores_nan[scores_nan == 0] = np.nan
      
      adjusted_scores = np.ndarray(shape=scores_nan.shape)
      for i, score in enumerate(scores_nan):
          adjusted_scores[i] = score - np.nanmean(score)
      return np.nan_to_num(adjusted_scores)

    def item_get_cos_similarities(scores, target_item_index):
      similarities = []

      items = mean_adjustment(scores).transpose()
      target_item = items[target_item_index]
      
      for i, item in enumerate(items):
        if i == target_item_index:
          continue
            
        similarity = np.dot(target_item, item.T) / (np.linalg.norm(target_item) * np.linalg.norm(item))
        similarities.append((i, similarity))

      return sorted(similarities, key=lambda s: s[1], reverse=True)

    def item_predict(scores, similarities, target_user_index):
      numerator = 0.0
      denominator = 0.0
      k = 0
      
      target = scores[target_user_index]
      
      for similarity in similarities:

          if (k >= 5 or similarity[1] <= 0):
              break
          if (target[similarity[0]] == 0):
              continue
              
          numerator += similarity[1] * target[similarity[0]]
          denominator += similarity[1]
          k += 1
      
      return numerator / denominator if denominator != 0.0 else -1

    def item_rank_items(scores, similarities, target_user_index,book_count):
      ranking = []

      for i in range(book_count):
        if scores[target_user_index][i] > 0:
          continue
        
        similarities =  item_get_cos_similarities(scores, i)
        
        predict_score = item_predict(scores, similarities, target_user_index)
        
        ranking.append((i, predict_score))
          
      return sorted(ranking, key=lambda r: r[1], reverse=True)

    def youser_filter(ranking_origin,target_user):
      comments=BookComment.objects.filter(writer=target_user)
      number_list=[]
      ranking=[]
      for comment in comments:
        number_list.append(comment.book_id-1)

      for rank in ranking_origin:
        if rank[0] not in number_list:
          ranking.append(rank)
      
      return ranking

    if request.user.is_authenticated:
      target_user=self.request.user
      last_book = Book.objects.all().last()
      book_count = last_book.id

      scores=create_scores(target_user,book_count)
      age_scores=create_age_scores(target_user,book_count,age)
      if len(age_scores) <= 1:
        age_scores=scores

      target_user_index = 0
      similarities = get_correlation_coefficents(scores, target_user_index)

      if len(similarities) !=0 and similarities[0][1] > 0:
        rank = rank_items(age_scores, similarities, target_user_index,book_count)
      else:
        rank = item_rank_items(age_scores, similarities, target_user_index,book_count)
        if len(rank) == 0:
          self.params['attention'] = 1
        elif np.isnan(rank[0][1]):
          ranking_origin=default_ranking(age)
          rank=youser_filter(ranking_origin,target_user)
    else:
      rank=default_ranking(age)


    books = []

    for id in rank:
      book=Book.objects.filter(id=id[0]+1)
      if len(book) != 0 :
        if category_id == 0 or book[0].category_id == category_id:
          books.append(book[0])

    if len(books) == 0:
      books=Book.objects.all().order_by('date').reverse()


    comment=BookComment.objects.filter(good__gte=10,title=True,comment=True).order_by('date', 'good')
    if len(comment) < 9:
      comment=BookComment.objects.order_by('date', 'good')

    k=0
    comment_loop=[]
    for item in comment:
      if k >= 9:
        break
      if item.comment != None and item.title != None:
        comment_loop.append(item)
        k+=1

    comment_set=[]
    for i in range(len(comment_loop)//3):
      item={}
      item['a']=comment_loop[i*3]
      item['b']=comment_loop[i*3+1]
      item['c']=comment_loop[i*3+2]
      comment_set.append(item)

    self.params['comment']=comment_set
    self.params['books']=books
    self.params['category_id']=category_id
    self.params['age']=age
    return render(request,'bookdoor/book_condition.html', self.params)

  def post(self,request):

    return render(request, 'bookdoor/book_condition.html',self.params)


class BookSearchView(TemplateView):
  
  def __init__(self):

    self.params={
      'form':BookSearchForm(),
      'search':'None',
      'data':'',
      'count':'',
      'category':Category.objects.all(),
      'category_id':'',
    }

  def get(self,request,category_id,search):
    if search != 'None' and category_id != 0:
      data=Book.objects.filter(Q(title__icontains=search)|Q(author__icontains=search)|\
        Q(illustrator__icontains=search)|Q(translator__icontains=search)|\
          Q(publisher__icontains=search)).filter(category_id=category_id)
    elif category_id != 0:
      data=Book.objects.filter(category_id=category_id)
    elif search != 'None':
      data=Book.objects.filter(Q(title__icontains=search)|Q(author__icontains=search)|\
        Q(illustrator__icontains=search)|Q(translator__icontains=search)|\
          Q(publisher__icontains=search))
    else:
      data=Book.objects.all()

    for item in data:
      count=BookComment.objects.filter(book=item).count()
      item.count=count
    
    self.params['count']=len(data)
    self.params['data']=data
    if search != 'None':
      initial_dict=dict(search=search)
      self.params['form']=BookSearchForm(request.GET or None, initial=initial_dict)
    self.params['search']=search
    self.params['category_id']=category_id
    return render(request,'bookdoor/book_search.html', self.params)

  def post(self,request,category_id,search):
    if request.POST['search'] == '':
      return redirect(to='/book_search/'+str(category_id)+'/None')
    search=request.POST['search']
    if category_id != 0:
      data=Book.objects.filter(Q(title__icontains=search)|Q(author__icontains=search)|\
        Q(illustrator__icontains=search)|Q(translator__icontains=search)|\
          Q(publisher__icontains=search)).filter(category_id=category_id)
    else:
      data=Book.objects.filter(Q(title__icontains=search)|Q(author__icontains=search)|\
        Q(illustrator__icontains=search)|Q(translator__icontains=search)|\
          Q(publisher__icontains=search))
    self.params['count']=len(data)
    self.params['data']=data
    self.params['form']=BookSearchForm(request.POST)
    self.params['search']=search
    self.params['category_id']=category_id
    return render(request, 'bookdoor/book_search.html',self.params)


class BookDetailView(TemplateView):

  def __init__(self):
    self.params={
      'form':BookSearchForm(),
      'comment':'',
      'book':'',
      'count':0,
    }

  def get(self,request,book_code):
    book=Book.objects.get(code=book_code)
    comment_item=BookComment.objects.filter(book=book.id)
    comment=[]
    for item in comment_item:
      if item.comment != None and item.title != None:
        profile=Profile.objects.get(owner=item.writer)
        item.nickname=profile.nickname
        if request.user.is_authenticated:
          owner=self.request.user
          count_comment=BookComment.objects.get(code=item.code)
          count_good=BookCommentGood.objects.filter(owner=owner,comment=count_comment).count()
          count_report=BookCommentReport.objects.filter(owner=owner,comment=count_comment).count()
          item.count_good=count_good
          item.count_report=count_report
        comment.append(item)
    if request.user.is_authenticated:
      count=FavoriteBook.objects.filter(owner=request.user,book=book).count()
      self.params['count']=count
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
      title=request.POST['title']
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
      today=datetime.date.today()
      birthday=writer.birthday
      age=(int(today.strftime("%Y%m%d")) - int(birthday.strftime("%Y%m%d"))) // 10000
      value=BookComment(book=book,writer=writer,evaluation=evaluation,comment=comment,\
        code=code,date=date,age=age,title=title)
      value.save()
    return redirect(to='/book_detail/'+str(book_code))


@login_required
def book_comment_good(request,code):
  owner=request.user
  comment=BookComment.objects.get(code=code)
  count=BookCommentGood.objects.filter(owner=owner,comment=comment).count()
  if count<=0:
    date=datetime.date.today()
    good=BookCommentGood(owner=owner,comment=comment,date=date)
    good.save()
    comment.good+=1
    comment.save()
  else:
    good=BookCommentGood.objects.filter(owner=owner,comment=comment)
    for item in good:
      item.delete()
      comment.good-=1
      comment.save()
  book_id=comment.book
  book=Book.objects.get(id=book_id.id)
  book_code=book.code
  return redirect(to='/book_detail/'+str(book_code))


@login_required
def book_comment_report(request,code):
  owner=request.user
  comment=BookComment.objects.get(code=code)
  count=BookCommentReport.objects.filter(owner=owner,comment=comment).count()
  if count<=0:
    date=datetime.date.today()
    report=BookCommentReport(owner=owner,comment=comment,date=date)
    report.save()
    comment.report+=1
    comment.save()
  else:
    report=BookCommentReport.objects.filter(owner=owner,comment=comment)
    for item in report:
      item.delete()
      comment.report-=1
      comment.save()
  book_id=comment.book
  book=Book.objects.get(id=book_id.id)
  book_code=book.code
  return redirect(to='/book_detail/'+str(book_code))


@login_required
def favorite_book(request,code):
  owner=request.user
  book=Book.objects.get(code=code)
  count=FavoriteBook.objects.filter(owner=owner,book=book).count()
  if count<=0:
    favorite=FavoriteBook(owner=owner,book=book)
    favorite.save()
  else:
    favorite=FavoriteBook.objects.filter(owner=owner,book=book)
    item=favorite[0]
    item.delete()
  book_code=book.code
  return redirect(to='/book_detail/'+str(book_code))


class FavoriteBookListView(LoginRequiredMixin,TemplateView):
  
  def __init__(self):

    self.params={
      'form':BookSearchForm(),
      'data':'',
      'count':'',
      'category':Category.objects.all(),
      'category_id':'',
      'page_range':'',
    }

  def get(self,request,category_id,page=1):
    if  category_id != 0:
      data=Book.objects.filter(category_id=category_id)
    else:
      data=Book.objects.all()
    my_data=[]
    for item in data:
      count = FavoriteBook.objects.filter(owner=request.user,book=item).count()
      if count > 0:
        my_data.append(item)
    self.params['count']=len(my_data)

    my_data_item=Paginator(my_data,12)
    page_count=my_data_item.num_pages
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

    self.params['data']=my_data_item.get_page(page)
    self.params['page_range']=page_range
    self.params['category_id']=category_id
    return render(request,'bookdoor/favorite_book_list.html', self.params)

  def post(self,request,category_id,search):
    return render(request, 'bookdoor/favorite_book_list.html',self.params)


class BookRankingView(TemplateView):
  
  def __init__(self):

    self.params={
      'data':'',
    }

  def get(self,request):
    data=[]
    categories=Category.objects.all()
    for category in categories:
      books=Book.objects.filter(category_id=category.id)
      for book in books:
        count=BookComment.objects.filter(book=book).count()
        book.count=count
      if len(books) >1:
        books=sorted(books, key=lambda r: r.count, reverse=True)
      if len(books) == 0:
        data.append(
          {'category':category,
          'book':books,
          'count':0}
        )
      elif len(books) < 5:
        data.append(
          {'category':category,
          'book':books[0:len(books)-1],
          'count':len(books)-1}
        )
      else:
        data.append(
          {'category':category.category,
          'book':books[0:4],
          'count':5}
        )

    self.params['data']=data 
    return render(request,'bookdoor/book_ranking.html', self.params)

  def post(self,request):
    return render(request, 'bookdoor/book_ranking.html',self.params)


class CommentSearchView(TemplateView):
  
  def __init__(self):

    self.params={
      'form':BookSearchForm(),
      'search':'None',
      'data':'',
      'category':Category.objects.all(),
      'category_id':'',
      'evaluation':'',
      'evaluation_list':[5,4,3,2,1],
    }

  def get(self,request,category_id,search,evaluation):
    if search != 'None':
      data=BookComment.objects.filter(Q(title__icontains=search)|\
        Q(comment__icontains=search)).filter(title__isnull = False,\
          comment__isnull = False )
    else:
      data=BookComment.objects.filter(title__isnull = False, comment__isnull = False)
    
    data_list=[]
    if category_id != 0 and evaluation != 0:
      for item in data:
        if item.book.category_id == category_id and item.evaluation == evaluation:
          data_list.append(item)
      data=data_list
    elif category_id !=0:
      for item in data:
        if item.book.category_id == category_id :
          data_list.append(item)
      data=data_list
    elif evaluation !=0:
      for item in data:
        if item.evaluation == evaluation:
          data_list.append(item)
      data=data_list

    self.params['data']=sorted(data, key = lambda x: x.date,reverse=True)

    if search != 'None':
      initial_dict=dict(search=search)
      self.params['form']=BookSearchForm(request.GET or None, initial=initial_dict)
    self.params['search']=search
    self.params['category_id']=category_id
    self.params['evaluation']=evaluation
    return render(request,'bookdoor/comment_search.html', self.params)

  def post(self,request,category_id,search,evaluation):
    if request.POST['search'] == '':
      return redirect(to='/comment_search/'+str(category_id)+'/None/'+str(evaluation))
    search=request.POST['search']
    data=BookComment.objects.filter(Q(title__icontains=search)|\
      Q(comment__icontains=search))\
        .filter(title__isnull = False, comment__isnull = False)
    
    data_list=[]
    if category_id != 0 and evaluation != 0:
      for item in data:
        if item.book.category_id == category_id and item.evaluation == evaluation:
          data_list.append(item)
      data=data_list
    elif category_id !=0:
      for item in data:
        if item.book.category_id == category_id :
          data_list.append(item)
      data=data_list
    elif evaluation !=0:
      for item in data:
        if item.evaluation == evaluation:
          data_list.append(item)
      data=data_list

    self.params['data']=sorted(data, key = lambda x: x.date,reverse=True)
    
    if search != 'None':
      initial_dict=dict(search=search)
      self.params['form']=BookSearchForm(request.GET or None, initial=initial_dict)
    self.params['search']=search
    self.params['category_id']=category_id
    self.params['evaluation']=evaluation
    return render(request,'bookdoor/comment_search.html', self.params)


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


class BookRankingCategoryView(TemplateView):
  
  def __init__(self):

    self.params={
      'book':'',
      'category':'',
    }

  def get(self,request,category_id):
    books=Book.objects.filter(category_id=category_id)
    for book in books:
      count=BookComment.objects.filter(book=book).count()
      book.count=count
    if len(books) >1:
      books=sorted(books, key=lambda r: r.count, reverse=True)

    if len(books) < 30:
      books=books[0:len(books)-1]
    else:
      books=books[0:30]

    self.params['book']=books
    self.params['category']=Category.objects.get(id=category_id)
    return render(request,'bookdoor/book_ranking_category.html', self.params)

  def post(self,request):
    return render(request, 'bookdoor/book_ranking_category.html',self.params)
