from django.views.generic import TemplateView

from .servise import FundOptimizationService


class FundOptimizationView(TemplateView):
    """Представление для анализа и оптимизации распределения книг."""

    template_name = 'analytics/optimization.html'

    def get_context_data(self, **kwargs):
        """Переопределяем контекст."""
        context = super().get_context_data(**kwargs)

        # Получаем параметр поиска
        query = self.request.GET.get('q', '')

        # Запускаем всю бизнес-логику
        report_data = FundOptimizationService.generate_report(
            query_filter=query
        )

        # Сливаем данные из сервиса с нашим контекстом для шаблона
        context.update(report_data)

        # Добавляем поисковой запрос, чтобы он не сбрасывался в input'е
        context['query'] = query

        return context
