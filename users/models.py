from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    virtual_balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=100000.00
    )

    def __str__(self):
        return self.user.username