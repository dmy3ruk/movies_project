from rest_framework import serializers
from .models import Watchlist
from .models import MovieInfo  # Якщо фільми зберігаються в окремій моделі

# serializers.py
class MovieInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = MovieInfo
        fields = ['id', 'movie_name', 'poster_url']

class WatchlistSerializer(serializers.ModelSerializer):
    movie = MovieInfoSerializer()

    class Meta:
        model = Watchlist
        fields = ['id', 'movie']
