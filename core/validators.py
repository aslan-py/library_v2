from django.core.exceptions import ValidationError

from core.constants import ConstansModels


def capacity_validate(library, book_instance=None):
    """Проверка вместимости библиотеки.

    Нет ошибки при редактировании книги , которая уже есть в бибилиотеке.
    """
    if not library:
        return

    current_count = library.books.count()

    if book_instance and book_instance.library_id == library.id:
        current_count -= 1

    if current_count >= library.capacity:
        raise ValidationError(
            ConstansModels.ERR_CAPACITY.format(
                name=library.name, capacity=library.capacity
            )
        )
