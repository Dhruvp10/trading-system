import csv
from pathlib import Path

from django.core.management.base import BaseCommand

from trading.models import Stock


class Command(BaseCommand):

    help = "Import NSE stocks from EQUITY_L.csv"

    def handle(self, *args, **kwargs):

        file_path = (
    Path(__file__).resolve().parent.parent.parent
    / "data"
    / "EQUITY_L.csv"
)

        if not file_path.exists():
            self.stdout.write(
                self.style.ERROR(
                    f"CSV file not found: {file_path}"
                )
            )
            return

        added = 0
        updated = 0

        with open(
            file_path,
            "r",
            encoding="utf-8-sig"
        ) as file:

            reader = csv.DictReader(file)

            for row in reader:

                symbol = row.get("SYMBOL", "").strip()
                company_name = row.get(
                    "NAME OF COMPANY", ""
                ).strip()

                series = row.get(" SERIES", "").strip()

                if not series:
                    series = row.get("SERIES", "").strip()

                if not symbol or not company_name:
                    continue

                # Only regular equity stocks
                if series and series != "EQ":
                    continue

                stock, created = Stock.objects.update_or_create(
                    symbol=symbol,
                    defaults={
                        "company_name": company_name,
                        "exchange": "NSE",
                    }
                )

                if created:
                    added += 1
                else:
                    updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Import completed! "
                f"Added: {added}, Updated: {updated}"
            )
        )