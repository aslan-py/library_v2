from django.views.generic import CreateView

from .models import Book


class BookCreateView(CreateView):
    """Представление для добавления новой книги.

    Включает валидацию вместимости библиотеки.
    """

    model = Book
    template_name = 'core/books.html'
    fields = '__all__'
