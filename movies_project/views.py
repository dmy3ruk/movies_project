from django.shortcuts import render
from imdb import Cinemagoer
import re
from movies_project.models import movies

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

        poster_url = cache.get(imdb_id)
        if poster_url:
            print(f"🔄 Постер для {imdb_id} знайдено в кеші")
            posters_data.append({'poster_url': poster_url})
            continue

        # Отримуємо з БД лише потрібне поле
        mv = movies.objects.filter(movie_name=movie.movie_name).values("poster_url").first()

        if mv and mv.get("poster_url"):
            poster_url = mv["poster_url"]
        else:
            try:
                movie_data = ia.get_movie(imdb_id)  # Тепер передаємо тільки число
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
            posters_data.append({'poster_url': poster_url})

    return posters_data
