from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from decimal import Decimal
import yfinance as yf
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from users.models import UserProfile
from .models import Portfolio, Transaction, Watchlist, Stock
from django.db import transaction


def home(request):
    return render(request, "home.html")


@login_required
def dashboard(request):

    profile = UserProfile.objects.get(user=request.user)
    portfolio = Portfolio.objects.filter(user=request.user)

    try:
        nifty = yf.Ticker("^NSEI").info.get("currentPrice", 0)
    except Exception:
        nifty = 0

    try:
        sensex = yf.Ticker("^BSESN").info.get("currentPrice", 0)
    except Exception:
        sensex = 0

    total_portfolio = Decimal("0")
    total_profit = Decimal("0")

    performance_data = []

    for stock in portfolio:

        try:
            ticker = yf.Ticker(stock.symbol + ".NS")
            info = ticker.info

            current_price = Decimal(
                str(info.get("currentPrice", stock.average_price))
            )

        except Exception:
            current_price = stock.average_price

        investment = stock.average_price * stock.quantity
        current_value = current_price * stock.quantity

        total_portfolio += current_value
        total_profit += current_value - investment

        performance_data.append({
            "symbol": stock.symbol,
            "investment": float(investment),
            "current_value": float(current_value),
        })

    context = {
        "balance": profile.virtual_balance,
        "portfolio_value": total_portfolio,
        "profit": total_profit,
        "holdings": portfolio.count(),
        "portfolio": portfolio,
        "nifty": nifty,
        "sensex": sensex,
        "performance_data": performance_data,
    }

    return render(request, "dashboard.html", context)


def search_stock(request):

    stock_data = None
    error = None

    if request.method == "POST":

        symbol = request.POST.get("symbol", "").strip().upper()

        if not symbol:
            error = "Please enter a stock symbol."

        else:

            db_stock = Stock.objects.filter(
                symbol__iexact=symbol
            ).first()

            if not db_stock:
                error = "Stock not found in NSE database."

            else:

                symbol = db_stock.symbol
                yf_symbol = symbol + ".NS"

                try:

                    print("=" * 60)
                    print("YFINANCE DEBUG START")
                    print("Symbol:", yf_symbol)

                    ticker = yf.Ticker(yf_symbol)

                    # -----------------------------------------
                    # Try history first
                    # -----------------------------------------

                    try:

                        history = ticker.history(
                            period="5d",
                            interval="1d",
                            auto_adjust=False
                        )

                        print("History Empty:", history.empty)
                        print("History Columns:", list(history.columns))

                        if not history.empty:
                            print("Latest History:")
                            print(history.tail(1).to_string())

                        else:
                            print("History returned EMPTY")

                    except Exception as history_error:

                        history = None

                        print(
                            "History Error:",
                            repr(history_error)
                        )


                    # -----------------------------------------
                    # Default values
                    # -----------------------------------------

                    current_price = 0
                    open_price = 0
                    high_price = 0
                    low_price = 0
                    volume = 0


                    # -----------------------------------------
                    # Get price from history
                    # -----------------------------------------

                    if history is not None and not history.empty:

                        latest = history.iloc[-1]

                        current_price = latest.get(
                            "Close",
                            0
                        )

                        open_price = latest.get(
                            "Open",
                            0
                        )

                        high_price = latest.get(
                            "High",
                            0
                        )

                        low_price = latest.get(
                            "Low",
                            0
                        )

                        volume = latest.get(
                            "Volume",
                            0
                        )

                        print(
                            "History Current Price:",
                            current_price
                        )


                    # -----------------------------------------
                    # If history failed, try ticker.info
                    # -----------------------------------------

                    if (
                        current_price is None
                        or current_price <= 0
                    ):

                        print(
                            "History price unavailable."
                        )

                        try:

                            info = ticker.info

                            print(
                                "Ticker Info received:",
                                bool(info)
                            )

                            current_price = (
                                info.get("currentPrice")
                                or info.get("regularMarketPrice")
                                or info.get("previousClose")
                                or 0
                            )

                            open_price = (
                                info.get("open")
                                or info.get("regularMarketOpen")
                                or 0
                            )

                            high_price = (
                                info.get("dayHigh")
                                or info.get(
                                    "regularMarketDayHigh"
                                )
                                or 0
                            )

                            low_price = (
                                info.get("dayLow")
                                or info.get(
                                    "regularMarketDayLow"
                                )
                                or 0
                            )

                            volume = (
                                info.get("volume")
                                or info.get(
                                    "regularMarketVolume"
                                )
                                or 0
                            )

                            print(
                                "Info Current Price:",
                                current_price
                            )

                        except Exception as info_error:

                            print(
                                "Ticker Info Error:",
                                repr(info_error)
                            )


                    # -----------------------------------------
                    # Convert values safely
                    # -----------------------------------------

                    try:
                        current_price = float(
                            current_price or 0
                        )
                    except (TypeError, ValueError):
                        current_price = 0


                    try:
                        open_price = float(
                            open_price or 0
                        )
                    except (TypeError, ValueError):
                        open_price = 0


                    try:
                        high_price = float(
                            high_price or 0
                        )
                    except (TypeError, ValueError):
                        high_price = 0


                    try:
                        low_price = float(
                            low_price or 0
                        )
                    except (TypeError, ValueError):
                        low_price = 0


                    try:
                        volume = int(
                            volume or 0
                        )
                    except (TypeError, ValueError):
                        volume = 0


                    # -----------------------------------------
                    # Final price check
                    # -----------------------------------------

                    print(
                        "FINAL PRICE:",
                        current_price
                    )

                    print("YFINANCE DEBUG END")
                    print("=" * 60)


                    if current_price <= 0:

                        error = (
                            "Live stock price is currently "
                            "unavailable on the server. "
                            "Please try again."
                        )

                    else:

                        stock_data = {
                            "symbol": symbol,
                            "company": db_stock.company_name,
                            "price": current_price,
                            "open": open_price,
                            "high": high_price,
                            "low": low_price,
                            "volume": volume,
                        }


                except Exception as e:

                    print(
                        "YFinance Main Error:",
                        repr(e)
                    )

                    print(
                        "YFinance Error Type:",
                        type(e).__name__
                    )

                    error = (
                        "Unable to fetch live stock price. "
                        "Please try again."
                    )


    return render(
        request,
        "search_stock.html",
        {
            "stock": stock_data,
            "error": error,
        }
    )

@login_required
def buy_stock(request):

    if request.method == "POST":

        symbol = request.POST.get("symbol", "").strip().upper()
        company = request.POST.get("company", "").strip()

        try:
            price = Decimal(
                request.POST.get("price", "0")
            )
        except (TypeError, ValueError, ArithmeticError):

            messages.error(
                request,
                "Please enter a valid price."
            )

            return redirect("search_stock")

        try:
            quantity = int(
                request.POST.get("quantity", "0")
            )
        except (TypeError, ValueError):

            messages.error(
                request,
                "Please enter a valid quantity."
            )

            return redirect("search_stock")

        if not symbol:

            messages.error(
                request,
                "Invalid stock symbol."
            )

            return redirect("search_stock")

        if price <= 0:

            messages.error(
                request,
                "Price must be greater than 0."
            )

            return redirect("search_stock")

        if quantity <= 0:

            messages.error(
                request,
                "Quantity must be greater than 0."
            )

            return redirect("search_stock")

        total = price * quantity

        try:
            profile = UserProfile.objects.get(
                user=request.user
            )

        except UserProfile.DoesNotExist:

            messages.error(
                request,
                "User profile not found."
            )

            return redirect("dashboard")

        if profile.virtual_balance < total:

            messages.error(
                request,
                f"Insufficient Balance! Required ₹{total:.2f}"
            )

            return redirect("search_stock")

        with transaction.atomic():

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

                total_qty = (
                    portfolio.quantity + quantity
                )

                avg_price = (
                    (
                        portfolio.average_price
                        * portfolio.quantity
                    )
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

        messages.success(
            request,
            f"Successfully purchased {quantity} shares of {symbol}."
        )

        return redirect("dashboard")

    return redirect("search_stock")


@login_required
def add_watchlist(request):

    if request.method == "POST":

        symbol = request.POST.get(
            "symbol",
            ""
        ).strip().upper()

        company = request.POST.get(
            "company",
            ""
        ).strip()

        if not symbol:

            messages.error(
                request,
                "Invalid stock symbol."
            )

            return redirect("search_stock")

        if not company:

            messages.error(
                request,
                "Invalid company name."
            )

            return redirect("search_stock")

        already_exists = Watchlist.objects.filter(
            user=request.user,
            symbol=symbol
        ).exists()

        if already_exists:

            messages.info(
                request,
                f"{symbol} is already in your Watchlist."
            )

            return redirect("search_stock")

        Watchlist.objects.create(
            user=request.user,
            symbol=symbol,
            company_name=company
        )

        messages.success(
            request,
            f"{symbol} added to Watchlist successfully!"
        )

    return redirect("search_stock")


@login_required
def transactions(request):

    transactions = Transaction.objects.filter(
        user=request.user
    ).order_by("-id")

    return render(
        request,
        "transactions.html",
        {
            "transactions": transactions
        }
    )


@login_required
def portfolio(request):

    portfolio = Portfolio.objects.filter(
        user=request.user
    )

    portfolio_data = []

    total_investment = Decimal("0")
    total_current_value = Decimal("0")

    performance_data = []

    for stock in portfolio:

        try:

            ticker = yf.Ticker(
                stock.symbol + ".NS"
            )

            info = ticker.info

            current_price = Decimal(
                str(
                    info.get(
                        "currentPrice",
                        stock.average_price
                    )
                )
            )

        except Exception:

            current_price = stock.average_price

        investment = (
            stock.average_price
            * stock.quantity
        )

        current_value = (
            current_price
            * stock.quantity
        )

        profit_loss = (
            current_value
            - investment
        )

        if investment > 0:

            profit_percentage = (
                profit_loss
                / investment
            ) * 100

        else:

            profit_percentage = Decimal("0")

        total_investment += investment
        total_current_value += current_value

        portfolio_data.append({
            "symbol": stock.symbol,
            "company": stock.company_name,
            "quantity": stock.quantity,
            "average_price": stock.average_price,
            "current_price": current_price,
            "investment": investment,
            "current_value": current_value,
            "profit_loss": profit_loss,
            "profit_percentage": profit_percentage,
        })

        performance_data.append({
            "symbol": stock.symbol,
            "investment": float(investment),
            "current_value": float(current_value),
        })

    total_profit_loss = (
        total_current_value
        - total_investment
    )

    if total_investment > 0:

        total_profit_percentage = (
            total_profit_loss
            / total_investment
        ) * 100

    else:

        total_profit_percentage = Decimal("0")

    context = {
        "portfolio": portfolio_data,
        "total_investment": total_investment,
        "total_current_value": total_current_value,
        "total_profit_loss": total_profit_loss,
        "total_profit_percentage": total_profit_percentage,
        "performance_data": performance_data,
    }

    return render(
        request,
        "portfolio.html",
        context
    )


@login_required
def sell_stock(request, symbol):

    stock = get_object_or_404(
        Portfolio,
        user=request.user,
        symbol=symbol
    )

    if request.method == "POST":

        try:

            quantity = int(
                request.POST.get(
                    "quantity",
                    0
                )
            )

        except (TypeError, ValueError):

            messages.error(
                request,
                "Please enter a valid quantity."
            )

            return redirect(
                "sell_stock",
                symbol=symbol
            )

        if quantity <= 0:

            messages.error(
                request,
                "Quantity must be greater than 0."
            )

            return redirect(
                "sell_stock",
                symbol=symbol
            )

        if quantity > stock.quantity:

            messages.error(
                request,
                f"You only own {stock.quantity} shares."
            )

            return redirect(
                "sell_stock",
                symbol=symbol
            )

        try:

            ticker = yf.Ticker(
                symbol + ".NS"
            )

            info = ticker.info

            current_price = Decimal(
                str(
                    info.get(
                        "currentPrice",
                        stock.average_price
                    )
                )
            )

        except Exception:

            current_price = stock.average_price

        total_amount = (
            current_price
            * quantity
        )

        with transaction.atomic():

            profile = UserProfile.objects.get(
                user=request.user
            )

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

        messages.success(
            request,
            f"Successfully sold {quantity} shares of {symbol}."
        )

        return redirect("portfolio")

    return render(
        request,
        "sell_stock.html",
        {
            "stock": stock
        }
    )


@login_required
def watchlist(request):

    stocks = Watchlist.objects.filter(
        user=request.user
    )

    watchlist_data = []

    for stock in stocks:

        try:

            ticker = yf.Ticker(
                stock.symbol + ".NS"
            )

            info = ticker.info

            current_price = info.get(
                "currentPrice",
                0
            )

        except Exception:

            current_price = 0

        watchlist_data.append({
            "symbol": stock.symbol,
            "company": stock.company_name,
            "price": current_price,
        })

    return render(
        request,
        "watchlist.html",
        {
            "watchlist": watchlist_data
        }
    )


@login_required
def remove_watchlist(request, symbol):

    stock = Watchlist.objects.filter(
        user=request.user,
        symbol=symbol
    ).first()

    if stock:

        stock.delete()

        messages.success(
            request,
            "Stock removed from Watchlist!"
        )

    else:

        messages.error(
            request,
            "Stock not found in Watchlist!"
        )

    return redirect("watchlist")


@require_GET
def stock_suggestions(request):

    query = request.GET.get(
        "q",
        ""
    ).strip()

    if len(query) < 2:

        return JsonResponse(
            [],
            safe=False
        )

    stocks = Stock.objects.filter(
        symbol__icontains=query
    ).order_by("symbol")[:10]

    results = [
        {
            "symbol": stock.symbol,
            "company": stock.company_name
        }
        for stock in stocks
    ]

    return JsonResponse(
        results,
        safe=False
    )