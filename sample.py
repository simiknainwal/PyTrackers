from flask import Flask, render_template, request
from web_scraping import WebScraper, log_to_csv_row
from price_alert import PriceAlertSystem
from price_plot import generate_dummy_past_prices, plot_price_trend, get_recommendation
from datetime import datetime
import os
import pandas as pd

app = Flask(__name__)

scraper = WebScraper()
alert_system = PriceAlertSystem()
CSV_FILE = 'price_history.csv'


@app.route('/')
def home():
    """Render homepage."""
    return render_template('index.html')


@app.route('/track', methods=['GET', 'POST'])
def track():
    """Handle product tracking and visualization."""
    image_path = None
    web_message = ""

    if request.method == 'POST':
        url = request.form['url'].strip()
        target = float(request.form['target'])

        # Scrape product once (no background thread)
        product_data = scraper.scrape_product(url)

        if product_data and product_data['price'] > 0:
            now = datetime.now()

            # Log current price to CSV
            row = {
                'product_id': product_data['product_id'],
                'product_name': product_data['product_name'],
                'date': now.strftime("%Y-%m-%d"),
                'time': now.strftime("%H:%M:%S"),
                'price': product_data['price'],
                'source': product_data['source'],
                'url': product_data['url']
            }
            log_to_csv_row(CSV_FILE, row)

            # Generate dummy data for last year's prices
            past_df = generate_dummy_past_prices(product_data['price'])

            # Get recommendation and plot price trend
            recommendation = get_recommendation(product_data['price'], past_df, target)
            image_path = plot_price_trend(
                product_data['product_name'],
                product_data['price'],
                target,
                past_df
            )

            # Prepare message for UI
            web_message = (
                f"✅ <b>{product_data['product_name']}</b><br>"
                f"💰 Current Price: ₹{product_data['price']}<br>"
                f"🎯 Target Price: ₹{target}<br>"
                f"💡 Recommendation: {recommendation}<br>"
            )

            # Immediate check for alert condition
            if product_data['price'] <= target:
                web_message += "🎯 Target reached! You can buy now."
            else:
                web_message += "⏳ Price is above target. Try again later."

        else:
            web_message = "❌ Failed to fetch product. Check URL."

        return render_template('track2.html', message=web_message, image_path=image_path)
    
    # FIX: Handle GET request - show the tracking form
    return render_template('index.html')


@app.route('/history')
def history():
    """Display all tracked products from CSV."""
    if not os.path.exists(CSV_FILE):
        return render_template('history.html', products=[], message="No tracking history yet!")
    
    try:
        df = pd.read_csv(CSV_FILE)
        
        # Get latest entry for each unique product
        df['datetime'] = pd.to_datetime(df['date'] + ' ' + df['time'])
        df = df.sort_values('datetime', ascending=False)
        
        # Group by product_id and get the most recent entry
        latest_products = df.groupby('product_id').first().reset_index()
        
        # Convert to list of dictionaries
        products = latest_products.to_dict('records')
        
        return render_template('history.html', products=products, message=None)
    
    except Exception as e:
        print(f"⚠️ Error reading history: {e}")
        return render_template('history.html', products=[], message="Error loading tracking history")


if __name__ == '__main__':
    os.makedirs('data', exist_ok=True)
    app.run(debug=True)