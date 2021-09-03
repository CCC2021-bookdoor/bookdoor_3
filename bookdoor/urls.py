from django.urls import path
from . import views
from .views import BookDoorView

app_name='bookdoor'
urlpatterns=[
  path(r'',BookDoorView.as_view(), name='index'),
]