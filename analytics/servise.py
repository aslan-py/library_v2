from collections import defaultdict
from typing import Any, Dict, List

from django.db.models import Count

from core.models import Library


class FundOptimizationService:
    """Сервис выравнивания количества дубликатов по филиалам."""

    @staticmethod
    def generate_report(query_filter: str = '') -> Dict[str, Any]:
        """Главный оркестратор оптимизации."""

        libraries = FundOptimizationService._get_base_data()
        if not libraries:
            return {'results': []}

        # Шаг 1: Получаем "стопки" книг дублей.
        book_groups = FundOptimizationService._group_books(libraries)

        # Шаг 2: Создаем пустой шаблон отчета.
        results_map = FundOptimizationService._initialize_results_map(
            libraries
        )

        # Шаг 3: Цикл перебора каждой книги.
        for (title, author), lib_counts in book_groups.items():
            # А: Рассчитываем идеальную квоту
            quotas = FundOptimizationService._calculate_quotas(
                lib_counts, libraries
            )

            # Б: Находим доноров (с излишками) и реципиентов.
            givers, takers = FundOptimizationService._find_givers_and_takers(
                libraries, lib_counts, quotas, results_map
            )

            # В: Сопоставляем их друг с другом и записываем партии книг.
            FundOptimizationService._execute_transfers(
                title, author, givers, takers, results_map
            )
        for data in results_map.values():
            data['total_give_books'] = sum(
                item['amount'] for item in data['give']
            )
            data['total_take_books'] = sum(
                item['amount'] for item in data['take']
            )
        # Шаг 4: Фильтрация и сортировка.
        final_results = FundOptimizationService._finalize_results(
            results_map, query_filter
        )
        return {'results': final_results}

    @staticmethod
    def _get_base_data() -> List[Library]:
        """Сбор библиотек и подсчет занятого места."""
        return list(
            Library.objects.annotate(
                current_books_count=Count('books', distinct=True)
            ).prefetch_related('books')
        )

    @staticmethod
    def _initialize_results_map(
        libraries: List[Library],
    ) -> Dict[int, Dict[str, Any]]:
        """Создает структуру данных для хранения результатов.

        На выходе:
            - Словарь словарей, где ключом будет id библиотеки.
            - give и take теперь будут хранить не объекты книг, а словари с
              названием, автором и количеством (amount) в партии.
        """
        return {
            lib.id: {
                'library': lib,
                'give': [],
                'take': [],
                'capacity': lib.capacity,
                'current_books': lib.current_books_count,
                'free_space': lib.capacity - lib.current_books_count,
            }
            for lib in libraries
        }

    @staticmethod
    def _group_books(libraries: List[Library]) -> Dict[tuple, Dict[int, int]]:
        """Группирует книги и просто считает их количество по филиалам.

        book_groups:
            - Используем вложенный defaultdict. Он автоматически создает нули
                для новых библиотек.
            - Перебираем все книги, формируем ключ (title, author).
            - Просто плюсуем счетчик: "У такой-то книги в такой-то
                библиотеке +1 шт".
        duplicates_only:
            - Фильтруем словарь. sum(counts.values()) считает общее
                количество копий этой
              книги по всей сети. Оставляем только те, где в сумме > 1.

        На выходе: { ('Дюна', 'Герберт'): {Библ_1: 3 шт, Библ_2: 0 шт} }
        """
        book_groups = defaultdict(lambda: defaultdict(int))

        for lib in libraries:
            for book in lib.books.all():
                book_key = (book.title, book.author)
                book_groups[book_key][lib.id] += 1

        duplicates_only = {
            book_key: counts
            for book_key, counts in book_groups.items()
            if sum(counts.values()) > 1
        }
        return duplicates_only

    @staticmethod
    def _calculate_quotas(
        lib_counts: Dict[int, int], libraries: List[Library]
    ) -> Dict[int, int]:
        """Рассчитывает идеальную норму книг для каждого филиала.

        total_copies:
            - Сумма всех экземпляров конкретной книги в сети.
        base_target:
            - Базовая норма (общее количество делим на число филиалов).
        remainder:
            - Остаток от деления.
        quotas:
            - Словарь с id библиотек и их таргетами по дублям книг.
        sorted_libs:
            - Сортируем библиотеки у кого больше дублей, от самой богатой...
            - Раздаем остаток лидерам (+1 к квоте), итерации цикла зависят от
                количетсва остатков

        На выходе: словарь с квотами (ключ - id библиотеки,
            значение - сколько должно быть книг {1: 2, 2: 3}
        """
        total_copies = sum(lib_counts.values())
        num_libs = len(libraries)

        base_target = total_copies // num_libs
        remainder = total_copies % num_libs

        quotas = {lib.id: base_target for lib in libraries}

        sorted_libs = sorted(
            libraries,
            key=lambda library: lib_counts.get(library.id, 0),
            reverse=True,
        )
        for i in range(remainder):
            quotas[sorted_libs[i].id] += 1

        return quotas

    @staticmethod
    def _find_givers_and_takers(
        libraries: List[Library],
        lib_counts: Dict[int, int],
        quotas: Dict[int, int],
        results_map: Dict[int, Dict[str, Any]],
    ) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Определяет доноров (с излишками) и реципиентов (с местом на полках).

        Смотрит реальное распределение книг и идеальное - словарь quotas.

        givers:
            - Список словарей. Если факт (have) > квоты (need),
                библиотека становится донором.
            - Записываем её объект и СКОЛЬКО (amount) штук она должна отдать.
        takers:
            - Если факт < квоты, проверяем наличие свободного места.
            - Выбираем минимальное между "сколько нужно" и
                "сколько влезет на полку".
            - Если влезет хоть что-то, записываем в список принимающих
                (amount = сколько возьмет).
            - Сортируем список так, чтобы самые "пустые" библиотеки
                получили партии первыми.

        На выходе: два списка (доноры и получатели партий).
        givers: [{'lib': Объект_Библиотеки_1, 'amount': 1}]
        akers: [{'lib': Объект_Библиотеки_2, 'amount': 1, 'free_space': 5}]
        """
        givers = []
        takers = []

        for lib in libraries:
            have = lib_counts.get(lib.id, 0)
            need = quotas[lib.id]
            diff = have - need

            if diff > 0:
                givers.append({'lib': lib, 'amount': diff})
            elif diff < 0:
                amount_needed = abs(diff)
                free_space = results_map[lib.id]['free_space']
                can_take = min(amount_needed, free_space)

                if can_take > 0:
                    takers.append({
                        'lib': lib,
                        'amount': can_take,
                        'free_space': free_space,
                    })

        takers.sort(key=lambda x: x['free_space'], reverse=True)
        return givers, takers

    @staticmethod
    def _execute_transfers(
        title: str,
        author: str,
        givers: List[Dict],
        takers: List[Dict],
        results_map: Dict[int, Dict[str, Any]],
    ) -> None:
        """Сводит доноров и реципиентов, оформляя перевод партий.

        Логика работы:
            - Используем индексы-указатели (donor_index, receiver_index).
            - transfer_amount вычисляет партию: отдаем столько,
                сколько может дать
              донор ИЛИ сколько может взять реципиент (выбираем меньшее).
            - Записываем текстовые накладные в словари 'give' и 'take'
                с указанием amount.
            - Жестко вычитаем переданное количество из свободного места
                получателя.
            - Уменьшаем долги донора и потребности получателя.
            - Если донор всё отдал (amount == 0), переходим к
                следующему донору.
            - Если получатель всё взял, переходим к следующему получателю.

        На выходе: ничего. Напрямую мутирует results_map.
        """
        donor_index = 0
        receiver_index = 0

        # Пока не дошли до конца списка доноров И до конца списка получателей
        while donor_index < len(givers) and receiver_index < len(takers):
            current_donor = givers[donor_index]
            current_receiver = takers[receiver_index]

            transfer_amount = min(
                current_donor['amount'], current_receiver['amount']
            )

            results_map[current_donor['lib'].id]['give'].append({
                'title': title,
                'author': author,
                'amount': transfer_amount,
                'to_lib': current_receiver['lib'],
            })

            results_map[current_receiver['lib'].id]['take'].append({
                'title': title,
                'author': author,
                'amount': transfer_amount,
                'from_lib': current_donor['lib'],
            })

            results_map[current_receiver['lib'].id]['free_space'] -= (
                transfer_amount
            )

            current_donor['amount'] -= transfer_amount
            current_receiver['amount'] -= transfer_amount

            if current_donor['amount'] == 0:
                donor_index += 1

            if current_receiver['amount'] == 0:
                receiver_index += 1

    @staticmethod
    def _finalize_results(results_map: Dict, query: str) -> List[Dict]:
        """Отсеивает по поиску и сортирует итоговый список по алфавиту."""
        final_results = []
        for data in results_map.values():
            if query and query.lower() not in data['library'].name.lower():
                continue
            final_results.append(data)
        final_results.sort(key=lambda x: x['library'].name)
        return final_results
