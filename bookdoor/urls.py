from django.urls import path
from . import views
from .views import BookDoorView, BookSearchView, BookCreateView
from .views import BookSearchCategoriView

app_name='bookdoor'
urlpatterns=[
  path(r'',BookDoorView.as_view(), name='index'),
  path(r'book_search/<int:category_id>',BookSearchView.as_view(), name='book_search'),
  path(r'book_search/<int:category_id>/<str:search>',\
    BookSearchCategoriView.as_view(), name='book_search_category'),
  path(r'book_create',BookCreateView.as_view(), name='book_create'),
]