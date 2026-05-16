from django.urls import path

from .views import BookCreateView

app_name = 'core'

urlpatterns = [
    path('books/add/', BookCreateView.as_view(), name='book_add'),
]
