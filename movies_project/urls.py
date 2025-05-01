"""
URL configuration for movies_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.db import router
from django.conf.urls.static import static  # ✅ правильно
from django.urls import path
from rest_framework.routers import DefaultRouter

from . import views, settings

from django.contrib import admin
from django.urls import path, include

from .views import SignUpView, SignInView, watchlist, add_to_watchlist, Film, DeleteReviewView, FilmListView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name=''),
    path('films/<str:genre>/', views.films_poster, name='genre'),
    path('serials/<str:genre>/', views.serials_poster, name='genre'),

    path('film/<int:filmId>', Film.as_view(), name='movie_detail'),
    path('delete-review/<int:review_id>/', DeleteReviewView.as_view(), name='delete_review'),
    path('signup/', SignUpView.as_view(), name='signup'),
    path('login/', SignInView.as_view(), name='signin'),
    path('api/films', FilmListView.as_view()),
    path('api/watchlist/', views.watchlist_api),
    path('api/add_to_watchlist/<int:movie_id>/', views.add_to_watchlist),
    path('api/remove_from_watchlist/<int:movie_id>/', views.remove_from_watchlist),
    path('watchlist', watchlist, name='watchlist'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
