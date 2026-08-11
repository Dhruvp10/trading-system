from django.shortcuts import render, redirect
from . forms import UserRegisterform
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login
from django.contrib.auth.models import User
import yfinance as yf
from django.shortcuts import render

def register(request):
    if request.method == 'POST':
        form = UserRegisterform(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
        
    else:
            form = UserRegisterform()
            
    return render(request, "Register.html", {"form": form})
            
def login_view(request):
    form = AuthenticationForm(request, data=request.POST or None)
    
      
    if form.is_valid():
        user = form.get_user()
        login(request, user)
        return redirect("home")
    else:
        form = AuthenticationForm()
    
    return render(request, "login.html", {"form": form})

def search_stock(request):
    stock_data = None
    error = None

    if request.method == "POST":
        symbol = request.POST.get("symbol").upper()

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

    return render(
        request,
        "search_stock.html",
        {
            "stock": stock_data,
            "error": error,
        },
    )


# Create your views here.
