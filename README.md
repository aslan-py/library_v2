# Library CRM: Оптимизация книжного фонда 📚

Library CRM — это система управления дублями книг в сети библиотек

## 🌟 Основной функционал

- Просмотр дэшборда по всем библиотекам с количетсвом книг и вместимостью.
- Просмотр всего фонда книг.
- Умный поиск: Позволяет искать библиотеку. либо книгу по названию , автору.
- Создание книг и распределение их по библиотекам.
- Возможность зайти в админку.
- Просмотр аналитики с рекомендациями как поступить с дубликатами.
 отправляются в те филиалы, где такого произведения еще нет ни на полках, ни в ожидаемых поставках.

## 🧠 Детальное описание логики распределения (Как это работает) на примере вложенных фикстур.

- *Алгоритм состоит из 5 последовательных шагов:*
- Для примера возьмем движение книги "Мастер и Маргарита"

### ШАГ 1:Выгрузка с БД.
```bash
# Алгоритм забирает из БД 3 объекта Библиотек и 15 объектов книг.
list(Library.objects.annotate(current_books_count=Count('books', distinct=True)
).prefetch_related('books')
  ```
```bash
# Формирование стартового шаблона в который будетм собирать данные
lib.id: {
    'library': lib,    # Библиотека 
    'give': [],        # Список словарей для отдачи дублей
    'take': [],        # Список словарей для приема
    'capacity': lib.capacity,
    'current_books': lib.current_books_count,
    'free_space': lib.capacity - lib.current_books_count,  # Свободыне места
  }
```

### ШАГ 2:Группировка дубликтов книг по названию + автор
```bash
# На выходе получим  словарь словарей
{('Дюна', 'Герберт'): {Библ_1: 3 шт, Библ_2: 0 шт}}
```
### Получим данные
- Центральная библиотека: 3 шт. (свободно на полках: 4 места)
- Детский сектор: 1 шт. (свободно на полках: 0 мест)
- Филиал северный: 0 шт. (свободно на полках: 2 места)
- Всего в сети: 4 штуки

### ШАГ 3:Получение квот на библиотеку сколько книг "Мастер и Маргарита" должно быть в каждой.
```bash
# Используем метод _calculate_quotas
base_target = total_copies // num_libs
remainder = total_copies % num_libs

quotas = {lib.id: base_target for lib in libraries}

sorted_libs = sorted(
    libraries, key=lambda library: lib_counts.get(library.id, 0), reverse=True
)
for i in range(remainder):
    quotas[sorted_libs[i].id] += 1
На выходе будет словарь с id библиотеки и ковтами: {1: 2, 2: 3}
```
- Распределяем 4 копии по 3 филиалам. Базовая норма — 1, остаток — 1 книга.
- Сортируем библиотеки по количеству дублей: Центральная библиотека (у неё 3), Детский сектор (у него 1), Филиал северный (у него 0).
- Раздаем остаток лидерам по +1 штуке (квоту получит только первая в списке Центральная библиотека, так как остаток равен 1).
- Итог квоты: Центральная библиотека: 2 шт., Детский сектор: 1 шт., Филиал северный: 1 шт.

### ШАГ 4:Выявления доноров (кто может отдавать книги) и реципиентов - кому нужно закинуть книги.
```bash
# _find_givers_and_takers
diff = have - need

if diff > 0:
    givers.append({'lib': lib, 'amount': diff})
elif diff < 0:
    amount_needed = abs(diff)
    free_space = results_map[lib.id]['free_space']
    can_take = min(amount_needed, free_space)
    
    if can_take > 0:
        takers.append({'lib': lib, 'amount': can_take, 'free_space': free_space})
```
  - Центральная библиотека: Имеет 3 книиги "Мастер и Маргарита", по квоте надо 2. Вывод: Донор (надо отдать 1 шт.).

  - Детский сектор: Имеет 1, по квоте надо 1. Вывод: Баланс. Свою книгу "Мастер и Маргарита" оставляет у себя.
  - Филиал северный: Имеет 0, по квоте надо 1. Проверяем полки: вместимость 6, занято 4. Свободно 2 места. Функция min(1 дефицит, 2 места) = 1. Вывод: Реципиент (готова принять 1 шт.).

  ### ШАГ 5:Собиаем данные в наш общий шаблон.
  ```bash
  # _execute_transfers
  transfer_amount = min(current_donor['amount'], current_receiver['amount'])
  results_map[current_donor['lib'].id]['give'].append({ ... })
  results_map[current_receiver['lib'].id]['take'].append({ ... })
  results_map[current_receiver['lib'].id]['free_space'] -= transfer_amount
  ```
  - Пара найдена (Центральная отдает, Северный принимает). Алгоритм пишет накладную: Перевезти книгу «Мастер и Маргарита» в количестве 1 шт. из Центральной библиотеки в Филиал северный.
  - Свободное место на полках Филиала северного уменьшается с 2 до 1 (чтобы алгоритм знал актуальную вместимость для следующей книги).

**🛠 Технологии**

- Python 3.12.7

- Django 6 — основной Web-фреймворк

- SQLite — базы данных

- HTML / CSS / Tailwind CSS — рендеринг интерфейса (Templates)

- uv — современный менеджер пакетов (Rust)

# 🚀 Быстрый старт

### Клонируйте репозиторий:

```bash
git clone git@github.com:aslan-py/library-project.git
cd library-project
```

### Вариант А: Использование uv (Рекомендуется, очень быстро)

**Установка**  
```bash
# Для Windows (PowerShell):
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# Для Linux/macOS:
curl -LsSf https://astral.sh/uv/install.sh | sh

# Проверка установки и версии, если есть версия то все - ok
uv --version

# Установка зависимостей
uv sync --no-dev

# Запуск проекта
uv run python manage.py runserver

# Остальные команды Django 
uv run <команда Django>
```

### Вариант Б: Использование стандартного pip

```bash
python -m venv venv
source venv/bin/activate   # Для Linux/macOS
pip install -r requirements.txt
```

### Примените миграции базы данных:

```bash
python manage.py migrate
```

### Загрузите тестовые данные (Фикстуры) для проверки работы алгоритма:

**Эта команда создаст 4 библиотеки, читателей и распределит книги (включая дубликаты)** 
``` bash
python manage.py loaddata complex_test.json
```

**Запуск сервера разработки:**

```
python manage.py runserver
```

Панель управления доступна по адресу: http://127.0.0.1:8000/

📂 Структура логики (App Analytics)
```bash

|-- analytics
|   |-- apps.py         
|   |-- migrations
|   |-- servise.py      # Главная логика распреда книг
|   |-- templates       # Шаблоны страницы распределения
|   |-- urls.py         # Пути для старницы аналитики    
|   |-- views.py        # Функции
|-- config              
|   |-- asgi.py
|   |-- settings.py     # Настрйоки проекта Django
|   |-- urls.py
|   |-- wsgi.py
|-- core
|   |-- admin.py
|   |-- apps.py
|   |-- constants.py
|   |-- fixtures         # Фикстуры для теста
|   |-- models.py        # Модели проекта
|   |-- templates        # Шаблоны для книг и читателей
|   |-- urls.py
|   |-- validators.py
|   |-- views.py
|-- homepage
|   |-- apps.py
|   |-- migrations
|   |-- mixins.py
|   |-- templates
|   |-- urls.py
|   |-- views.py
|-- manage.py
|-- pyproject.toml       # Настрйоки для зависимостей и линтера Ruff
|-- requirements.txt
|-- static               # Фавикон
|   |-- fav.png
|-- templates            # Базовые шаблоны
|   |-- base.html
|   |-- includes
|-- uv.lock              # Настройки uv
|-- .gitignore
|--.python-version
```

# 👤 Автор

* **Разработка** — [@Aslan_Ligus](https://t.me/Aslan_Ligus)