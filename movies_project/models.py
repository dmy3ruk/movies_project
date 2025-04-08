from django.db import models


class movies(models.Model):
    class Meta:
        db_table = 'movies'  # Явно вказуємо ім'я таблиці
    # Поля відповідають колонкам таблиці

    home_page = models.TextField()  # Home_Page
    movie_name = models.CharField(max_length=255)  # Movie_Name
    genres = models.TextField()  # Genres
    overview = models.TextField()  # Overview
    Cast = models.TextField()  # Cast (взято в лапки через зарезервоване слово)
    original_language = models.CharField(max_length=2)  # Original_Language (як правило, це 2-літерний код мови)
    storyline = models.TextField()  # Storyline
    production_company = models.CharField(max_length=255)  # Production_Company
    release_date = models.DateField()  # Release_Date
    tagline = models.CharField(max_length=255, blank=True, null=True)  # Tagline
    vote_average = models.FloatField()  # Vote_Average
    vote_count = models.BigIntegerField()  # Vote_Count
    budget_usd = models.BigIntegerField()  # Budget_USD
    revenue_usd = models.BigIntegerField()  # Revenue_USD
    run_time_minutes = models.IntegerField()  # Run_Time_Minutes
    release_country = models.CharField(max_length=255)
    poster_url = models.TextField()
    media_type = models.TextField(default="none")
    def __str__(self):
        return self.movie_name