from typing import Any, Dict, List, Tuple

from django.db.models import Count, Prefetch, Q

from core.models import Book, Library


class FundOptimizationService:
    """Сервис для расчета и перераспределения книжного фонда сети."""

    @staticmethod
    def generate_report(query_filter: str = '') -> Dict[str, Any]:
        """Главный оркестратор: генерация полного отчета по оптимизации фонда.

        query_filter - Строка для поиска конкретной библиотеки по ее названию.
        all_libs - Полный список объектов библиотек с предзагруженными данными.
        total_cap - Суммарная вместимость всех филиалов сети.
        total_books - Общее количество физических книг во всей сети.
        avg_rate - Идеальный коэффициент загрузки (число от 0 до 1).
        avg_percent - Идеальный коэффициент в процентах (например, 39.5%).
        temp_results - Список с расчетами квот по методу Гамильтона.
        full_analysis - Итоговый массив данных со статистикой по каждой
            библиотеке.
        donor_pool - Список конкретных книг, которые доноры готовы отдать.

        Связь с интерфейсом (HTML):
        Формирует итоговый словарь контекста (context) для рендеринга
            всей страницы.
        Всё, что видит пользователь на экране (от верхних плашек статистики до
        списков книг в карточках), упаковывается и отдается именно здесь.

        Возвращает итоговый словарь с результатами анализа и общими
            показателями для шаблона.
        """
        # ШАГ 0: Собираем исходные данные из БД (Один запрос на всё)
        all_libs, total_cap, total_books, avg_rate, avg_percent = (
            FundOptimizationService._get_base_data()
        )

        # ШАГ 1: Рассчитываем целевые квоты по методу Гамильтона
        temp_results = FundOptimizationService._calculate_hamilton_targets(
            all_libs, total_books, avg_rate
        )

        # ШАГ 2: Формируем базовый список анализа (отклонений и процентов)
        full_analysis = FundOptimizationService._create_analysis_entries(
            temp_results, avg_percent
        )

        # ШАГ 3: Собираем конкретные книги у библиотек-доноров в общий "котел"
        donor_pool = FundOptimizationService._collect_books_from_donors(
            full_analysis
        )

        # ШАГ 4: Распределяем собранные книги между библиотеками-реципиентами
        FundOptimizationService._match_books_to_receivers(
            full_analysis, donor_pool
        )

        # ШАГ 5: Фильтруем результат по поиску и сортируем по алфавиту
        results = FundOptimizationService._finalize_results(
            full_analysis, query_filter
        )

        return {
            'total_books': total_books,
            'total_capacity': total_cap,
            'avg_rate_percent': avg_percent,
            'results': results,
        }

    @staticmethod
    def _get_base_data() -> Tuple[List[Library], int, int, float, float]:
        """Сбор базовых данных из БД и расчет глобальных показателей сети.

        stats - Правила подсчета текущих книг и книг на руках (annotate).
        prefetches - Правила подгрузки книг для исключения N+1.
        all_libraries - Результат единственного запроса к БД.

        Связь с интерфейсом (HTML):
        Готовит данные для  верхнего белого блока "Оптимизация книжного фонда":
        - total_books -> выводит цифру для текста "Всего книг в фонде: X"
        - total_capacity -> выводит цифру "Общая вместимость сети: X"
        - avg_percent -> выводит крупную цифру "X%" (Средняя загрузка сети)

        Возвращает: Кортеж с объектами библиотек и глобальными цифрами сети.
        """
        stats = {
            'current_books': Count('books', distinct=True),
            'on_hand_count': Count(
                'books', filter=Q(books__reader__isnull=False), distinct=True
            ),
        }

        prefetches = [
            Prefetch(
                'books',
                queryset=Book.objects.filter(reader__isnull=True).order_by(
                    'id'
                ),
                to_attr='available_books',
            ),
            Prefetch('books', to_attr='all_books_list'),
        ]

        all_libraries = list(
            Library.objects.annotate(**stats).prefetch_related(*prefetches)
        )

        total_capacity = sum(lib.capacity for lib in all_libraries)
        total_books = sum(lib.current_books for lib in all_libraries)

        avg_rate = total_books / total_capacity if total_capacity > 0 else 0
        avg_percent = round(avg_rate * 100, 1)

        return (
            all_libraries,
            total_capacity,
            total_books,
            avg_rate,
            avg_percent,
        )

    @staticmethod
    def _calculate_hamilton_targets(
        libraries: List[Library], total_books: int, avg_rate: float
    ) -> List[Dict[str, Any]]:
        """Расчет целевого количества книг по методу Гамильтона.

        assigned_total - Сколько целых книг мы уже распределили.
        temp_results - Список словарей, где хранятся целые части и остатки
            для каждой библиотеки.
        books_to_distribute - Количество "лишних" книг после округления,
            которые нужно раздать.

        Связь с интерфейсом (HTML):
        Рассчитывает математический идеал внутри карточки библиотеки:
        - target -> выводит цифру для текста "Целевое значение: X (...)"
        - current_books -> выводит цифру для текста "Количество книг: X (...)"
        - on_hand_total -> выводит цифру для текста "На руках: X (...)"

        Возвращает: Список словарей библиотек с ключом 'target'.
        """
        temp_results = []
        assigned_total = 0

        for lib in libraries:
            float_target = lib.capacity * avg_rate
            floor_target = int(float_target)
            assigned_total += floor_target

            temp_results.append({
                'library': lib,
                'current_books': lib.current_books,
                'target': floor_target,
                'remainder': float_target - floor_target,
                'capacity': lib.capacity,
                'on_hand_total': lib.on_hand_count,
            })

        books_to_distribute = total_books - assigned_total
        temp_results.sort(key=lambda x: x['remainder'], reverse=True)

        for i in range(int(books_to_distribute)):
            temp_results[i]['target'] += 1

        return temp_results

    @staticmethod
    def _create_analysis_entries(
        temp_results: List[Dict[str, Any]], avg_percent: float
    ) -> List[Dict[str, Any]]:
        """Расчет отклонений и создание базовых записей анализа.

        Дополняем данные temp_results:
        diff - Разница между текущим количеством книг и целевым значением.
        load_p - Текущий процент загрузки полок конкретной библиотеки.
        hand_p - Процент книг, выданных на руки в данной библиотеке.
        action - Вердикт для библиотеки: 'give' (донор),
            'take' (реципиент) или 'none'.

        Связь с интерфейсом (HTML):
        Управляет цветными бейджами и процентами в подзаголовке карточки:
        - action + diff -> Отрисовывают зеленую плашку "Нужно добавить: X шт."
                           или желтую плашку "Нужно забрать: X шт."
        - load_p -> Вставляет процент загрузки: "Количество книг: ... (X%)"
        - hand_p -> Вставляет процент выданных книг: "На руках: ... (X%)"
        Также создает пустые массивы 'candidates' и 'incoming_books', чтобы
        в HTML не падали ошибки при отрисовке пустых таблиц.

        Возвращает: Список словарей со статусами и рассчитанными процентами.
        """
        full_analysis = []

        for item in temp_results:
            diff = item['current_books'] - item['target']
            load_p = (
                int((item['current_books'] / item['capacity']) * 100)
                if item['capacity'] > 0
                else 0
            )
            hand_p = (
                int((item['on_hand_total'] / item['capacity']) * 100)
                if item['capacity'] > 0
                else 0
            )

            if diff > 0:
                action = 'give'
            elif diff < 0:
                action = 'take'
                diff = abs(diff)
            else:
                action = 'none'

            full_analysis.append({
                **item,
                'target_percent': avg_percent,
                'on_hand_percent': hand_p,
                'load': load_p,
                'action': action,
                'diff': diff,
                'candidates': [],
                'incoming_books': [],
            })

        return full_analysis

    @staticmethod
    def _collect_books_from_donors(
        full_analysis: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Поиск дубликатов и сбор конкретных книг у библиотек-доноров.

        donor_pool - Общий список книг на перераспределение.
        seen_keys - Набор (Название, Автор) для определения первого
            уникального экземпляра.
        protected - Список уникальных книг, которые мы стараемся не забирать.
        duplicates - Список лишних копий, которые забираются в первую очередь.
        candidates - Список книг на перераспределение, который перебором
            добавим в donor_pool

        Связь с интерфейсом (HTML):
        Наполняет данными нижнюю часть карточки с ЖЕЛТОЙ плашкой:
        - candidates -> Формирует строки для таблицы "ПЛАН ВЫВОЗА КНИГ".
            Каждый объект в списке — это строка с названием, автором и
            инвентарным номером книги, которую нужно снять с полки.

        Возвращает: Наполненный пул книг для перераспределения по сети.
        """
        donor_pool = []

        for entry in full_analysis:
            if entry['action'] == 'give':
                lib = entry['library']

                # Работаем только с теми книгами, что на полке
                available = lib.available_books

                seen_keys = set()
                protected, duplicates = [], []

                for b in available:
                    key = (b.title.lower(), b.author.lower())
                    if key not in seen_keys:
                        seen_keys.add(key)
                        protected.append(b)
                    else:
                        duplicates.append(b)

                # Cписок: сначала дубли, потом (если не хватило) уникальные
                candidates = (duplicates + protected)[: entry['diff']]
                entry['candidates'] = candidates

                for b in candidates:
                    donor_pool.append({'book': b, 'from_lib': lib})

        return donor_pool

    @staticmethod
    def _match_books_to_receivers(
        full_analysis: List[Dict[str, Any]], donor_pool: List[Dict[str, Any]]
    ) -> None:
        """Распределение собранных книг между нуждающимися библиотеками.

        receivers - Список библиотек, помеченных как 'take' (принимающие).
        exists_in_base - Проверка наличия такой же книги в основном фонде.
        exists_in_incoming - Проверка, не едет ли такая книга в этой партии.

        Связь с интерфейсом (HTML):
        Наполняет данными нижнюю часть карточки с ЗЕЛЕНОЙ плашкой:
        - incoming_books -> Формирует строки для таблицы "ОЖИДАЕМЫЕ ПОСТАВКИ".
            В HTML выводится название книги, её номер и желтая плашка
            "Отправитель" (откуда она приедет).
            Также дописывает адрес получателя в 'candidates' доноров,
            заполняя колонку "КУДА ОТПРАВИТЬ" в таблице вывоза.

        Ничего не возвращает, модифицирует списки 'incoming_books'
            внутри full_analysis.
        """
        receivers = [res for res in full_analysis if res['action'] == 'take']

        for item in donor_pool:
            book = item['book']

            best_receiver = None
            # Задаем "худшие" стартовые показатели для поиска лучшего кандидата
            best_copies = float('inf')  # Бесконечное число дубликатов
            best_hole = 0  # Нулевой дефицит

            # Перебираем всех реципиентов
            for rec in receivers:
                current_hole = rec['diff'] - len(rec['incoming_books'])

                # 1. Если библиотеке книги больше не нужны — пропускаем
                if current_hole <= 0:
                    continue

                # 2. Считаем, сколько таких книг у нее уже есть (в базе + едут)
                in_base = sum(
                    1
                    for b in rec['library'].all_books_list
                    if b.title.lower() == book.title.lower()
                    and b.author.lower() == book.author.lower()
                )
                in_path = sum(
                    1
                    for b in rec['incoming_books']
                    if b['book'].title.lower() == book.title.lower()
                    and b['book'].author.lower() == book.author.lower()
                )
                total_copies = in_base + in_path

                # 3. Сравниваем с текущим лидером (поиск лучшего)
                # ПРИОРИТЕТ А: Ищем того, у кого меньше всего копий этой книги
                if total_copies < best_copies:
                    best_copies = total_copies
                    best_hole = current_hole
                    best_receiver = rec

                # ПРИОРИТЕТ Б: Если копий поровну, отдаем -у кого больше "дыра"
                elif total_copies == best_copies:
                    if current_hole > best_hole:
                        best_copies = total_copies
                        best_hole = current_hole
                        best_receiver = rec

            # 4. Если нашли идеального кандидата — оформляем посылку
            if best_receiver:
                book.to_library_name = best_receiver['library'].name
                best_receiver['incoming_books'].append({
                    'book': book,
                    'from_lib': item['from_lib'],
                })

    @staticmethod
    def _finalize_results(
        full_analysis: List[Dict[str, Any]], query: str
    ) -> List[Dict[str, Any]]:
        """Финальная обработка: фильтрация по поиску и алфавитная сортировка.

        query - Поисковая строка от пользователя.
        full_analysis - Полный массив рассчитанных данных.

        Связь с интерфейсом (HTML):
        Связано с полем ввода "Поиск библиотеки..." и кнопкой "Найти".
        Если пользователь ввел текст, этот метод отсекает лишние карточки
        из итогового списка. Сортировка гарантирует, что карточки идут
        строго сверху вниз (Библиотека №1, №2, №3 и т.д.).

        Возвращает: Финальный список карточек библиотек для вывода в браузере.
        """
        if query:
            full_analysis = [
                res
                for res in full_analysis
                if query.lower() in res['library'].name.lower()
            ]

        full_analysis.sort(key=lambda x: x['library'].name)
        return full_analysis
