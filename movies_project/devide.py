import re
from imdb import Cinemagoer
from movies_project.models import movies

def get_media_type():
    ia = Cinemagoer()  # Створюємо екземпляр Cinemagoer для доступу до IMDb
    mv = movies.objects.all()  # Отримуємо всі фільми і серіали з бази

    for movie in mv:
        home_page = movie.home_page  # Витягувати home_page для кожного фільму/серіалу

        # Витягнути IMDb ID з home_page
        match = re.search(r'tt(\d+)', home_page)  # Шукаємо "tt" та номер
        if not match:
            print(f"Не вдалося знайти IMDb ID у {home_page}")
            continue  # Пропускаємо, якщо ID не знайдено

        imdb_id = match.group(1)

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

        except Exception as e:
            print(f"Помилка при отриманні даних з IMDb для {imdb_id}: {e}")
            continue  # Якщо сталася помилка, пропускаємо цей запис

# Викликаємо функцію для обробки всіх фільмів/серіалів
get_media_type()
