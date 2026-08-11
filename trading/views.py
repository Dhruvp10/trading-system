from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from decimal import Decimal
import yfinance as yf
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout

from users.models import UserProfile
from .models import Portfolio, Transaction, Watchlist


from django.shortcuts import render, redirect

def home(request):

    if request.user.is_authenticated:
        return redirect("dashboard")

    return render(request, "home.html")

from django.contrib.auth.decorators import login_required

@login_required
def dashboard(request):
    ...


@login_required
def dashboard(request):

    profile = UserProfile.objects.get(user=request.user)
    portfolio = Portfolio.objects.filter(user=request.user)
    
    try:
        nifty = yf.Ticker("^NSEI").info.get("currentPrice", 0)
    except:
        nifty = 0

    try:
        sensex = yf.Ticker("^BSESN").info.get("currentPrice", 0)
    except:
        sensex = 0

    total_portfolio = Decimal("0")
    total_profit = Decimal("0")

    for stock in portfolio:
        try:
            ticker = yf.Ticker(stock.symbol + ".NS")
            info = ticker.info
            current_price = Decimal(str(info.get("currentPrice", 0)))
        except:
            current_price = Decimal("0")

        investment = stock.average_price * stock.quantity
        current_value = current_price * stock.quantity

        total_portfolio += current_value
        total_profit += current_value - investment

    context = {
        "balance": profile.virtual_balance,
        "portfolio_value": total_portfolio,
        "profit": total_profit,
        "holdings": portfolio.count(),
        "portfolio": portfolio,
        "nifty": nifty,
        "sensex": sensex,
    }

    return render(request, "dashboard.html", context)


def search_stock(request):

    stock_data = None
    error = None

    if request.method == "POST":

        symbol = request.POST.get("symbol", "").upper()

        try:
            stock = yf.Ticker(symbol + ".NS")
            info = stock.info

            stock_data = {
                "symbol": symbol,
                "company": info.get("longName"),
                "price": info.get("currentPrice"),
                "open": info.get("open"),
                "high": info.get("dayHigh"),
                "low": info.get("dayLow"),
                "volume": info.get("volume"),
            }

        except Exception:
            error = "Stock not found!"

    return render(request, "search_stock.html", {
        "stock": stock_data,
        "error": error,
    })


@login_required
def buy_stock(request):

    if request.method == "POST":

        symbol = request.POST.get("symbol")
        company = request.POST.get("company")
        price = Decimal(request.POST.get("price"))
        quantity = int(request.POST.get("quantity"))

        total = price * quantity

        profile = UserProfile.objects.get(user=request.user)

        if profile.virtual_balance < total:
            messages.error(request, "Insufficient Balance!")
            return redirect("search_stock")

        profile.virtual_balance -= total
        profile.save()

        Transaction.objects.create(
            user=request.user,
            symbol=symbol,
            company_name=company,
            transaction_type="BUY",
            quantity=quantity,
            price=price,
            total_amount=total,
        )

        portfolio = Portfolio.objects.filter(
            user=request.user,
            symbol=symbol
        ).first()

        if portfolio:
            total_qty = portfolio.quantity + quantity

            avg_price = (
                (portfolio.average_price * portfolio.quantity)
                + (price * quantity)
            ) / total_qty

            portfolio.quantity = total_qty
            portfolio.average_price = avg_price
            portfolio.save()

        else:
            Portfolio.objects.create(
                user=request.user,
                symbol=symbol,
                company_name=company,
                quantity=quantity,
                average_price=price,
            )

        messages.success(request, "Stock purchased successfully!")
        return redirect("dashboard")

    return redirect("search_stock")


@login_required
def add_watchlist(request):

    if request.method == "POST":

        symbol = request.POST.get("symbol")
        company = request.POST.get("company")

        already_exists = Watchlist.objects.filter(
            user=request.user,
            symbol=symbol
        ).exists()

        if not already_exists:

            Watchlist.objects.create(
                user=request.user,
                symbol=symbol,
                company_name=company
            )

            messages.success(request, "Stock added to Watchlist!")

        else:
            messages.info(request, "Stock already exists in Watchlist!")

    return redirect("search_stock")


@login_required
def transactions(request):

    transactions = Transaction.objects.filter(
        user=request.user
    ).order_by("-id")

    return render(request, "transactions.html", {
        "transactions": transactions
    })


@login_required
def portfolio(request):

    portfolio = Portfolio.objects.filter(user=request.user)

    return render(request, "portfolio.html", {
        "portfolio": portfolio
    })


@login_required
def sell_stock(request, symbol):

    stock = get_object_or_404(
        Portfolio,
        user=request.user,
        symbol=symbol
    )

    if request.method == "POST":

        quantity = int(request.POST.get("quantity"))

        if quantity > stock.quantity:
            messages.error(request, "Invalid Quantity!")
            return redirect("sell_stock", symbol=symbol)

        ticker = yf.Ticker(symbol + ".NS")
        info = ticker.info
        current_price = Decimal(
            str(info.get("currentPrice", stock.average_price))
        )

        total_amount = current_price * quantity

        profile = UserProfile.objects.get(user=request.user)
        profile.virtual_balance += total_amount
        profile.save()

        Transaction.objects.create(
            user=request.user,
            symbol=stock.symbol,
            company_name=stock.company_name,
            transaction_type="SELL",
            quantity=quantity,
            price=current_price,
            total_amount=total_amount,
        )

        stock.quantity -= quantity

        if stock.quantity == 0:
            stock.delete()
        else:
            stock.save()

        messages.success(request, "Stock Sold Successfully!")
        return redirect("portfolio")

    return render(request, "sell_stock.html", {
        "stock": stock
    })


@login_required
def watchlist(request):

    stocks = Watchlist.objects.filter(user=request.user)

    watchlist_data = []

    for stock in stocks:

        try:
            ticker = yf.Ticker(stock.symbol + ".NS")
            info = ticker.info
            current_price = info.get("currentPrice", 0)

        except:
            current_price = 0

        watchlist_data.append({
            "symbol": stock.symbol,
            "company": stock.company_name,
            "price": current_price,
        })

    return render(request, "watchlist.html", {
        "watchlist": watchlist_data
    })