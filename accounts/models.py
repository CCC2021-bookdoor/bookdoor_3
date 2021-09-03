from django.db import models
from django.conf import settings
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.contrib.auth.models import UserManager,PermissionsMixin
from django.utils import timezone


class UserManager(UserManager):
  use_in_migrations=True


  def _create_user(self, username, password, **extra_fields):
    if not username:
      raise ValueError('ユーザーネームをください')
    username=self.model.normalize_username(username)
    user=self.model(username=username, **extra_fields)
    user.set_password(password)
    user.save(using=self._db)
    return user

  def create_user(self, username, password=None, **extra_fields):
    extra_fields.setdefault('is_staff',False)
    extra_fields.setdefault('is_superuser',False)
    return self._create_user(username, password, **extra_fields)

  def create_superuser(self, username, password, **extra_fields):
    extra_fields.setdefault('is_staff',True)
    extra_fields.setdefault('is_superuser',True)

    if extra_fields.get('is_staff') is not True:
      raise ValueError('Superuser must have is_staff=True.')
    if extra_fields.get('is_superuser') is not True:
      raise ValueError('Superuser must have is_superuser=True.')
    
    return self._create_user(username, password, **extra_fields)

class CustomUser(AbstractBaseUser, PermissionsMixin):

  username_validator = UnicodeUsernameValidator()

  username=models.CharField(
    'ユーザーネーム',
    max_length=20, 
    unique=True,
    help_text='20文字以内です',
    validators=[username_validator],
    error_messages={
      'unique': "すでに登録されているユーザーネームです"
      },
  )
  code=models.CharField('コード', max_length=10,null=True)
  birthday=models.DateField('誕生日',null=True)
  date=models.DateTimeField('入会日', default=timezone.now)
  is_staff=models.BooleanField(
    'staff status',
    default=False,
    help_text=('Designates whether the user can log into this admin site.'),
  )
  is_active=models.BooleanField(
    'active',
    default=True,
    help_text=(
      'Designates whether this user should be treated as active.'
      'Unselect this instead of deleting accounts.'
      ),
  )

  objects=UserManager()


  USERNAME_FIELD='username'
  REQUIRED_FIELDS=[]

  class Meta:
    verbose_name='user'
    verbose_name_plural='users'

class Profile(models.Model):
  owner=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
  nickname=models.CharField(max_length=20)
  choices=models.IntegerField()
  secret=models.CharField(max_length=20)
  email=models.EmailField(unique=True,null=True,blank=True)

  def __str__(self):
    return '<Profile:id='+str(self.id)+','+\
      str(self.owner)+'('+str(self.nickname)+')>'