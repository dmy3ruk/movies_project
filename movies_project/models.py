from django.contrib.auth.models import User
from django.db import models


class MovieInfo(models.Model):
    movie_name = models.CharField(max_length=255)
    storyline = models.TextField()
    overview = models.TextField()
    release_date = models.DateField()
    release_country = models.CharField(max_length=255)
    run_time_minutes = models.IntegerField()
    poster_url = models.TextField()

    # Поля з MovieMetadata
    genre = models.TextField(blank=True, null=True)
    original_language = models.TextField(blank=True, null=True)
    media_type = models.TextField(default="none")
    home_page = models.TextField(blank=True, null=True)
    production_company = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = 'movie_info'


class MovieCast(models.Model):

    movie = models.ForeignKey(MovieInfo, on_delete=models.CASCADE, related_name='casts')  # Зв'язок з MovieInfo
    cast = models.TextField()  # Склад акторів у фільмі

    class Meta:
        db_table = 'movie_cast'

class MovieFinancials(models.Model):
    movie = models.ForeignKey(MovieInfo, on_delete=models.CASCADE, related_name='financials')
    budget_usd = models.CharField(max_length=255)  # Бюджет фільму як текст
    revenue_usd = models.CharField(max_length=255)  # Доходи фільму як текст
    vote_average = models.FloatField()  # Середня оцінка фільму
    vote_count = models.CharField(max_length=255)  # Кількість голосів
    tagline = models.CharField(max_length=255, blank=True, null=True)  # Теглайн фільму

    class Meta:
        db_table = 'movie_financials'

class movie_trailer (models.Model):
    movie = models.ForeignKey(MovieInfo, on_delete=models.CASCADE, related_name='trailers')
    film_id = models.IntegerField()  # Прибираємо unique=True, щоб дозволити кілька трейлерів
    trailer_url = models.URLField()

    def __str__(self):
        return f"Trailer for movie {self.film_id} ({self.movie.movie_name})"

class Watchlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="watchlist")
    movie = models.ForeignKey(MovieInfo, on_delete=models.CASCADE, related_name="watchlist_movies")

    class Meta:
        unique_together = ('user', 'movie')  # уникальність по користувачу та фільму

    def __str__(self):
        return f"{self.user.username} - {self.movie.movie_name}"

class Review(models.Model):
    movie = models.ForeignKey(MovieInfo, related_name='reviews', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    rating = models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)])  # оцінка від 1 до 5
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Review by {self.user.username} on {self.movie.title}'
