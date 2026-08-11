from django.contrib import admin
from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("search/", views.search_stock, name="search_stock"),
    path("buy/", views.buy_stock, name="buy_stock"),
    path("portfolio/", views.portfolio, name="portfolio"),
    path("sell/<str:symbol>/", views.sell_stock, name="sell_stock"),
    path("transactions/", views.transactions, name="transactions"),
    path("watchlist/", views.watchlist, name="watchlist"),
]
