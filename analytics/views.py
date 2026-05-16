from django.views.generic import TemplateView

from homepage.mixins import SearchMixin

from .servise import FundOptimizationService


class FundOptimizationView(SearchMixin, TemplateView):
    """Представление для анализа и оптимизации распределения книг."""

    template_name = 'analytics/optimization.html'

    def get_context_data(self, **kwargs):
        """Переопределяем контекст."""
        context = super().get_context_data(**kwargs)

        query = self.get_search_query()

        report_data = FundOptimizationService.generate_report(
            query_filter=query
        )

        context.update(report_data)

        return context
