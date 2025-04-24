import re
import requests
import os
import django
from imdb import Cinemagoer
from django.db.models import Q

# Налаштування Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'movies_project.settings')
django.setup()

from movies_project.models import MovieInfo

# Ініціалізація IMDb
ia = Cinemagoer()

# Фільтруємо фільми з порожнім storyline
empty_storyline_movies = MovieInfo.objects.filter(Q(storyline__isnull=True) | Q(storyline=""))

# Проходимо по кожному фільму з порожнім storyline
for movie in empty_storyline_movies:
    if movie.home_page:  # Перевіряємо, чи є home_page з IMDb ID
        match = re.search(r"imdb\.com/title/(\w+)", movie.home_page)
        if match:
            imdb_id = match.group(1)  # Отримуємо IMDb ID з URL
            print(f"IMDb ID фільму: {imdb_id}")

            # Отримуємо інформацію про фільм через IMDbPY
            try:
                imdb_movie = ia.get_movie(imdb_id[2:])  # Отримуємо фільм (відрізаємо "tt")

                # Отримуємо розгорнутий сюжет (повний сюжет)
                full_plot = imdb_movie.get('full_plot', '')
                if not full_plot:  # Якщо повний сюжет відсутній, використовуємо plot
                    full_plot = imdb_movie.get('plot', [''])[0]

                # Порівняння старого і нового сюжету
                if full_plot and movie.storyline != full_plot:
                    movie.storyline = full_plot
                    movie.save()
                    print(f"Updated storyline for {movie.movie_name}")
                else:
                    print(f"Storyline for {movie.movie_name} is already up to date or empty.")

            except Exception as e:
                print(f"Не вдалося отримати дані з IMDb для {movie.movie_name}: {e}")
        else:
            print(f"Не вдалося знайти IMDb ID у URL: {movie.home_page}")
    else:
        print(f"Відсутній home_page для фільму: {movie.movie_name}")
