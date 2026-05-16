from django.contrib import admin

from core.constants import ConstantsAdmin

from .models import Book, Library


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


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    """Настройки админки для книг."""

    list_display = (
        'id',
        'title',
        'author',
        'inventory_number',
        'library',
    )
    list_display_links = (
        'id',
        'title',
    )
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

    list_select_related = ('library',)

    fieldsets = (
        (
            ConstantsAdmin.FIELDSET_BASE,
            {'fields': ('title', 'author', 'inventory_number')},
        ),
        (
            ConstantsAdmin.FIELDSET_STATUS,
            {
                'fields': ('library',),
            },
        ),
    )

    autocomplete_fields = ('library',)
    save_as = True
    save_on_top = True
