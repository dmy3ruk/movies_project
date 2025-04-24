import json
import requests
from django.contrib import auth
from django.contrib.auth import authenticate
from django.db.models import Max, Avg, Subquery, OuterRef, Count
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views import View
from imdb import Cinemagoer
import re
from imdb.Movie import Movie
from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from movies_project.forms import RegistrationForm, LoginForm
from movies_project.models import MovieInfo, MovieFinancials, movie_trailer, MovieCast, Watchlist
from django.core.cache import cache
from movies_project.serializers import WatchlistSerializer, MovieInfoSerializer


class SignUpView(View):
    def get(self, request):
        # Створюємо порожню форму для GET-запиту
        form = RegistrationForm()
        return render(request, 'sign.html', {'registerForm': form})

    def post(self, request):
        # Отримуємо дані з форми
        form = RegistrationForm(request.POST)

        if form.is_valid():
            # Створюємо нового користувача, але не зберігаємо ще в базі
            user = form.save(commit=False)
            user.is_active = True  # Користувач неактивний до підтвердження
            user.save()

            # Перенаправляємо на сторінку перевірки email
            return render(request, 'SignIn.html', {'email': request.POST.get('email')})

        # Якщо форма не дійсна, повертаємо її разом з помилками
        return render(request, 'sign.html', {'registerForm': form})


class SignInView(View):
    def get(self, request):
        form = LoginForm()
        return render(request, 'SignIn.html', {'loginForm': form})

    def post(self, request):
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(username=username, password=password)
            if user is not None and user.is_active:

                auth.login(request, user)
                print("User logged in")
                return redirect('/')
            else:
                print("Invalid login")

        return render(request, 'SignIn.html', {'loginForm': form})


def home(request):
    new_posters = []
    top10_posters = []
    popular_posters = []

    # Вибір останніх 10 фільмів за датою випуску
    movies_new = MovieInfo.objects.all().order_by('-release_date')[:10]
    movies_top10 = MovieInfo.objects.annotate(
        highest_rating=Max('financials__vote_average')
    ).order_by('-highest_rating')[:10]

    top_rating_subquery = MovieFinancials.objects.filter(
        movie=OuterRef('pk')
    ).order_by('-vote_average').values('vote_average')[:1]

    movies_top10 = MovieInfo.objects.annotate(
        highest_rating=Subquery(top_rating_subquery)
    ).order_by('-highest_rating')[:10]

    for movie in movies_top10:
        print(movie.movie_name, movie.id, movie.highest_rating)

    movies_popular = MovieInfo.objects.all().order_by('-financials__vote_count').distinct()[:10]

    ia = Cinemagoer()

    queryset = MovieInfo.objects.all().order_by('-financials__vote_average')[:10]
    print(str(queryset.query))

    posters_new = find_movie_id(ia, movies_new)
    posters_top10 = find_movie_id(ia, movies_top10)
    posters_popular = find_movie_id(ia, movies_popular)

    print(new_posters)  # Перевірка нових постерів
    print(top10_posters)  # Перевірка постерів топ-10
    print(popular_posters)  # Перевірка популярних постерів

    return render(request, 'index.html', {
        'new_posters': posters_new,
        'top10_posters': posters_top10,
        'popular_posters': posters_popular
    })


def find_movie_id(ia, movies_array):
    posters_data = []
    for movie in movies_array:
        if not movie.home_page:
            continue

        match = re.search(r'tt(\d+)', movie.home_page)
        if not match:
            continue

        imdb_id = match.group(1)

        poster_url = cache.get(imdb_id)
        if poster_url:
            posters_data.append({'poster_url': poster_url})
            continue

        mv = MovieInfo.objects.filter(movie_name=movie.movie_name).first()

        if mv and mv.poster_url:
            poster_url = mv.poster_url
        else:
            try:
                movie_data = ia.get_movie(imdb_id)
                poster_url = movie_data.get('full-size cover url')
                if poster_url and mv:
                    mv.poster_url = poster_url
                    mv.save(update_fields=['poster_url'])
            except Exception:
                poster_url = None

        if poster_url:
            posters_data.append({'movie_name': movie.movie_name, 'poster_url': poster_url, 'id': movie.id})

    return posters_data


def get_media_type(mv):
    ia = Cinemagoer()
    for movie in mv:
        if movie.media_type in ['serial', 'film', 'unknown']:
            continue
        if not movie.home_page:
            continue

        match = re.search(r'tt(\d+)', movie.home_page)
        if not match:
            continue

        imdb_id = match.group(1)

        try:
            media = ia.get_movie(imdb_id)
            if 'series' in media.get('kind', ''):
                movie.media_type = 'serial'
            elif 'movie' in media.get('kind', ''):
                movie.media_type = 'film'
            else:
                movie.media_type = 'unknown'

            movie.save(update_fields=['media_type'])
        except Exception:
            continue


def genres(genre, posters):
    genre = genre.capitalize()
    mv = MovieInfo.objects.filter(genre__contains=genre).order_by('vote_average')
    get_media_type(mv)
    ia = Cinemagoer()
    posters_data = find_movie_id(ia, posters)
    return posters_data


def films_poster(request, genre):
    genre = genre.capitalize()
    all_movies = MovieInfo.objects.filter(media_type__contains='film')
    films_posters = all_movies.filter(genre__contains=genre)
    ia = Cinemagoer()
    # sync_genres_with_tmdb(films_posters)
    posters_data = find_movie_id(ia, films_posters)
    print(posters_data)
    return render(request, "action.html", {
        'posters_data': posters_data,
        'genre': genre
    })


def serials_poster(request, genre):
    genre = genre.capitalize()
    all_movies = MovieInfo.objects.filter(media_type__contains='serial')
    get_media_type(all_movies)
    films_posters = all_movies.filter(media_type='serial').order_by('-release_date')
    ia = Cinemagoer()
    posters_data = find_movie_id(ia, films_posters)
    return render(request, "action.html", {
        'posters_data': posters_data,
        'genre': genre
    })


def film_page(request, filmId):
    movie = MovieInfo.objects.filter(id=filmId).first()
    cast = MovieCast.objects.filter(id=filmId)
    cast_list = [cast_entry.cast for cast_entry in cast]  # Отримуємо всі акторські дані
    cast_string = ', '.join(cast_list)  # Об'єднуємо їх у рядок через кому

    print(cast_string)
    if trailer := movie_trailer.objects.filter(movie=movie).first():
        trailer_url = trailer.trailer_url
        if trailer_url:
            trailer = trailer_url.split('v=')[1] if 'v=' in trailer_url else None
    return render(request, 'film.html', {'movie': movie, 'trailer': trailer, 'cast': cast_string})

@api_view(['GET'])
def films_api(request):
    movies = MovieInfo.objects.all()
    serializer = MovieInfoSerializer(movies, many=True, context={'request': request})
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def watchlist_api(request):
    items = Watchlist.objects.filter(user=request.user)
    serializer = WatchlistSerializer(items, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_to_watchlist(request, movie_id):
    user = request.user
    try:
        movie = MovieInfo.objects.get(id=movie_id)
    except MovieInfo.DoesNotExist:
        return Response({'error': 'Movie not found'}, status=404)

    obj, created = Watchlist.objects.get_or_create(user=user, movie=movie)
    if not created:
        return Response({'message': 'Movie already in watchlist'}, status=400)
    return Response({'message': 'Movie added to watchlist'})

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def remove_from_watchlist(request, movie_id):
    user = request.user
    try:
        movie = MovieInfo.objects.get(id=movie_id)
    except MovieInfo.DoesNotExist:
        return Response({'error': 'Movie not found'}, status=404)

    deleted, _ = Watchlist.objects.filter(user=user, movie=movie).delete()
    if deleted:
        return Response({'message': 'Movie removed from watchlist'})
    return Response({'error': 'Movie not in watchlist'}, status=400)
def watchlist(request):
    return render(request, 'watchlist.html')

