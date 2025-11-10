import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for server environments
import matplotlib.pyplot as plt
import random
import os
from datetime import datetime


def generate_dummy_past_prices(current_price):
    """
    Generate dummy monthly price data for the past 12 months
    by fluctuating ±10% around the current price.
    """
    if not current_price or current_price <= 0:
        print("⚠️ Invalid current price for generating dummy data")
        return pd.DataFrame()
    
    try:
        today = datetime.today()
        data = []

        for i in range(12, 0, -1):
            # Generate month name (e.g., "Jan 2025")
            month_date = today.replace(day=1) - pd.DateOffset(months=i)
            # Simulate realistic price fluctuation ±10%
            simulated_price = current_price * (1 + random.uniform(-0.1, 0.1))
            data.append({
                "month": month_date.strftime('%b %Y'),
                "price": round(simulated_price, 2)
            })

        df = pd.DataFrame(data)
        print(f"✅ Generated {len(df)} months of historical price data")
        return df
    
    except Exception as e:
        print(f"⚠️ Error generating dummy prices: {e}")
        return pd.DataFrame()


def plot_price_trend(product_name, current_price, target_price, df):
    """
    Plot price trend for the product using dummy past data
    and save the graph image inside the /static folder.
    """
    try:
        # Validate inputs
        if df is None or df.empty:
            print("⚠️ No data available to plot")
            return None
        
        if not current_price or current_price <= 0:
            print("⚠️ Invalid current price for plotting")
            return None
        
        # Create figure
        plt.figure(figsize=(10, 5))
        plt.plot(df['month'], df['price'], marker='o', linewidth=2, 
                label='Past Avg Price', color='#3b82f6', markersize=6)

        # Highlight lines for current and target prices
        plt.axhline(y=current_price, color='#10b981', linestyle='--', 
                   linewidth=1.5, label=f'Current: ₹{current_price}')
        plt.axhline(y=target_price, color='#ef4444', linestyle='--', 
                   linewidth=1.5, label=f'Target: ₹{target_price}')

        # Styling
        plt.xticks(rotation=45, ha='right')
        plt.ylabel('Price (₹)', fontsize=11, fontweight='bold')
        plt.xlabel('Month', fontsize=11, fontweight='bold')
        plt.title(f'Price Trend: {product_name[:50]}', fontsize=13, fontweight='bold')
        plt.legend(loc='best', framealpha=0.9)
        plt.grid(alpha=0.3, linestyle=':', linewidth=0.5)
        plt.tight_layout()

        # Save plot to static directory
        os.makedirs('static', exist_ok=True)
        
        # Create safe filename (limit length and remove special characters)
        safe_name = "".join([c if c.isalnum() or c in (' ', '-') else "_" 
                            for c in product_name])
        safe_name = safe_name[:50]  # Limit length to avoid filesystem issues
        
        # Add timestamp to avoid overwriting
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"static/{safe_name}_{timestamp}_trend.png"
        
        plt.savefig(filename, dpi=150, bbox_inches='tight', facecolor='white')
        plt.close('all')  # Close all figures to free memory
        
        print(f"✅ Price trend chart saved: {filename}")
        return filename
    
    except Exception as e:
        print(f"⚠️ Error creating price plot: {e}")
        import traceback
        traceback.print_exc()
        # Make sure to close any open figures
        plt.close('all')
        return None


def get_recommendation(current_price, df, target_price):
    """
    Analyze the price compared to past data and target to give recommendation.
    """
    try:
        # Validate inputs
        if not current_price or current_price <= 0:
            return "⚠️ Invalid price data"
        
        if df is None or df.empty or 'price' not in df.columns:
            return "⚠️ Insufficient historical data for recommendation"
        
        lowest_price = df['price'].min()
        avg_price = df['price'].mean()
        highest_price = df['price'].max()

        # Calculate price position
        price_vs_avg = ((current_price - avg_price) / avg_price) * 100
        price_vs_low = ((current_price - lowest_price) / lowest_price) * 100

        # Enhanced recommendation logic
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
    
    except Exception as e:
        print(f"⚠️ Error generating recommendation: {e}")
        return "⚠️ Unable to generate recommendation"


def cleanup_old_charts(days_old=7):
    """
    Clean up chart images older than specified days to save disk space.
    """
    try:
        static_dir = 'static'
        if not os.path.exists(static_dir):
            return
        
        current_time = datetime.now()
        deleted_count = 0
        
        for filename in os.listdir(static_dir):
            if filename.endswith('_trend.png'):
                filepath = os.path.join(static_dir, filename)
                file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
                age_days = (current_time - file_time).days
                
                if age_days > days_old:
                    os.remove(filepath)
                    deleted_count += 1
        
        if deleted_count > 0:
            print(f"🧹 Cleaned up {deleted_count} old chart(s)")
    
    except Exception as e:
        print(f"⚠️ Error during cleanup: {e}")