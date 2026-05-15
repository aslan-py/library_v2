from django.db.models import Count, Q
from django.shortcuts import get_object_or_404

from core.models import Book, Library, Reader


class LibraryDashboardMixin:
    """Миксин для всей логики дашборда: библиотеки и статистика."""

    def get_annotated_libraries(self):
        """Возвращает QuerySet библиотек с подсчетами книг."""
        return Library.objects.annotate(
            total_books=Count('books'),
            on_hand=Count('books', filter=Q(books__reader__isnull=False)),
            on_shelf=Count('books', filter=Q(books__reader__isnull=True)),
        ).order_by('-total_books')

    def get_global_book_stats(self):
        """Возвращает общую статистику по всем книгам."""
        return Book.objects.aggregate(
            total=Count('id'),
            on_hand=Count('id', filter=Q(reader__isnull=False)),
            on_shelf=Count('id', filter=Q(reader__isnull=True)),
        )

    def get_search_query(self):
        """Извлечение параметра поиска из GET-запроса."""
        return self.request.GET.get('q', '')


class BookMixin(LibraryDashboardMixin):
    """Миксин для работы со списками книг: фильтрация, поиск."""

    def get_optimized_books(self):
        """Базовый QuerySet книг с решением проблемы N+1."""
        return Book.objects.select_related('library', 'reader').order_by('-id')

    def get_library_by_pk(self, pk):
        """Возвращает объект библиотеки или 404."""
        return get_object_or_404(Library, pk=pk)

    def filter_books(self, queryset, query):
        """Применяет универсальный поиск по списку книг."""
        if not query:
            return queryset
        return queryset.filter(
            Q(inventory_number__icontains=query)
            | Q(title__icontains=query)
            | Q(author__icontains=query)
            | Q(library__name__icontains=query)
            | Q(reader__name__icontains=query)
        )


class ReaderMixin(LibraryDashboardMixin):
    """Миксин для работы со списками читателей."""

    def get_optimized_readers(self):
        """Возвращает QuerySet читателей."""
        return Reader.objects.all().order_by('name')

    def filter_readers(self, queryset, query):
        """Поиск по имени и телефону читателя."""
        if not query:
            return queryset
        return queryset.filter(
            Q(name__icontains=query) | Q(phone__icontains=query)
        )

    def get_global_reader_stats(self):
        """Возвращает общее количество читателей в системе."""
        return Reader.objects.count()
