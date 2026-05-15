from django.contrib import admin

from core.constants import ConstantsAdmin

from .models import Book, Library, Reader


@admin.register(Library)
class LibraryAdmin(admin.ModelAdmin):
    """Настройки админки для библиотек."""

    list_display = ('id', 'name', 'capacity', 'get_books_count')
    list_display_links = ('id', 'name')
    search_fields = ('name',)

    @admin.display(description=ConstantsAdmin.BOOKS_COUNT_LABEL)
    def get_books_count(self, obj):
        """Возвращает количество книг в библиотеке."""
        return obj.books.count()


@admin.register(Reader)
class ReaderAdmin(admin.ModelAdmin):
    """Настройки админки для читателей."""

    list_display = ('id', 'name', 'phone', 'get_borrowed_books')
    list_display_links = ('id', 'name')
    search_fields = ('name', 'phone')

    def get_queryset(self, request):
        """Оптимизация: предзагрузка книг читателя."""
        return super().get_queryset(request).prefetch_related('borrowed_books')

    @admin.display(description=ConstantsAdmin.BORROWED_BOOKS_LABEL)
    def get_borrowed_books(self, obj):
        """Формирует строку со списком книг читателя."""
        books = obj.borrowed_books.all()
        if not books:
            return ConstantsAdmin.NO_BOOKS
        return ', '.join([
            f'{book.title}(№{book.inventory_number})' for book in books
        ])


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    """Настройки админки для книг."""

    list_display = (
        'id',
        'title',
        'author',
        'inventory_number',
        'library',
        'reader',
    )
    list_display_links = ('id', 'title', 'reader')
    list_filter = ('library', 'author')
    search_fields = (
        'title',
        'author',
        'inventory_number',
        'library__name',
    )
    list_per_page = ConstantsAdmin.LIST_PER_PAGE
    ordering = ('-id',)
    empty_value_display = ConstantsAdmin.EMPTY_VALUE

    list_select_related = ('library', 'reader')

    fieldsets = (
        (
            ConstantsAdmin.FIELDSET_BASE,
            {'fields': ('title', 'author', 'inventory_number')},
        ),
        (
            ConstantsAdmin.FIELDSET_STATUS,
            {
                'fields': ('library', 'reader'),
                'classes': ('collapse',),
            },
        ),
    )

    autocomplete_fields = ('library', 'reader')
    save_as = True
    save_on_top = True
