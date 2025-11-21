import pandas as pd
import matplotlib
matplotlib.use('Agg')  
import matplotlib.pyplot as plt
import random
import os
from datetime import datetime

def generate_dummy_past_prices(current_price):
    if not current_price or current_price <= 0:
        return pd.DataFrame()
    
    try:
        today = datetime.today()
        data = []

        for i in range(12, 0, -1):
            month_date = today.replace(day=1) - pd.DateOffset(months=i)
            simulated_price = current_price * (1 + random.uniform(-0.1, 0.1))
            data.append({
                "month": month_date.strftime('%b %Y'),
                "price": round(simulated_price, 2)
            })

        df = pd.DataFrame(data)
        return df
    
    except Exception:
        return pd.DataFrame()


def plot_price_trend(product_name, current_price, target_price, df):
    try:
        if df is None or df.empty or not current_price or current_price <= 0:
            return None
        
        plt.figure(figsize=(10, 5))

        plt.plot(df['month'], df['price'], marker='o', linewidth=2, 
                label='Past Avg Price', color='#3b82f6', markersize=6)
        plt.axhline(y=current_price, color='#10b981', linestyle='--', 
                   linewidth=1.5, label=f'Current: ₹{current_price}')
        plt.axhline(y=target_price, color='#ef4444', linestyle='--', 
                   linewidth=1.5, label=f'Target: ₹{target_price}')

        plt.xticks(rotation=45, ha='right')
        plt.ylabel('Price (₹)', fontsize=11, fontweight='bold')
        plt.xlabel('Month', fontsize=11, fontweight='bold')
        plt.title(f'Price Trend: {product_name[:50]}', fontsize=13, fontweight='bold')
        plt.legend(loc='best', framealpha=0.9)
        plt.grid(alpha=0.3, linestyle=':', linewidth=0.5)
        plt.tight_layout()
        os.makedirs('static', exist_ok=True)
        
        safe_name = "".join([c if c.isalnum() or c in (' ', '-') else "_" for c in product_name])
        safe_name = safe_name[:50]  
        
        filename = f"static/{safe_name}_trend.png"
        plt.savefig(filename, dpi=150, bbox_inches='tight', facecolor='white')
        plt.close('all')  
        
        return filename
    
    except Exception:
        plt.close('all')
        return None


def get_recommendation(current_price, df, target_price):
    try:
        if not current_price or current_price <= 0:
            return "⚠️ Invalid price data"
        
        if df is None or df.empty or 'price' not in df.columns:
            return "⚠️ Insufficient historical data for recommendation"
        
        lowest_price = df['price'].min()
        avg_price = df['price'].mean()
        highest_price = df['price'].max()

        price_vs_avg = ((current_price - avg_price) / avg_price) * 100
        price_vs_low = ((current_price - lowest_price) / lowest_price) * 100
        
        if current_price <= target_price:
            return f"🟢 BUY NOW – Price is at or below your target! (₹{current_price} ≤ ₹{target_price})"
        elif current_price <= lowest_price * 1.05:
            return f"🟢 BUY NOW – Near historical low! (Only {price_vs_low:.1f}% above lowest)"
        elif current_price <= avg_price * 0.95:
            return f"🟡 FAIR DEAL – Below average price ({price_vs_avg:.1f}% below average)"
        elif current_price >= avg_price * 1.15:
            return f"🔴 WAIT – Price is significantly higher than usual ({price_vs_avg:.1f}% above average)"
        elif current_price >= avg_price * 1.1:
            return f"🔴 WAIT – Price is higher than usual ({price_vs_avg:.1f}% above average)"
        else:
            return f"🟡 FAIR PRICE – Close to average price (₹{avg_price:.2f})"
    
    except Exception:
        return "⚠️ Unable to generate recommendation"
