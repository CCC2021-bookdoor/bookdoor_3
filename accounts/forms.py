from django import forms
from django.contrib.admin.widgets import AdminDateWidget
from django.db.models import fields
from allauth.account.forms import SignupForm
from .models import CustomUser, Profile
import random
import string
import datetime

class ProfileForm(forms.ModelForm):
  class Meta:
    model=Profile
    fields=['nickname','email']

class SignupUserForm(SignupForm):
  now=datetime.datetime.now()
  this_year=now.year
  years = []
  for i in range(118):
    years.append(this_year-i)

  birthday = forms.DateField( widget=forms.SelectDateWidget(years=years))
  
  def save(self, request):
    user=super(SignupUserForm,self).save(request)
    dat=string.digits + string.ascii_lowercase + string.ascii_uppercase
    while True:
      item=''.join([random.choice(dat) for i in range(10)])
      judge=CustomUser.objects.filter(code=item).count()
      if judge==0:
        break
    user.code=item
    user.birthday=self.cleaned_data['birthday']
    user.save()
    return user


class ProfileCreateForm(forms.Form):

  data=[
    (1,'初恋の人の名前(はつこいのひとのなまえ)'),
    (2,'初めて見た映画(はじめてみたえいが)'),
    (3,'初めての旅行に行った場所(はじめてのりょこうにいったばしょ)'),
    (4,'おふくろの味といえば(おふくろのあじといえば)'),
    (5,'生まれた病院の名前(うまれたびょういんのなまえ)'),
  ]

  nickname=forms.CharField(label='ニックネーム',max_length=20)
  choices=forms.ChoiceField(label='秘密の質問(ひみつのしつもん)',choices=data)
  secreat=forms.CharField(label='',max_length=20)
  email=forms.EmailField(label='メール',required=False)