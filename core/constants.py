class ConstansModels:
    """Константы для оформления моделей."""
    # Лимиты длины полей
    MAX_STRING_LENGTH = 255
    MAX_PHONE_LENGTH = 11  # Исправил опечатку LENGHT -> LENGTH
    MAX_UNIQ_BOOK_ID = 20

    # Названия для verbose_name полей
    LIB_NAME = 'Название библиотеки'
    LIB_CAPACITY = 'Вместимость (книг)'
    READER_NAME = 'Имя читателя'
    READER_PHONE = 'Номер телефона'
    BOOK_TITLE = 'Название книги'
    BOOK_AUTHOR = 'Автор'
    BOOK_INV_NUMBER = 'Инвентарный номер'
    BOOK_READER = 'Читатель (на руках)'

    # Названия моделей (Meta)
    LIB_VERBOSE_NAME = 'Библиотека'
    LIB_VERBOSE_NAME_PLURAL = 'Библиотеки'
    READER_VERBOSE_NAME = 'Читатель'
    READER_VERBOSE_NAME_PLURAL = 'Читатели'
    BOOK_VERBOSE_NAME = 'Книга'
    BOOK_VERBOSE_NAME_PLURAL = 'Книги'

    # Регулярные выражения (Regex)
    NAME_REGEX = r'^[^\d]*$'
    PHONE_REGEX = r'^7\d{10}$'

    # Сообщения об ошибках
    ERR_ONLY_LETTERS = 'Поле не должно содержать цифры.'
    ERR_PHONE_FORMAT = 'Ошибка, телефон начинается с 7 и состоит из 11 цифр'
    ERR_BOOK_TITLE = 'Название книги не должно состоять из одних цифр.'
    ERR_BOOK_AUTHOR = 'Имя автора не должно содержать цифры.'

    ERR_CAPACITY = (
        'В филиале "{name}" нет свободных мест (максимум: {capacity}).'
    )


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