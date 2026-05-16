from core.constants import ViewsConstants


class SearchMixin:
    """Миксин для добавления поиска."""

    def get_search_query(self):
        return self.request.GET.get('q', '').strip()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.get_search_query()
        return context


class BookListMixin:
    """Миксин для унификации конфигурации списков книг."""

    context_object_name = 'books'
    paginate_by = ViewsConstants.PAGINATOR
