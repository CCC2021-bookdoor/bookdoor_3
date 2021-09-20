from django.urls import path
from . import views
from .views import BookDoorView, BookSearchView, BookCreateView
from .views import BookDetailView, BookCommentView, BookConditionView
from .views import FavoriteBookListView,BookRankingView
from .views import CommentSearchView

app_name='bookdoor'
urlpatterns=[
  path(r'',BookDoorView.as_view(), name='index'),
  path(r'book_condition/<int:category_id>/<int:age>',\
    BookConditionView.as_view(), name='book_condition'),
  path(r'book_search/<int:category_id>/<str:search>',BookSearchView.as_view(),\
     name='book_search'),
  path(r'book_detail/<str:book_code>',BookDetailView.as_view(), name='book_detail'),
  path(r'book_comment/<str:book_code>',BookCommentView.as_view(), name='book_comment'),
  path(r'book_comment_good/<str:code>',views.book_comment_good,name='book_comment_good'),
  path(r'book_comment_report/<str:code>',views.book_comment_report,\
     name='book_comment_report'),
  path(r'favorite_book/<str:code>',views.favorite_book,\
     name='favorite_book'),
  path(r'favorite_book_list/<int:category_id>/<str:search>',\
    FavoriteBookListView.as_view(),name='favorite_book_list'),
  path(r'book_ranking',BookRankingView.as_view(),name='book_ranking'),
  path(r'comment_search/<int:category_id>/<str:search>/<int:evaluation>',\
    CommentSearchView.as_view(),name='comment_search'),
  path(r'book_create',BookCreateView.as_view(), name='book_create'),
]