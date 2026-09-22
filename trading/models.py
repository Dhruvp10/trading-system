
from django.db import models
from django.contrib.auth.models import User


class Portfolio(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    symbol = models.CharField(
        max_length=20
    )

    company_name = models.CharField(
        max_length=200
    )

    quantity = models.PositiveIntegerField()

    average_price = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    def __str__(self):
        return f"{self.user.username} - {self.symbol}"


class Transaction(models.Model):

    TRANSACTION_TYPES = [
        ('BUY', 'Buy'),
        ('SELL', 'Sell'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    symbol = models.CharField(
        max_length=20
    )

    company_name = models.CharField(
        max_length=200
    )

    transaction_type = models.CharField(
        max_length=4,
        choices=TRANSACTION_TYPES
    )

    quantity = models.PositiveIntegerField()

    price = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    total_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.transaction_type} - {self.symbol} ({self.user.username})"


class Watchlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    symbol = models.CharField(max_length=20)
    company_name = models.CharField(max_length=200)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "symbol"],
                name="unique_user_watchlist_stock"
            )
        ]

    def __str__(self):
        return f"{self.user.username} - {self.symbol}"


# ==========================================
# NSE STOCK MASTER
# ==========================================

class Stock(models.Model):

    symbol = models.CharField(
        max_length=30,
        unique=True
    )

    company_name = models.CharField(
        max_length=200
    )

    exchange = models.CharField(
        max_length=20,
        default="NSE"
    )

    def __str__(self):
        return f"{self.symbol} - {self.company_name}"

