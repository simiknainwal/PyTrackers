
import requests
import time
import json
import os

class CurrencyConverter:
    def __init__(self, cache_file="data/currency_cache.json"):
        self.cache_file = cache_file
        self.cache_expiry = 60 * 60

        os.makedirs(os.path.dirname(cache_file) if os.path.dirname(cache_file) else ".", exist_ok=True)

    def _fetch_live_rates(self):
        try:
            url = "https://api.exchangerate.host/latest?base=INR"
            response = requests.get(url, timeout=10)
            data = response.json()

            cache_data = {
                "timestamp": time.time(),
                "rates": data["rates"]
            }

            with open(self.cache_file, "w") as f:
                json.dump(cache_data, f, indent=4)

            return data["rates"]

        except Exception:
            return None

    def _load_cached_rates(self):
        if not os.path.exists(self.cache_file):
            return None

        with open(self.cache_file, "r") as f:
            data = json.load(f)

        if time.time() - data["timestamp"] > self.cache_expiry:
            return None

        return data["rates"]

    def get_rates(self):
        cached = self._load_cached_rates()
        if cached:
            return cached

        live = self._fetch_live_rates()
        if live:
            return live

        print("⚠️ Could not fetch live rates. Using cached if available.")
        return cached or {}

    def convert(self, amount_in_inr, to_currency):
        rates = self.get_rates()
        to_currency = to_currency.upper()

        if to_currency not in rates:
            return None

        return round(amount_in_inr * rates[to_currency], 2)
