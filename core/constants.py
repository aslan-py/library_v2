class ConstansModels:
    """Константы для оформления моделей."""

    # Лимиты длины полей
    MAX_STRING_LENGTH = 255
    MAX_UNIQ_BOOK_ID = 20

    # Названия для verbose_name полей
    LIB_NAME = 'Название библиотеки'
    LIB_CAPACITY = 'Вместимость (книг)'
    BOOK_TITLE = 'Название книги'
    BOOK_AUTHOR = 'Автор'
    BOOK_INV_NUMBER = 'Инвентарный номер'

    # Названия моделей (Meta)
    LIB_VERBOSE_NAME = 'Библиотека'
    LIB_VERBOSE_NAME_PLURAL = 'Библиотеки'
    BOOK_VERBOSE_NAME = 'Книга'
    BOOK_VERBOSE_NAME_PLURAL = 'Книги'

    # Регулярные выражения (Regex)
    NAME_REGEX = r'^[^\d]*$'

    # Сообщения об ошибках
    ERR_BOOK_TITLE = 'Название книги не должно состоять из одних цифр.'
    ERR_BOOK_AUTHOR = 'Имя автора не должно содержать цифры.'

    ERR_CAPACITY = 'В филиале "{name}" нет свободных мест (максимум: {capacity}).'


class ConstantsAdmin:
    """Константы для оформления панели администратора."""

    EMPTY_VALUE = '-нет данных-'
    NO_BOOKS = '-нет книг-'
    BOOKS_COUNT_LABEL = 'Количество книг'
    BORROWED_BOOKS_LABEL = 'Список взятых книг'
    FIELDSET_BASE = 'Основная информация'
    FIELDSET_STATUS = 'Расположение и статус'
    LIST_PER_PAGE = 20


class ViewsConstants:
    """Константы для оформления вьюх."""

    MAIN_PAGINATOR = 6
    PAGINATOR = 15
