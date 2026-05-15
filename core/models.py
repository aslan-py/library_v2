from django.core.validators import MinValueValidator, RegexValidator
from django.db import models
from django.urls import reverse

from core.constants import ConstansModels

from .validators import capacity_validate


class Library(models.Model):
    """Хранит информацию о библиотеке и её вместимости."""

    name = models.CharField(
        verbose_name=ConstansModels.LIB_NAME,
        max_length=ConstansModels.MAX_STRING_LENGTH,
    )
    capacity = models.PositiveIntegerField(
        verbose_name=ConstansModels.LIB_CAPACITY,
        validators=(MinValueValidator(1),),
    )

    class Meta:
        verbose_name = ConstansModels.LIB_VERBOSE_NAME
        verbose_name_plural = ConstansModels.LIB_VERBOSE_NAME_PLURAL

    def __str__(self):
        """Возвращает строковое представление библиотеки (её название)."""
        return self.name

    def save(self, *args, **kwargs):
        """Сохраняет объект, имя с большой буквы."""
        if self.name:
            self.name = self.name.capitalize()
        super().save(*args, **kwargs)


class Reader(models.Model):
    """Хранит данные читателя сети библиотек."""

    name = models.CharField(
        verbose_name=ConstansModels.READER_NAME,
        max_length=ConstansModels.MAX_STRING_LENGTH,
        validators=(
            RegexValidator(
                regex=ConstansModels.NAME_REGEX,
                message=ConstansModels.ERR_ONLY_LETTERS,
            ),
        ),
    )
    phone = models.CharField(
        verbose_name=ConstansModels.READER_PHONE,
        validators=(
            RegexValidator(
                regex=ConstansModels.PHONE_REGEX,
                message=ConstansModels.ERR_PHONE_FORMAT,
            ),
        ),
        max_length=ConstansModels.MAX_PHONE_LENGTH,
        unique=True,
    )

    class Meta:
        verbose_name = ConstansModels.READER_VERBOSE_NAME
        verbose_name_plural = ConstansModels.READER_VERBOSE_NAME_PLURAL

    def __str__(self):
        """Возвращает строковое представление читателя (его имя)."""
        return self.name

    def save(self, *args, **kwargs):
        """Сохраняет данные читателя.

        Оставляет только первое слово из имени и капитализирует его.
        """
        if self.name and self.name.strip():
            self.name = self.name.split()[0].capitalize()
        super().save(*args, **kwargs)


class Book(models.Model):
    """Хранит физический экземпляр книги и её местоположение."""

    title = models.CharField(
        verbose_name=ConstansModels.BOOK_TITLE,
        max_length=ConstansModels.MAX_STRING_LENGTH,
        validators=(
            RegexValidator(
                regex=ConstansModels.NAME_REGEX,
                message=ConstansModels.ERR_BOOK_TITLE,
            ),
        ),
    )
    author = models.CharField(
        verbose_name=ConstansModels.BOOK_AUTHOR,
        max_length=ConstansModels.MAX_STRING_LENGTH,
        validators=(
            RegexValidator(
                regex=ConstansModels.NAME_REGEX,
                message=ConstansModels.ERR_BOOK_AUTHOR,
            ),
        ),
    )
    inventory_number = models.CharField(
        verbose_name=ConstansModels.BOOK_INV_NUMBER,
        max_length=ConstansModels.MAX_UNIQ_BOOK_ID,
        unique=True,
    )

    library = models.ForeignKey(
        Library,
        on_delete=models.CASCADE,
        related_name='books',
        verbose_name=Library._meta.verbose_name,
    )
    reader = models.ForeignKey(
        Reader,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='borrowed_books',
        verbose_name=ConstansModels.BOOK_READER,
    )

    class Meta:
        verbose_name = ConstansModels.BOOK_VERBOSE_NAME
        verbose_name_plural = ConstansModels.BOOK_VERBOSE_NAME_PLURAL

    def __str__(self):
        """Возвращает название книги и её уникальный инвентарный номер."""
        return f'{self.title} ({self.inventory_number})'

    def get_absolute_url(self):
        return reverse(
            'homepage:library_detail', kwargs={'pk': self.library.pk}
        )

    def clean(self):
        """Выполняет валидацию вместимости библиотеки перед сохранением."""
        super().clean()
        capacity_validate(self.library, book_instance=self)

    def save(self, *args, **kwargs):
        """Сохраняет экземпляр книги.
    
        Запускает валидацию (full_clean) и капитализирует заголовок и автора.
        """
        self.full_clean()
        if self.title:
            self.title = self.title.capitalize()
        if self.author:
            self.author = self.author.capitalize()
        super().save(*args, **kwargs)
