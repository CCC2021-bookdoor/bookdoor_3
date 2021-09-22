from django.contrib import admin
from .models import Book, BookComment, BookCommentGood,BookCommentReport
from .models import FavoriteBook, Category

admin.site.register(Book)
admin.site.register(BookComment)
admin.site.register(BookCommentGood)
admin.site.register(BookCommentReport)
admin.site.register(FavoriteBook)
admin.site.register(Category)