import json

from django.shortcuts import render
from imdb import Cinemagoer
import re
from movies_project.models import movies

def signIn(request):
    render('sign.html')
def home(request):
    new_posters = []
    top10_posters = []
    popular_posters = []

    # Отримуємо фільми
    movies_new = movies.objects.all().order_by('release_date')[:10]
    movies_top10 = movies.objects.all().order_by('-vote_average')[:10]
    movies_popular = movies.objects.all().order_by('-vote_count')[:10]

    # Ініціалізація IMDb API
    ia = Cinemagoer()

    # Отримання постерів
    posters_new = find_movie_id(ia, movies_new)
    posters_top10 = find_movie_id(ia, movies_top10)
    posters_popular = find_movie_id(ia, movies_popular)

    return render(request, 'index.html', {
        'new_posters': posters_new,
        'top10_posters': posters_top10,
        'popular_posters': posters_popular
    })
from django.core.cache import cache


def find_movie_id(ia, movies_array):
    posters_data = []
    for movie in movies_array:
        if not movie.home_page:
            print(f"⚠️ У фільма {movie.movie_name} немає home_page")
            continue  # Пропускаємо фільм без home_page

        match = re.search(r'tt(\d+)', movie.home_page)  # Захоплюємо тільки числа
        if not match:
            print(f"❌ IMDb ID не знайдено в home_page: {movie.home_page}")
            continue

        imdb_id = match.group(1)  # Отримуємо лише числову частину ID
        print(f"✅ Знайдено IMDb ID: {imdb_id}")

        # Перевіряємо кеш для постера
        poster_url = cache.get(imdb_id)
        if poster_url:
            print(f"🔄 Постер для {imdb_id} знайдено в кеші")
            posters_data.append({'poster_url': poster_url})
            continue

        # Отримуємо об'єкт фільму з БД
        mv = movies.objects.filter(movie_name=movie.movie_name).first()  # Отримуємо перший результат, а не .values()

        if mv and mv.poster_url:  # Перевіряємо, чи є постер у БД
            poster_url = mv.poster_url
        else:
            try:
                movie_data = ia.get_movie(imdb_id)  # Тепер передаємо тільки число
                print(f"📝 Отримані дані з IMDb: {movie_data}")  # Для дебагу
                poster_url = movie_data.get('full-size cover url')
                if poster_url:
                    print(f"🌟 Отримано постер: {poster_url}")
                    # Оновлюємо поле у БД
                    if mv:
                        mv.poster_url = poster_url
                        mv.save(update_fields=['poster_url'])
            except Exception as e:
                print(f"❌ Помилка при отриманні даних з IMDb для {imdb_id}: {e}")
                poster_url = None

        if poster_url:
            posters_data.append({'movie_name': movie.movie_name, 'poster_url': poster_url})

    return posters_data
def get_media_type(mv):

    for movie in mv:
        home_page = movie.home_page  # Витягувати home_page для кожного фільму/серіалу
        print(f"Обробляється фільм/серіал: {movie.movie_name}")  # Виводимо назву фільму для відстеження

        # Витягнути IMDb ID з home_page
        match = re.search(r'tt(\d+)', home_page)  # Шукаємо "tt" та номер
        if not match:
            print(f"Не вдалося знайти IMDb ID у {home_page}")
            continue  # Пропускаємо, якщо ID не знайдено

        imdb_id = match.group(1)
        print(f"Знайдено IMDb ID: {imdb_id}")

        try:
            # Отримуємо об'єкт фільму/серіалу за ID
            ia = Cinemagoer()  # Створюємо екземпляр для кожного фільму
            media = ia.get_movie(imdb_id)

            # Перевіряємо тип медіа
            if 'series' in media['kind']:
                print(f"Серіал: {movie.movie_name}")
                movie.media_type = 'serial'  # Можна зберігати тип у базу
            elif 'movie' in media['kind']:
                print(f"Фільм: {movie.movie_name}")
                movie.media_type = 'film'  # Можна зберігати тип у базу
            else:
                print(f"Невизначено: {movie.movie_name}")
                movie.media_type = 'unknown'

            # Зберігаємо зміни в базі даних
            movie.save()
            print(f"Тип медіа для {movie.movie_name} збережено у базу даних.")

        except Exception as e:
            print(f"Помилка при отриманні даних з IMDb для {imdb_id}: {e}")
            continue  # Якщо сталася помилка, пропускаємо цей запис

def genres_films(request, genre):
    print(genre)

    genre = genre.capitalize()
    mv = movies.objects.filter(genres__contains=genre).order_by('vote_average')
    films_posters = movies.objects.filter(genres__contains=genre).order_by('-release_date').filter(media_type='film')
    ia = Cinemagoer()
    posters_data = find_movie_id(ia,films_posters)

    for movie in mv:
        # Пропустити, якщо media_type вже заповнено
        if movie.media_type in ['serial', 'film', 'unknown']:
            print(f"⏭ Пропущено {movie.movie_name}, бо media_type вже є: {movie.media_type}")
            continue

        if not movie.home_page:
            print(f"⚠️ У фільма {movie.movie_name} немає home_page")
            continue  # Пропускаємо фільм без home_page

        match = re.search(r'tt(\d+)', movie.home_page)  # Захоплюємо тільки числа
        if not match:
            print(f"❌ IMDb ID не знайдено в home_page: {movie.home_page}")
            continue

        imdb_id = match.group(1)  # Отримуємо лише числову частину ID
        print(f"✅ Знайдено IMDb ID: {imdb_id}")
        try:
            ia = Cinemagoer()
            media = ia.get_movie(imdb_id)

            print(media)
            if 'series' in media['kind']:
                print(f"Серіал: {movie.movie_name}")
                movie.media_type = 'serial'
            elif 'movie' in media['kind']:
                print(f"Фільм: {movie.movie_name}")
                movie.media_type = 'film'
            else:
                print(f"Невизначено: {movie.movie_name}")
                movie.media_type = 'unknown'

            movie.save(update_fields=['media_type'])
            print(f"Тип медіа для {movie.movie_name} збережено у базу даних.")

        except Exception as e:
            print(f"Помилка при отриманні даних з IMDb для {imdb_id}: {e}")

    print(posters_data)  # For debugging (you can remove this in production)

    print(mv)

    return render(request, 'action.html', { 'posters_data': posters_data, "genre": genre })


