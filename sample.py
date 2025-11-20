from flask import Flask, render_template, request, redirect, url_for, session
from web_scraping import WebScraper, log_to_csv_row
from price_alert import PriceAlertSystem
from price_plot import generate_dummy_past_prices, plot_price_trend, get_recommendation
from datetime import datetime
import os
import pandas as pd

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

scraper = WebScraper()
alert_system = PriceAlertSystem()

CSV_FILE = "price_history.csv"

# =====================
# Dummy Users
# =====================
USERS = {
    'admin': '1234'
}

# =====================
# Auth
# =====================

@app.route('/login', methods=['GET','POST'])
def login():
    if 'username' in session:
        return redirect(url_for('home'))

    message = ""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username in USERS and USERS[username] == password:
            session['username'] = username
            return redirect(url_for('home'))
        else:
            message = "⚠️ Invalid username or password"

    return render_template("login.html", message=message)


@app.route('/register', methods=['GET','POST'])
def register():
    if 'username' in session:
        return redirect(url_for('home'))

    message = ""
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()

        if username in USERS:
            message = "⚠️ Username already exists!"
        elif username == "" or password == "":
            message = "⚠️ Username and password cannot be empty!"
        else:
            USERS[username] = password
            return redirect(url_for('login'))

    return render_template("register.html", message=message)


@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))


# =====================
# Login Required Decorator
# =====================

def login_required(f):
    from functools import wraps

    @wraps(f)
    def decorated(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)

    return decorated


# =====================
# Home Page
# =====================

@app.route("/")
@login_required
def home():
    return render_template("index.html")


# =====================
# Track Product
# =====================

@app.route("/track", methods=['GET','POST'])
@login_required
def track():
    image_path = None
    web_message = ""

    if request.method == 'POST':
        url = request.form['url'].strip()
        target = float(request.form['target'])
        username = session['username']   # <-- identify user

        product_data = scraper.scrape_product(url)

        if product_data and product_data["price"] > 0:
            now = datetime.now()

            # ============================
            # ADD USERNAME TO CSV ROW HERE
            # ============================
            row = {
                'username': username,
                'product_id': product_data['product_id'],
                'product_name': product_data['product_name'],
                'date': now.strftime("%Y-%m-%d"),
                'time': now.strftime("%H:%M:%S"),
                'price': product_data['price'],
                'source': product_data['source'],
                'url': product_data['url']
            }

            log_to_csv_row(CSV_FILE, row)

            past_df = generate_dummy_past_prices(product_data['price'])
            recommendation = get_recommendation(product_data['price'], past_df, target)

            image_path = plot_price_trend(
                product_data["product_name"],
                product_data["price"],
                target,
                past_df
            )

            web_message = (
                f"✅ <b>{product_data['product_name']}</b><br>"
                f"💰 Current Price: ₹{product_data['price']}<br>"
                f"🎯 Target Price: ₹{target}<br>"
                f"💡 Recommendation: {recommendation}<br>"
            )

            if product_data["price"] <= target:
                web_message += "🎯 Target reached! You can buy now."
            else:
                web_message += "⏳ Price is above target. Try again later."

        else:
            web_message = "❌ Failed to fetch product. Check URL."

        return render_template("track2.html", message=web_message, image_path=image_path)

    return render_template("index.html")


# =====================
# History Page (User-wise)
# =====================

@app.route("/history")
@login_required
def history():
    username = session['username']

    if not os.path.exists(CSV_FILE):
        return render_template("history.html", products=[], message="No tracking history yet!")

    try:
        df = pd.read_csv(CSV_FILE)

        # ============================
        # FILTER ONLY CURRENT USER DATA
        # ============================
        df = df[df['username'] == username]

        if df.empty:
            return render_template("history.html", products=[], message="You haven't tracked anything yet!")

        df['datetime'] = pd.to_datetime(df['date'] + ' ' + df['time'])
        df = df.sort_values('datetime', ascending=False)

        latest = df.groupby('product_id').first().reset_index()
        products = latest.to_dict('records')

        return render_template("history.html", products=products, message=None)

    except Exception as e:
        print("Error:", e)
        return render_template("history.html", products=[], message="Error loading history")


# =====================
# Run App
# =====================

if __name__ == "__main__":
    app.run(debug=True)
