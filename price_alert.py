import pandas as pd
import os
from datetime import datetime

class PriceAlertSystem:
    def __init__(self, csv_file='data/price_history.csv'):
        self.csv_file = csv_file
        os.makedirs(os.path.dirname(csv_file) if os.path.dirname(csv_file) else "data", exist_ok=True)

    def check_and_alert(self, product_data, target_price):
        """
        Check if the current price has reached or gone below target.
        """
        current_price = product_data.get('price')
        # FIXED: Changed 'name' to 'product_name' to match scraper output
        product_name = product_data.get('product_name', 'Unknown Product')

        if current_price is None:
            return f"⚠️ Price data unavailable for {product_name}"

        if current_price <= target_price:
            return f"🎯 ALERT! {product_name} has reached your target price (₹{current_price} ≤ ₹{target_price})"
        else:
            return f"⏳ No alert - current price (₹{current_price}) is above target (₹{target_price})."

    def get_price_analysis(self, product_id):
        """
        Analyze historical price trends for a given product.
        """
        if not os.path.exists(self.csv_file):
            print(f"⚠️ CSV file not found: {self.csv_file}")
            return None
        
        try:
            df = pd.read_csv(self.csv_file)

            # Ensure required columns exist
            required_cols = {'product_id', 'product_name', 'price', 'date', 'time'}
            if not required_cols.issubset(df.columns):
                print(f"⚠️ CSV missing required columns. Found: {df.columns.tolist()}")
                print(f"⚠️ Required: {required_cols}")
                return None

            # Filter by product_id
            product_df = df[df['product_id'] == product_id].copy()
            if len(product_df) == 0:
                print(f"⚠️ No data found for product_id: {product_id}")
                return None

            # Convert and sort datetime
            product_df['datetime'] = pd.to_datetime(product_df['date'] + ' ' + product_df['time'])
            product_df = product_df.sort_values('datetime')

            # Core statistics
            current_price = product_df['price'].iloc[-1]
            avg_price = product_df['price'].mean()
            min_price = product_df['price'].min()
            max_price = product_df['price'].max()

            # Trend analysis (last few entries)
            recent = product_df.tail(min(7, len(product_df)))
            if len(recent) > 1:
                price_change = recent['price'].iloc[-1] - recent['price'].iloc[0]
                trend = "📈 Rising" if price_change > 0 else "📉 Falling" if price_change < 0 else "➡️ Stable"
            else:
                trend = "➡️ Insufficient data"

            # Recommendation logic
            if current_price <= min_price * 1.05:
                recommendation = "🟢 BUY NOW - Near historical low!"
            elif current_price <= avg_price * 0.9:
                recommendation = "🟡 GOOD TIME TO BUY"
            elif current_price >= avg_price * 1.1:
                recommendation = "🔴 WAIT - Price is high"
            else:
                recommendation = "🟡 FAIR PRICE"

            analysis = {
                'product_name': product_df['product_name'].iloc[-1],
                'current_price': round(current_price, 2),
                'avg_price': round(avg_price, 2),
                'min_price': round(min_price, 2),
                'max_price': round(max_price, 2),
                'trend': trend,
                'recommendation': recommendation,
                'data_points': len(product_df)
            }
            
            print(f"✅ Analysis complete for {analysis['product_name']}")
            return analysis

        except pd.errors.EmptyDataError:
            print(f"⚠️ CSV file is empty: {self.csv_file}")
            return None
        except Exception as e:
            print(f"⚠️ Error in analysis: {e}")
            import traceback
            traceback.print_exc()
            return None