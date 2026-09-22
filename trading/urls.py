from django.urls import path

from . import views


urlpatterns = [

    # Home
    path("", views.home, name="home"),

    # Dashboard
    path(
        "dashboard/",
        views.dashboard,
        name="dashboard"
    ),

    # Search Stock
    path(
        "search/",
        views.search_stock,
        name="search_stock"
    ),

    # Buy Stock
    path(
        "buy/",
        views.buy_stock,
        name="buy_stock"
    ),

    # Portfolio
    path(
        "portfolio/",
        views.portfolio,
        name="portfolio"
    ),

    # Sell Stock
    path(
        "sell/<str:symbol>/",
        views.sell_stock,
        name="sell_stock"
    ),

    # Transactions
    path(
        "transactions/",
        views.transactions,
        name="transactions"
    ),

    # Watchlist
    path(
        "watchlist/",
        views.watchlist,
        name="watchlist"
    ),

    # Add to Watchlist
    path(
        "watchlist/add/",
        views.add_watchlist,
        name="add_watchlist"
    ),

    # Remove from Watchlist
    path(
        "watchlist/remove/<str:symbol>/",
        views.remove_watchlist,
        name="remove_watchlist"
    ),

    # Stock Autocomplete Suggestions
    path(
        "stock-suggestions/",
        views.stock_suggestions,
        name="stock_suggestions"
    ),
]