import os
import re
import django
import requests
from imdb import Cinemagoer
from imdb._exceptions import IMDbParserError
from django.db.models import Q
from django.utils.dateparse import parse_date
from datetime import datetime

# Налаштування Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'movies_project.settings')
django.setup()

from movies_project.models import MovieInfo, MovieFinancials, MovieCast, movie_trailer

# Константи
API_KEY = 'c9505d842969fd7f1552dc8f26690809'  # Замінити на свій TMDb API ключ
BASE_URL = 'https://api.themoviedb.org/3'
HEADERS = {'accept': 'application/json'}
start_date = '2022-01-01'
current_date = datetime.now().strftime('%Y-%m-%d')

# Функції


def fetch_content(content_type, pages, start_page):
    for page in range(start_page, start_page + pages):
        url = (
            f'{BASE_URL}/discover/{content_type}?api_key={API_KEY}&language=en-US&sort_by=popularity.desc'
            f'&page={page}&first_air_date.gte={start_date}&first_air_date.lte={current_date}'
            f'&with_origin_country=KR'
        )

        response = requests.get(url)
        if response.status_code != 200:
            print(f"Помилка при отриманні {content_type} сторінка {page}: {response.status_code}")
            continue

        data = response.json()
        results = data.get('results', [])

        for item in results:
            save_movie_or_tv(item, content_type)

def save_movie_or_tv(item, content_type):
    movie_id = item.get('id')
    details = fetch_details(movie_id, content_type)
    if not details:
        return

    title = details.get('title') if content_type == 'movie' else details.get('name')

    # Перевіряємо, чи такий фільм або серіал уже є в БД
    if MovieInfo.objects.filter(movie_name=title).exists():
        print(f"Пропущено {content_type}: {title} (вже існує)")
        return

    overview = details.get('overview', '')
    release_date = details.get('release_date') if content_type == 'movie' else details.get('first_air_date')
    original_language = details.get('original_language', '')
    genres = details.get('genres', [])
    genre_names = ', '.join([genre['name'] for genre in genres])
    poster_path = details.get('poster_path')
    homepage = details.get('homepage', '')
    production_companies = details.get('production_companies', [])
    production_company = production_companies[0]['name'] if production_companies else None
    vote_average_tmdb = details.get('vote_average', 0)
    vote_count_tmdb = details.get('vote_count', 0)
    tagline = details.get('tagline', '')
    episode_runtime = details.get('episode_run_time', [])
    runtime = details.get('runtime', 0) if content_type == 'movie' else (episode_runtime[0] if episode_runtime else 0)
    countries = details.get('production_countries', [])
    release_country = countries[0]['name'] if countries else 'Unknown'

    if not release_date:
        release_date = datetime.date.today().isoformat()

    # Пошук додаткової інформації через IMDb
    ia = Cinemagoer()
    imdb_vote_count = None
    imdb_vote_average = None
    imdb_trailer_url = None

    try:
        search_results = ia.search_movie(title)
        if search_results:
            first_result = search_results[0]
            imdb_movie = ia.get_movie(first_result.movieID)

            imdb_vote_count = imdb_movie.data.get('votes')
            imdb_vote_average = imdb_movie.data.get('rating')

            trailers = imdb_movie.get('trailers')
            if trailers:
                imdb_trailer_url = trailers[0]
    except Exception as e:
        print(f"Помилка IMDb при обробці фільму {title}: {e}")

    movie_info = MovieInfo.objects.create(
        movie_name=title,
        storyline=overview,
        overview=overview,
        release_date=release_date,
        release_country=release_country,
        run_time_minutes=runtime or 0,
        poster_url=f'https://image.tmdb.org/t/p/original{poster_path}' if poster_path else '',
        genre=genre_names,
        original_language=original_language,
        media_type='film' if content_type == 'movie' else 'serial',
        home_page=homepage,
        production_company=production_company,
    )

    MovieFinancials.objects.create(
        movie=movie_info,
        budget_usd=str(details.get('budget', 0)),
        revenue_usd=str(details.get('revenue', 0)),
        vote_average=imdb_vote_average if imdb_vote_average is not None else vote_average_tmdb,
        vote_count=str(imdb_vote_count) if imdb_vote_count is not None else str(vote_count_tmdb),
        tagline=tagline,
    )
    print(f"Додано {content_type}: {title}")

    # Зберігаємо каст
    cast_list = fetch_cast(movie_id, content_type)
    if cast_list:
        MovieCast.objects.create(movie=movie_info, cast=', '.join(cast_list))

    # Зберігаємо трейлер
    trailer_url = fetch_trailer(movie_id, content_type)
    if trailer_url:
        movie_trailer.objects.create(movie=movie_info, film_id=movie_id, trailer_url=trailer_url)
    elif imdb_trailer_url:
        movie_trailer.objects.create(movie=movie_info, film_id=movie_id, trailer_url=imdb_trailer_url)

def fetch_details(movie_id, content_type):
    url = f'{BASE_URL}/{content_type}/{movie_id}?api_key={API_KEY}&language=en-US'
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Не вдалось завантажити деталі для ID {movie_id}")
        return None

def fetch_cast(movie_id, content_type):
    url = f'{BASE_URL}/{content_type}/{movie_id}/credits?api_key={API_KEY}&language=en-US'
    response = requests.get(url)
    if response.status_code == 200:
        credits = response.json()
        cast_list = [actor['name'] for actor in credits.get('cast', [])][:10]  # Перші 10 акторів
        return cast_list
    else:
        print(f"Не вдалось завантажити каст для ID {movie_id}")
        return []

def fetch_trailer(movie_id, content_type):
    url = f'{BASE_URL}/{content_type}/{movie_id}/videos?api_key={API_KEY}&language=uk-UA'
    response = requests.get(url)
    if response.status_code == 200:
        videos = response.json().get('results', [])
        for video in videos:
            if video['type'] == 'Trailer' and video['site'] == 'YouTube':
                return f"https://www.youtube.com/watch?v={video['key']}"
    else:
        print(f"Не вдалось завантажити трейлер для ID {movie_id}")
    return None

def fetch_imdb_data(imdb_id):
    ia = Cinemagoer()

    if not imdb_id:
        return {}

    numeric_id = imdb_id.replace('tt', '')

    try:
        movie = ia.get_movie(numeric_id)
        result = {}
        if movie:
            if 'rating' in movie:
                result['rating'] = movie['rating']
            if 'votes' in movie:
                result['votes'] = movie['votes']
            if 'trailers' in movie and movie['trailers']:
                result['trailer'] = movie['trailers'][0]
        return result
    except IMDbParserError as e:
        print(f"Помилка IMDb для ID {imdb_id}: {e}")
        return {}

# Виклик основної функції
# fetch_content('movie', pages=5, start_page=1)
fetch_content('tv', pages=10, start_page=1)