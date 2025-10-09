from flask import Flask, render_template, request
from web_scraping import WebScraper
from price_alert import PriceAlertSystem
import csv
import os
app = Flask(__name__)
scraper = WebScraper()
alert_system = PriceAlertSystem()
CSV_FILE = 'price_history.csv'
#This function is used to save data in CSV file.
def save_to_csv(data):
    file_exists = os.path.isfile(CSV_FILE)
    with open(CSV_FILE, 'a', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=['Product Name', 'Current Price', 'Target Price', 'Currency', 'URL'])
        if not file_exists:
            writer.writeheader()
        writer.writerow({
            'Product Name': data['product_name'],
            'Current Price': data['price'],
            'Target Price': data['target_price'],
            'Currency': data['currency'],
            'URL': data['url']
        })


# --- Home Page ---
@app.route('/')
def home():
    return render_template('index.html')


# --- Track Product Page ---
@app.route('/track', methods=['GET', 'POST'])
def track():
    if request.method == 'POST':
        url = request.form['url'].strip()
        target = float(request.form['target'])
        currency = request.form['currency'].strip()

        # Scrape product details
        product_data = scraper.scrape_product(url)

        if product_data:
            # Add target and currency fields
            product_data['target_price'] = target
            product_data['currency'] = currency

            # Save data in CSV
            save_to_csv(product_data)

            # Check price alert
            alert_message = alert_system.check_and_alert(product_data, target)

            # Generate message for web interface
            if product_data['price'] <= target:
                web_message = (f"<b>PRICE DROP ALERT!</b><br>"
                               f"Product: {product_data['product_name']}<br>"
                               f"Current Price: {product_data['price']} {currency}<br>"
                               f"Target Price: {target} {currency}<br>"
                               f"You save: {target - product_data['price']:.2f} {currency}<br>"
                               f"Recommended: BUY NOW!")
            else:
                web_message = (f"Tracking started for '{product_data['product_name']}'<br>"
                               f"Current Price: {product_data['price']} {currency}<br>"
                               f"Target Price: {target} {currency}<br>"
                               f"Price is {product_data['price'] - target:.2f} {currency} above your target. Keep monitoring.")

        else:
            web_message = "Failed to fetch product details. Please check the URL or try again."

        return render_template('track2.html', message=web_message)

    return render_template('track2.html')


# --- Run Flask App ---
if __name__ == '__main__':
    app.run(debug=True)