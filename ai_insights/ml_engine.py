import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import mean_absolute_error
import joblib
import os
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Sum, Count, Avg, F
from billing.models import Bill, BillItem
from products.models import Product

class MLSalesPredictor:
    """Machine Learning Sales Predictor"""
    
    def __init__(self, shop):
        self.shop = shop
        self.model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.scaler = StandardScaler()
        self.model_path = f'ml_models/sales_model_{shop.id}.pkl'
        self.scaler_path = f'ml_models/scaler_{shop.id}.pkl'
        
    def prepare_sales_data(self):
        """Prepare sales data for ML training"""
        # Get last 90 days of sales data
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=90)
        
        bills = Bill.objects.filter(
            shop=self.shop,
            date__date__gte=start_date,
            date__date__lte=end_date
        ).values('date', 'total')
        
        if not bills:
            return None, None
            
        # Convert to DataFrame and ensure numeric types
        df = pd.DataFrame(bills)
        df['date'] = pd.to_datetime(df['date'])
        df['total'] = df['total'].astype(float)  # Convert Decimal to float
        
        # Group by date and sum sales
        daily_sales = df.groupby(df['date'].dt.date)['total'].sum().reset_index()
        daily_sales['date'] = pd.to_datetime(daily_sales['date'])
        
        # Create features
        daily_sales['day_of_week'] = daily_sales['date'].dt.dayofweek
        daily_sales['month'] = daily_sales['date'].dt.month
        daily_sales['day_of_month'] = daily_sales['date'].dt.day
        daily_sales['is_weekend'] = daily_sales['day_of_week'].isin([5, 6]).astype(int)
        daily_sales['is_month_end'] = (daily_sales['day_of_month'] > 25).astype(int)
        
        # Add lag features (previous days sales)
        daily_sales = daily_sales.sort_values('date')
        daily_sales['sales_lag_1'] = daily_sales['total'].shift(1)
        daily_sales['sales_lag_7'] = daily_sales['total'].shift(7)
        daily_sales['sales_ma_7'] = daily_sales['total'].rolling(window=7).mean()
        
        # Remove rows with NaN values
        daily_sales = daily_sales.dropna()
        
        if len(daily_sales) < 10:
            return None, None
            
        features = ['day_of_week', 'month', 'day_of_month', 'is_weekend', 
                   'is_month_end', 'sales_lag_1', 'sales_lag_7', 'sales_ma_7']
        
        X = daily_sales[features]
        y = daily_sales['total']
        
        return X, y
    
    def train_model(self, force_retrain=False):
        """Train the ML model"""
        X, y = self.prepare_sales_data()
        
        if X is None or len(X) < 10:
            return False
            
        try:
            # Scale features
            X_scaled = self.scaler.fit_transform(X)
            
            # Train model
            self.model.fit(X_scaled, y)
            
            # Create models directory if it doesn't exist
            os.makedirs('ml_models', exist_ok=True)
            
            # Save model and scaler
            joblib.dump(self.model, self.model_path)
            joblib.dump(self.scaler, self.scaler_path)
            
            print(f"✅ Model trained and saved: {os.path.basename(self.model_path)}")
            print(f"Features used: {X.shape[1]} (Expected: 8)")
            
            return True
        except Exception as e:
            print(f"Error training model: {e}")
            return False
    
    def retrain_model(self):
        """Force retrain the model with current data"""
        # Delete old model files
        if os.path.exists(self.model_path):
            os.remove(self.model_path)
        if os.path.exists(self.scaler_path):
            os.remove(self.scaler_path)
        
        return self.train_model()
    
    def predict_sales(self, future_days=7):
        """Predict sales for future days"""
        try:
            # Load model if exists
            if os.path.exists(self.model_path) and os.path.exists(self.scaler_path):
                try:
                    model = joblib.load(self.model_path)
                    scaler = joblib.load(self.scaler_path)
                    print(f"✅ ML Model loaded: {os.path.basename(self.model_path)}")
                except Exception as load_error:
                    print(f"❌ Model loading failed: {load_error}")
                    # Retrain model
                    if not self.train_model():
                        return self._fallback_prediction(future_days)
                    model = self.model
                    scaler = self.scaler
            else:
                # Train new model
                if not self.train_model():
                    return self._fallback_prediction(future_days)
                model = self.model
                scaler = self.scaler
            
            # Get recent sales for lag features
            recent_sales = self._get_recent_sales()
            if not recent_sales:
                return self._fallback_prediction(future_days)
            
            predictions = []
            
            for i in range(1, future_days + 1):
                future_date = timezone.now().date() + timedelta(days=i)
                
                # Create features for future date - EXACTLY 8 features to match training
                features = [
                    future_date.weekday(),  # day_of_week
                    future_date.month,      # month
                    future_date.day,        # day_of_month
                    1 if future_date.weekday() in [5, 6] else 0,  # is_weekend
                    1 if future_date.day > 25 else 0,  # is_month_end
                    recent_sales[-1] if recent_sales else 0,  # sales_lag_1
                    recent_sales[-7] if len(recent_sales) >= 7 else recent_sales[-1],  # sales_lag_7
                    np.mean(recent_sales[-7:]) if len(recent_sales) >= 7 else recent_sales[-1]  # sales_ma_7
                ]
                
                # Ensure exactly 8 features
                if len(features) != 8:
                    print(f"⚠️ Feature count mismatch: {len(features)} instead of 8")
                    return self._fallback_prediction(future_days)
                
                try:
                    # Scale and predict
                    features_scaled = scaler.transform([features])
                    prediction = model.predict(features_scaled)[0]
                    
                    # Ensure positive prediction
                    prediction = max(0, prediction)
                    
                    predictions.append({
                        'date': future_date,
                        'predicted_sales': round(float(prediction), 2),
                        'confidence': self._calculate_confidence(recent_sales),
                        'method': 'ML'
                    })
                    
                    # Update recent_sales for next prediction
                    recent_sales.append(prediction)
                    if len(recent_sales) > 30:
                        recent_sales.pop(0)
                        
                except Exception as pred_error:
                    print(f"Prediction error: {pred_error}")
                    return self._fallback_prediction(future_days)
            
            return predictions
            
        except Exception as e:
            print(f"Error in ML prediction: {e}")
            return self._fallback_prediction(future_days)
    
    def _get_recent_sales(self):
        """Get recent sales data for lag features"""
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=30)
        
        bills = Bill.objects.filter(
            shop=self.shop,
            date__date__gte=start_date,
            date__date__lte=end_date
        ).extra(
            select={'date_only': 'DATE(date)'}
        ).values('date_only').annotate(
            daily_total=Sum('total')
        ).order_by('date_only')
        
        return [float(bill['daily_total']) for bill in bills]
    
    def _calculate_confidence(self, recent_sales):
        """Calculate prediction confidence based on data quality"""
        if len(recent_sales) < 7:
            return 40
        elif len(recent_sales) < 14:
            return 60
        elif len(recent_sales) < 30:
            return 75
        else:
            # Calculate variance to determine confidence
            variance = np.var(recent_sales)
            mean_sales = np.mean(recent_sales)
            cv = variance / mean_sales if mean_sales > 0 else 1
            
            if cv < 0.3:
                return 90
            elif cv < 0.5:
                return 80
            else:
                return 70
    
    def _fallback_prediction(self, future_days):
        """Fallback prediction when ML fails"""
        # Simple moving average fallback
        recent_sales = self._get_recent_sales()
        
        if not recent_sales:
            avg_sales = 1000  # Default value
        else:
            avg_sales = np.mean(recent_sales)
        
        predictions = []
        for i in range(1, future_days + 1):
            future_date = timezone.now().date() + timedelta(days=i)
            
            # Weekend boost
            multiplier = 1.2 if future_date.weekday() in [4, 5, 6] else 0.9
            prediction = avg_sales * multiplier
            
            predictions.append({
                'date': future_date,
                'predicted_sales': round(float(prediction), 2),
                'confidence': 50,
                'method': 'Statistical'
            })
        
        return predictions


class MLInventoryOptimizer:
    """ML-based Inventory Optimization"""
    
    def __init__(self, shop):
        self.shop = shop
    
    def calculate_optimal_stock(self, product):
        """Calculate optimal stock level using ML"""
        # Get sales history
        sales_data = BillItem.objects.filter(
            product=product,
            bill__date__gte=timezone.now() - timedelta(days=60)
        ).values('bill__date', 'quantity')
        
        if not sales_data:
            return self._default_stock_calculation(product)
        
        # Convert to daily sales and ensure numeric types
        df = pd.DataFrame(sales_data)
        df['date'] = pd.to_datetime(df['bill__date']).dt.date
        df['quantity'] = df['quantity'].astype(float)  # Convert Decimal to float
        daily_sales = df.groupby('date')['quantity'].sum()
        
        if len(daily_sales) < 7:
            return self._default_stock_calculation(product)
        
        # Calculate statistics
        mean_daily_sales = daily_sales.mean()
        std_daily_sales = daily_sales.std()
        
        # Lead time (days to restock)
        lead_time = 7
        
        # Safety stock (2 standard deviations)
        safety_stock = 2 * std_daily_sales * np.sqrt(lead_time)
        
        # Reorder point
        reorder_point = (mean_daily_sales * lead_time) + safety_stock
        
        # Optimal order quantity (EOQ approximation)
        annual_demand = mean_daily_sales * 365
        holding_cost_rate = 0.2  # 20% of product cost
        ordering_cost = 100  # Fixed ordering cost
        
        if product.cost_price and float(product.cost_price) > 0:
            holding_cost = float(product.cost_price) * holding_cost_rate
            eoq = np.sqrt((2 * annual_demand * ordering_cost) / holding_cost)
        else:
            eoq = mean_daily_sales * 30  # 30 days supply
        
        return {
            'reorder_point': max(1, int(reorder_point)),
            'optimal_quantity': max(1, int(eoq)),
            'safety_stock': max(1, int(safety_stock)),
            'daily_demand': round(mean_daily_sales, 2),
            'confidence': self._calculate_inventory_confidence(len(daily_sales))
        }
    
    def _default_stock_calculation(self, product):
        """Default calculation when insufficient data"""
        return {
            'reorder_point': max(5, product.min_stock_alert or 5),
            'optimal_quantity': 20,
            'safety_stock': 5,
            'daily_demand': 1.0,
            'confidence': 30
        }
    
    def _calculate_inventory_confidence(self, data_points):
        """Calculate confidence based on available data"""
        if data_points >= 30:
            return 90
        elif data_points >= 14:
            return 75
        elif data_points >= 7:
            return 60
        else:
            return 40


class MLCustomerSegmentation:
    """ML-based Customer Segmentation"""
    
    def __init__(self, shop):
        self.shop = shop
        self.kmeans = KMeans(n_clusters=3, random_state=42)
    
    def segment_customers(self):
        """Segment customers using RFM analysis"""
        # Get customer data
        customer_data = Bill.objects.filter(
            shop=self.shop,
            date__gte=timezone.now() - timedelta(days=90)
        ).values('customer_name', 'total', 'date')
        
        if not customer_data:
            return []
        
        df = pd.DataFrame(customer_data)
        
        # Convert numeric columns to float
        df['total'] = df['total'].astype(float)
        df['date'] = pd.to_datetime(df['date'])
        
        # Calculate RFM metrics
        current_date = timezone.now().date()
        
        rfm = df.groupby('customer_name').agg({
            'date': lambda x: (current_date - x.max().date()).days,  # Recency
            'total': ['count', 'sum']  # Frequency, Monetary
        }).round(2)
        
        rfm.columns = ['Recency', 'Frequency', 'Monetary']
        
        if len(rfm) < 3:
            return self._simple_segmentation(rfm)
        
        # Normalize data for clustering
        scaler = StandardScaler()
        rfm_scaled = scaler.fit_transform(rfm)
        
        # Perform clustering
        clusters = self.kmeans.fit_predict(rfm_scaled)
        rfm['Cluster'] = clusters
        
        # Analyze clusters
        segments = []
        for cluster in range(3):
            cluster_data = rfm[rfm['Cluster'] == cluster]
            
            segment = {
                'cluster_id': cluster,
                'customer_count': len(cluster_data),
                'avg_recency': round(cluster_data['Recency'].mean(), 1),
                'avg_frequency': round(cluster_data['Frequency'].mean(), 1),
                'avg_monetary': round(cluster_data['Monetary'].mean(), 2),
                'customers': cluster_data.index.tolist()
            }
            
            # Assign segment names based on characteristics
            if segment['avg_recency'] <= 30 and segment['avg_frequency'] >= 3:
                segment['name'] = 'Champions'
                segment['description'] = 'Best customers - high value, frequent buyers'
            elif segment['avg_recency'] <= 60 and segment['avg_monetary'] >= cluster_data['Monetary'].median():
                segment['name'] = 'Loyal Customers'
                segment['description'] = 'Regular customers with good value'
            else:
                segment['name'] = 'At Risk'
                segment['description'] = 'Customers who need attention'
            
            segments.append(segment)
        
        return segments
    
    def _simple_segmentation(self, rfm):
        """Simple segmentation for small datasets"""
        segments = []
        
        for idx, (customer, data) in enumerate(rfm.iterrows()):
            segment = {
                'cluster_id': 0,
                'customer_count': 1,
                'avg_recency': data['Recency'],
                'avg_frequency': data['Frequency'],
                'avg_monetary': data['Monetary'],
                'customers': [customer],
                'name': 'Regular Customer',
                'description': 'Individual customer analysis'
            }
            segments.append(segment)
        
        return segments[:3]  # Return top 3


class MLPriceOptimizer:
    """ML-based Price Optimization"""
    
    def __init__(self, shop):
        self.shop = shop
    
    def optimize_pricing(self, product):
        """Optimize product pricing using demand elasticity"""
        # Get sales data at different price points
        sales_data = BillItem.objects.filter(
            product=product,
            bill__date__gte=timezone.now() - timedelta(days=60)
        ).values('unit_price', 'quantity', 'bill__date')
        
        if not sales_data or len(sales_data) < 5:
            return self._default_pricing(product)
        
        df = pd.DataFrame(sales_data)
        
        # Convert numeric columns to float
        df['unit_price'] = df['unit_price'].astype(float)
        df['quantity'] = df['quantity'].astype(float)
        
        # Group by price and calculate demand
        price_demand = df.groupby('unit_price').agg({
            'quantity': 'sum',
            'bill__date': 'count'
        }).rename(columns={'bill__date': 'transactions'})
        
        if len(price_demand) < 2:
            return self._default_pricing(product)
        
        # Calculate demand elasticity
        prices = price_demand.index.values
        quantities = price_demand['quantity'].values
        
        # Simple linear regression for demand curve
        if len(prices) >= 2:
            try:
                # Log-log regression for elasticity
                log_prices = np.log(prices)
                log_quantities = np.log(quantities + 1)  # Add 1 to avoid log(0)
                
                model = LinearRegression()
                model.fit(log_prices.reshape(-1, 1), log_quantities)
                
                elasticity = model.coef_[0]
                
                # Optimal price calculation
                current_price = float(product.sale_price)
                cost_price = float(product.cost_price or 0)
                
                # Price optimization based on elasticity
                if elasticity < -1:  # Elastic demand
                    optimal_price = current_price * 0.95  # Reduce price
                    reason = "Elastic demand - lower price increases revenue"
                elif elasticity > -0.5:  # Inelastic demand
                    optimal_price = current_price * 1.1  # Increase price
                    reason = "Inelastic demand - can increase price"
                else:
                    optimal_price = current_price  # Keep current price
                    reason = "Current price is optimal"
                
                # Ensure minimum margin
                min_price = cost_price * 1.2 if cost_price > 0 else current_price * 0.8
                optimal_price = max(optimal_price, min_price)
                
                return {
                    'current_price': current_price,
                    'optimal_price': round(optimal_price, 2),
                    'elasticity': round(elasticity, 2),
                    'reason': reason,
                    'confidence': 75,
                    'expected_change': round(((optimal_price - current_price) / current_price) * 100, 1)
                }
                
            except Exception as e:
                return self._default_pricing(product)
        
        return self._default_pricing(product)
    
    def _default_pricing(self, product):
        """Default pricing when ML analysis fails"""
        current_price = float(product.sale_price)
        cost_price = float(product.cost_price or 0)
        
        if cost_price > 0:
            margin = ((current_price - cost_price) / current_price) * 100
            
            if margin < 20:
                optimal_price = cost_price * 1.25
                reason = "Low margin - increase price"
            elif margin > 50:
                optimal_price = current_price * 0.95
                reason = "High margin - competitive pricing"
            else:
                optimal_price = current_price
                reason = "Healthy margin maintained"
        else:
            optimal_price = current_price
            reason = "Insufficient cost data"
        
        return {
            'current_price': current_price,
            'optimal_price': round(optimal_price, 2),
            'elasticity': -1.0,
            'reason': reason,
            'confidence': 50,
            'expected_change': round(((optimal_price - current_price) / current_price) * 100, 1)
        }