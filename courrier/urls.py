from django.urls import path

from . import views

app_name = "courrier"

urlpatterns = [
    path("", views.courrier_list, name="list"),
    path("nouveau/", views.courrier_create, name="create"),
    path("<int:pk>/", views.courrier_detail, name="detail"),
]
