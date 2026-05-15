from django.urls import path

from .views import BookCreateView, ReaderCreateView

app_name = 'core'

urlpatterns = [
    path('books/add/', BookCreateView.as_view(), name='book_add'),
    path('readers/add/', ReaderCreateView.as_view(), name='reader_add'),
]
