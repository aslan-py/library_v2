from django.urls import path

from . import views

app_name = 'homepage'

urlpatterns = [
    path('', views.DashboardListView.as_view(), name='dashboard'),
    path(
        'library/<int:pk>/',
        views.LibraryListView.as_view(),
        name='library_detail',
    ),
    path('books/all/', views.TotalBookListView.as_view(), name='total_books'),
]
