from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from django.views.generic import ListView

from core.constants import ViewsConstants
from core.models import Book, Library

from .mixins import BookListMixin, SearchMixin


class DashboardListView(SearchMixin, ListView):
    """Главная страница CRM с дашбордом библиотек."""

    template_name = 'homepage/index.html'
    context_object_name = 'libraries'
    paginate_by = ViewsConstants.MAIN_PAGINATOR

    def get_queryset(self):
        """Формирует список библиотек с аннотацией количества книг."""
        queryset = Library.objects.annotate(
            total_books=Count('books')
        ).order_by('-total_books')

        query = self.get_search_query()
        if query:
            queryset = queryset.filter(name__icontains=query)

        return queryset

    def get_context_data(self, **kwargs) -> dict:
        """Расширяет контекст шаблона дополнительными данными."""
        context = super().get_context_data(**kwargs)
        context['global_stats'] = Book.objects.count()
        return context


class LibraryListView(SearchMixin, BookListMixin, ListView):
    """Детальная страница библиотеки со списком её книг."""

    template_name = 'homepage/library_detail.html'

    def get_queryset(self):
        """Формирует список книг конкретной библиотеки."""
        self.library = get_object_or_404(Library, pk=self.kwargs['pk'])
        queryset = (
            Book.objects
            .filter(library=self.library)
            .select_related('library')
            .order_by('-id')
        )

        query = self.get_search_query()
        if query:
            queryset = queryset.filter(
                Q(inventory_number__icontains=query)
                | Q(title__icontains=query)
                | Q(author__icontains=query)
            )
        return queryset

    def get_context_data(self, **kwargs) -> dict:
        """Расширяет контекст данными о текущей библиотеке."""
        context = super().get_context_data(**kwargs)
        context['library'] = self.library
        return context


class TotalBookListView(SearchMixin, BookListMixin, ListView):
    """Список абсолютно всех книг сети."""

    template_name = 'homepage/total_books.html'

    def get_queryset(self):
        queryset = Book.objects.select_related('library').order_by('-id')
        query = self.get_search_query()
        if query:
            queryset = queryset.filter(
                Q(inventory_number__icontains=query)
                | Q(title__icontains=query)
                | Q(author__icontains=query)
                | Q(library__name__icontains=query)
            )
        return queryset
