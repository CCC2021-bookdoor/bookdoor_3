from django.conf import settings
from django.db import models


class Book(models.Model):
  title=models.CharField(max_length=100)
  author=models.CharField(max_length=100,blank=True, null=True)
  illustrator=models.CharField(max_length=100,blank=True, null=True)
  translator=models.CharField(max_length=100,blank=True, null=True)
  publisher=models.CharField(max_length=100,blank=True, null=True)
  category_id=models.IntegerField(blank=True, null=True)
  url=models.CharField(max_length=100,blank=True, null=True)
  code=models.CharField(max_length=10)
  evaluation=models.FloatField(default=0)
  date=models.DateField(blank=True, null=True)

  def __str__(self):
    return '<Book:id='+str(self.id)+','+\
      self.title+'('+self.author+')>'


class BookComment(models.Model):

  data=[
    (5,'5'),
    (4,'4'),
    (3,'3'),
    (2,'2'),
    (1,'1')
  ]

  book=models.ForeignKey(Book,on_delete=models.CASCADE,related_name='book')
  writer=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name='writer')
  evaluation=models.IntegerField(choices=data)
  title=models.CharField(max_length=20,blank=True, null=True)
  comment=models.CharField(max_length=5000,blank=True, null=True)
  code=models.CharField(max_length=10)
  spoiler=models.BooleanField(verbose_name='',default=False)
  date=models.DateField(blank=True,null=True)
  good=models.IntegerField(default=0)
  age=models.IntegerField(default=0)
  report=models.IntegerField(default=0)
  
  def __str__(self):
    return '<BookComment:id='+str(self.id)+','+\
      str(self.writer)+'('+str(self.evaluation)+')>'

    
class BookCommentGood(models.Model):
  owner=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name='book_comment_good_owner')
  comment=models.ForeignKey(BookComment,on_delete=models.CASCADE,related_name='book_comment_good_comment')
  date=models.DateField()

  def __str__(self):
    return '<BookCommentGood:id='+str(self.id)+','+\
      str(self.owner)+'('+str(self.date)+')>'


class BookCommentReport(models.Model):
  owner=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name='book_comment_report_owner')
  comment=models.ForeignKey(BookComment,on_delete=models.CASCADE,related_name='book_comment_report_comment')
  date=models.DateField()

  def __str__(self):
    return '<BookCommentReport:id='+str(self.id)+','+\
      str(self.owner)+'('+str(self.date)+')>'


class FavoriteBook(models.Model):
  owner=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name='favorite_book_owner')
  book=models.ForeignKey(Book,on_delete=models.CASCADE,related_name='favorite_book_book')

  def __str__(self):
    return '<FavoriteBook:id='+str(self.id)+','+\
      str(self.owner)+'>'


class Category(models.Model):
  category=models.CharField(max_length=20)

  def __str__(self):
    return '<Category:id='+str(self.id)+','+\
      str(self.category)+'>'