import json
import requests
from django.contrib import auth
from django.contrib.auth import authenticate
from django.db.models import Max, Avg, Subquery, OuterRef, Count
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from imdb import Cinemagoer
import re
from imdb.Movie import Movie
from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, DjangoModelPermissionsOrAnonReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView

from movies_project.forms import RegistrationForm, LoginForm, ReviewForm
from movies_project.models import MovieInfo, MovieFinancials, movie_trailer, MovieCast, Watchlist, Review
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
            return redirect('/login')

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
    # movies_top10 = MovieInfo.objects.all().order_by('-financials__vote_average')[:10]
    # movies_popular = MovieInfo.objects.all().order_by('-financials__vote_count')[:10]

    movies_top10 = MovieInfo.objects.annotate(
        highest_rating=Max('financials__vote_average')
    ).order_by('-highest_rating').filter(release_date__gte='2023-01-01')[:10]
    #
    # top_rating_subquery = MovieFinancials.objects.filter(
    #     movie=OuterRef('pk')
    # ).order_by('-vote_average').values('vote_average')[:1]
    #
    # movies_top10 = MovieInfo.objects.annotate(
    #     highest_rating=Subquery(top_rating_subquery)
    # ).order_by('-highest_rating')[:10]
    #
    # for movie in movies_top10:
    #     print(movie.movie_name, movie.id, movie.highest_rating)

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
        # if not movie.home_page:
        #     continue
        #
        # match = re.search(r'tt(\d+)', movie.home_page)
        # if not match:
        #     continue
        #
        # imdb_id = match.group(1)

        poster_url = movie.poster_url
        if poster_url:
            posters_data.append({'movie_name': movie.movie_name, 'poster_url': poster_url, 'id': movie.id})
            continue

        mv = MovieInfo.objects.filter(movie_name=movie.movie_name).first()

        if mv and mv.poster_url:
            poster_url = mv.poster_url

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
    if genre == 'kdrama':
        all_movies = MovieInfo.objects.filter(media_type__icontains='serial', original_language='ko').order_by('financials__vote_average')
    else:
        sr = MovieInfo.objects.filter(media_type__contains='serial')
        all_movies = sr.filter(genre__icontains=genre).order_by('-release_date')

    get_media_type(all_movies)
    films_posters = all_movies.filter(media_type='serial').order_by('-release_date')
    ia = Cinemagoer()
    posters_data = find_movie_id(ia, films_posters)
    return render(request, "action.html", {
        'posters_data': posters_data,
        'genre': genre
    })


class Film(View):
    def get(self, request, filmId):
        # Отримуємо фільм
        movie = MovieInfo.objects.filter(id=filmId).first()
        cast = MovieCast.objects.filter(movie=movie)  # Пошук за movie, а не id
        cast_list = [cast_entry.cast for cast_entry in cast]  # Отримуємо всі акторські дані
        cast_string = ', '.join(cast_list)  # Об'єднуємо їх у рядок через кому
        rating_obj = MovieFinancials.objects.get(movie=movie)
        rating_10 = round(rating_obj.vote_average, 1)
        rating =rating_10/2
        # Create a range for 5 stars
        stars = []
        for i in range(1, 6):  # Loop over 5 stars
            if i <= rating:
                stars.append('full')  # Full star
            elif i - 0.5 < rating:
                stars.append('half')  # Half star
            else:
                stars.append('empty')  #
        # Отримуємо трейлер
        trailer = None
        if trailer_obj := movie_trailer.objects.filter(movie=movie).first():
            trailer_url = trailer_obj.trailer_url
            if trailer_url:
                trailer = trailer_url.split('v=')[1] if 'v=' in trailer_url else None

        # Отримуємо відгуки
        reviews = movie.reviews.all()  # Відгуки для цього фільму

        return render(request, 'film.html', {
            'movie': movie,
            'trailer': trailer,
            'cast': cast_string,
            'reviews': reviews,
            'rating': rating,
            'stars': stars
        })
    def post(self, request, filmId):
        # Отримуємо фільм за filmId
        movie = MovieInfo.objects.get(id=filmId)
        reviews = movie.reviews.all()  # Отримуємо всі відгуки для цього фільму

        if request.user.is_authenticated:  # Перевірка, чи користувач залогінений
            form = ReviewForm(request.POST)
            if form.is_valid():
                review = form.save(commit=False)
                review.movie = movie
                review.user = request.user
                review.save()
                return redirect('movie_detail', filmId=movie.id)  # Переходимо на сторінку фільму
        else:
            return redirect('login')

        return render(request, 'film.html', {
            'movie': movie,
            'review_form': form,
            'reviews': reviews
        })

class DeleteReviewView(View):
    def post(self, request, review_id):
        review = get_object_or_404(Review, id=review_id)

        # Перевірка, чи це відгук цього ж користувача
        if request.user == review.user:
            review.delete()

        return redirect('movie_detail', filmId=review.movie.id)

class FilmListView(APIView):
    # Додаємо права доступу
    permission_classes = [DjangoModelPermissionsOrAnonReadOnly]

    # Отримуємо queryset
    def get_queryset(self):
        return MovieInfo.objects.all()

    # Обробка GET запиту
    def get(self, request):
        movies = self.get_queryset()  # Отримуємо список фільмів
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

