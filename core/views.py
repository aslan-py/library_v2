from django.urls import reverse_lazy
from django.views.generic import CreateView

from .models import Book, Reader


class BookCreateView(CreateView):
    """Представление для добавления новой книги.

    Включает валидацию вместимости библиотеки.
    """

    model = Book
    template_name = 'core/books.html'
    fields = '__all__'


class ReaderCreateView(CreateView):
    """Представление для добавления нового читателя."""

    model = Reader
    template_name = 'core/readers.html'
    fields = (
        'name',
        'phone',
    )
    success_url = reverse_lazy('homepage:total_readers')
