from django.shortcuts import render
from imdb import IMDb
from imdb import Cinemagoer

import re
from movies_project.models import movies
from django.core.cache import cache  # Імпортуємо кеш


def home(request):
    # ia =imdb.IMDb()
    new_posters = []
    top10_posters = []
    popular_posters = []
    movies_with_ratings = []

    # Отримуємо перші 10 фільмів за датою випуску
    movies_new = movies.objects.all().order_by('release_date')[:10]
    # Отримуємо перші 10 фільмів за середнім рейтингом
    movies_top10 = movies.objects.all().order_by('-vote_average')[:10]  # Сортування за спаданням!
    # Отримуємо популярні фільми
    movies_popular = movies.objects.all().order_by('-vote_count')[:10]
    # Пошук фільмів за жанром "Action"

    ia = Cinemagoer('http')
    movies_ia = ia.get_popular100_movies()
    # Сортуємо фільми за датою випуску у порядку спадання (найновіші фільми першими)
    sorted_movies_by_year = sorted(movies_ia, key=lambda movie: movie['year'], reverse=True)

    # Беремо перший фільм після сортування
    first_movie = sorted_movies_by_year[10]
    movie_id = first_movie.getID()
    movie_data = ia.get_movie(movie_id)
    poster_url_1 = movie_data.get('full-size cover url')
    print(poster_url_1)
    # Виводимо перший фільм з його деталями
    imdb_id = first_movie.getID()  # Отримуємо IMDb ID
    print(f"Title: {first_movie['title']}, Year: {first_movie['year']}, IMDb ID: {imdb_id}")
    # Створюємо список для фільмів з рейтингами
    # movies_with_ratings = []
    # for movie in movies_ia:
    #     movie_id = movie.get('imdbID')
    #     if movie_id:  # Перевіряємо, чи є imdbID
    #         movie_data = ia.get_movie(movie_id[2:])  # ID без 'tt' префікса
    #         rating = movie_data.get('rating')  # Отримуємо рейтинг
    #         if rating is not None:  # Перевіряємо, чи є рейтинг
    #             movies_with_ratings.append({
    #                 'title': movie_data['title'],
    #                 'rating': rating,
    #                 'poster': movie_data.get('cover url')
    #             })
    # print(movies_with_ratings)
    # # Сортуємо фільми за рейтингом
    # sorted_movies = sorted(movies_with_ratings, key=lambda x: x['rating'], reverse=True)
    #
    # # Отримуємо постер для фільму з найвищим рейтингом
    # if sorted_movies:
    #     top_movie = sorted_movies[0]
    #     print(f"Найкращий фільм: {top_movie['title']}")
    #     print(f"Рейтинг: {top_movie['rating']}")
    #     print(f"Постер: {top_movie['poster'] if top_movie['poster'] else 'Постер не знайдено'}")
    # else:
    #     print("Не знайдено фільмів з рейтингом.")


    # Для нових фільмів
    for movie in movies_new:
        imdb_id, poster_url = find_movie_id(movie, ia)
        if imdb_id and poster_url:  # Перевіряємо на наявність даних
            new_posters.append({'imdb_id': imdb_id, 'poster_url': poster_url})

    # Для топ-10 фільмів
    for movie in movies_top10:
        imdb_id, poster_url = find_movie_id(movie, ia)
        if imdb_id and poster_url:  # Перевіряємо на наявність даних
            top10_posters.append({'imdb_id': imdb_id, 'poster_url': poster_url})

    # Для популярних фільмів
    for movie in movies_popular:
        imdb_id, poster_url = find_movie_id(movie, ia)
        if imdb_id and poster_url:  # Перевіряємо на наявність даних
            popular_posters.append({'imdb_id': imdb_id, 'poster_url': poster_url})

    return render(request, 'index.html',
                  {'new_posters': new_posters, 'top10_posters': top10_posters, 'popular_posters': popular_posters}, poster_url_1)


def find_movie_id(movie, ia):
    if not movie.home_page:  # Перевірка, чи є home_page
        print(f"⚠️ У фільма {movie} немає home_page")
        return None, None

    match = re.search(r'tt\d+', movie.home_page)
    if not match:
        print(f"❌ IMDb ID не знайдено в home_page: {movie.home_page}")
        return None, None

    imdb_id = match.group(0)
    print(f"✅ Знайдено IMDb ID: {imdb_id}")

    # Перевіряємо кеш для постера
    cache_key = f"poster_{imdb_id}"
    poster_url = cache.get(cache_key)

    if poster_url:
        print(f"🎉 Використано кешований постер для {imdb_id}")
        return imdb_id, poster_url

    # Якщо постера немає в кеші, запитуємо IMDb
    try:
        movie_id = ia.get_movie(imdb_id[2:])
        poster_url = movie_id.get('full-size cover url')
        print(f"🌟 Отримано постер: {poster_url}")

        if poster_url:
            cache.set(cache_key, poster_url, timeout=2592000)  # Кешуємо на 30 днів

    except Exception as e:
        print(f"❌ Помилка при отриманні даних з IMDb для {imdb_id}: {e}")
        poster_url = None

    return imdb_id, poster_url
