from django import forms
from .models import Book, Category

class BookSearchForm(forms.Form):
  search=forms.CharField(label='')



class BookCreateForm(forms.Form):
  data=[(0,'無し')]
  for category in Category.objects.all():
    item=(category.id,category.category)
    data.append(item)

  title=forms.CharField(label='タイトル',max_length=100)
  author=forms.CharField(label='筆者',max_length=100,required=None)
  illustrator=forms.CharField(label='イラストライター',max_length=100,required=None)
  translator=forms.CharField(label='翻訳者',max_length=100,required=None)
  publisher=forms.CharField(label='出版社',max_length=100,required=None)
  category=forms.ChoiceField(label='カテゴリー',choices=data,required=None)
  url=forms.CharField(label='URL',max_length=100)
  date=forms.DateField(label='発行日',required=None)