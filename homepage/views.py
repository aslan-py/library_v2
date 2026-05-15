from django.views.generic import ListView

from core.constants import ViewsConstants

from .mixins import BookMixin, ReaderMixin


class DashboardListView(ReaderMixin, ListView):
    """Главная страница CRM с дашбордом библиотек.

    get_queryset:
        - Собирает аннотированный список библиотек.
        - Применяет поиск по названию.
    get_context_data:
        - Добавляет глобальную агрегированную статистику.
        - Добавляет search_query для сохранения состояния формы.
    """

    template_name = 'homepage/index.html'
    context_object_name = 'libraries'
    paginate_by = ViewsConstants.MAIN_PAGINATOR

    def get_queryset(self):
        queryset = self.get_annotated_libraries()
        self.search_query = self.get_search_query()
        if self.search_query:
            queryset = queryset.filter(name__icontains=self.search_query)
        return queryset

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        context['global_stats'] = self.get_global_book_stats()
        context['total_readers'] = self.get_global_reader_stats()
        context['search_query'] = self.search_query
        return context


class LibraryListView(BookMixin, ListView):
    """Детальная страница библиотеки со списком её книг.

    get_queryset:
        - Получает объект библиотеки по PK.
        - Собирает книги этой библиотеки с select_related.
        - Применяет фильтры поиска.
    get_context_data:
        - Передает объект библиотеки в шаблон.
    """

    template_name = 'homepage/library_detail.html'
    context_object_name = 'books'
    paginate_by = ViewsConstants.PAGINATOR

    def get_queryset(self):
        self.library = self.get_library_by_pk(self.kwargs['pk'])
        queryset = self.get_optimized_books().filter(library=self.library)
        self.search_query = self.get_search_query()
        return self.filter_books(queryset, self.search_query)

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        context['library'] = self.library
        context['search_query'] = self.search_query
        return context


class TotalBookListView(BookMixin, ListView):
    """Список абсолютно всех книг сети.

    get_queryset:
        - Получает полный оптимизированный список книг.
        - Применяет универсальный поиск.
    """

    template_name = 'homepage/total_books.html'
    context_object_name = 'books'
    paginate_by = ViewsConstants.PAGINATOR

    def get_queryset(self):
        queryset = self.get_optimized_books()
        self.search_query = self.get_search_query()
        return self.filter_books(queryset, self.search_query)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.search_query
        return context


class ShelvedBookListView(BookMixin, ListView):
    """Список книг, находящихся на полках.

    get_queryset:
        - Фильтрует книги по признаку reader__isnull=True.
        - Применяет поиск.
    """

    template_name = 'homepage/shelves_books.html'
    context_object_name = 'books'
    paginate_by = ViewsConstants.PAGINATOR

    def get_queryset(self):
        queryset = self.get_optimized_books().filter(reader__isnull=True)
        self.search_query = self.get_search_query()
        return self.filter_books(queryset, self.search_query)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.search_query
        return context


class HandedBookListView(BookMixin, ListView):
    """Список книг, выданных читателям.

    get_queryset:
        - Фильтрует книги по признаку reader__isnull=False.
        - Применяет поиск.
    """

    template_name = 'homepage/handed_books.html'
    context_object_name = 'books'
    paginate_by = ViewsConstants.PAGINATOR

    def get_queryset(self):
        queryset = self.get_optimized_books().filter(reader__isnull=False)
        self.search_query = self.get_search_query()
        return self.filter_books(queryset, self.search_query)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.search_query
        return context


class TotalReaderListView(ReaderMixin, ListView):
    """Список всех читателей системы."""

    template_name = 'homepage/total_readers.html'
    context_object_name = 'readers'
    paginate_by = ViewsConstants.PAGINATOR

    def get_queryset(self):
        queryset = self.get_optimized_readers()
        self.search_query = self.get_search_query()
        return self.filter_readers(queryset, self.search_query)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.search_query
        return context
