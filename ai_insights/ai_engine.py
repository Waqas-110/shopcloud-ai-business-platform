from datetime import datetime, timedelta
from django.db.models import Sum, Count, Avg
from billing.models import Bill, BillItem
from products.models import Product
from .models import AIInsight
from .ml_models import load_models
import logging

logger = logging.getLogger(__name__)

class AIInsightEngine:
    def __init__(self, shop):
        self.shop = shop
        try:
            self.sales_predictor, self.stock_optimizer, self.price_optimizer = load_models()
        except Exception as e:
            logger.error(f"Error loading ML models: {e}")
            self.sales_predictor = None
            self.stock_optimizer = None
            self.price_optimizer = None
    
    def generate_comprehensive_insights(self):
        """Generate all types of AI insights"""
        # Clear old insights
        AIInsight.objects.filter(shop=self.shop).delete()
        
        insights = []
        
        # 1. Sales Performance Analysis
        insights.extend(self._analyze_sales_performance())
        
        # 2. Stock Management Insights
        insights.extend(self._analyze_stock_levels())
        
        # 3. Price Optimization
        insights.extend(self._analyze_pricing())
        
        # 4. Customer Behavior Analysis
        insights.extend(self._analyze_customer_behavior())
        
        # 5. Product Performance
        insights.extend(self._analyze_product_performance())
        
        # Save insights to database
        for insight_data in insights:
            AIInsight.objects.create(
                shop=self.shop,
                insight_type=insight_data['type'],
                title=insight_data['title'],
                message=insight_data['message'],
                priority=insight_data['priority'],
                confidence_score=insight_data.get('confidence', 0.8)
            )
        
        return insights
    
    def _analyze_sales_performance(self):
        """Analyze sales trends and performance"""
        insights = []
        
        # Get sales data
        last_30_days = datetime.now().date() - timedelta(days=30)
        last_7_days = datetime.now().date() - timedelta(days=7)
        
        bills_30d = Bill.objects.filter(shop=self.shop, date__date__gte=last_30_days)
        bills_7d = Bill.objects.filter(shop=self.shop, date__date__gte=last_7_days)
        
        if bills_30d.exists():
            total_sales_30d = bills_30d.aggregate(Sum('total'))['total__sum'] or 0
            total_sales_7d = bills_7d.aggregate(Sum('total'))['total__sum'] or 0
            
            avg_daily_30d = total_sales_30d / 30
            avg_daily_7d = total_sales_7d / 7 if bills_7d.exists() else 0
            
            # Growth analysis
            if avg_daily_7d > avg_daily_30d * 1.1:
                insights.append({
                    'type': 'sales_growth',
                    'title': 'Sales Growth Detected',
                    'message': f'Your recent sales (₨{avg_daily_7d:.0f}/day) are {((avg_daily_7d/avg_daily_30d-1)*100):.1f}% higher than your 30-day average. Great momentum!',
                    'priority': 'high',
                    'confidence': 0.9
                })
            elif avg_daily_7d < avg_daily_30d * 0.9:
                insights.append({
                    'type': 'sales_decline',
                    'title': 'Sales Decline Alert',
                    'message': f'Recent sales (₨{avg_daily_7d:.0f}/day) are down {((1-avg_daily_7d/avg_daily_30d)*100):.1f}%. Consider promotional campaigns.',
                    'priority': 'critical',
                    'confidence': 0.85
                })
            
            # Performance benchmarks
            if avg_daily_30d > 2000:
                insights.append({
                    'type': 'performance',
                    'title': 'Excellent Performance',
                    'message': f'Your daily average of ₨{avg_daily_30d:.0f} is excellent! Consider expanding your product range or opening new locations.',
                    'priority': 'medium',
                    'confidence': 0.8
                })
        
        return insights
    
    def _analyze_stock_levels(self):
        """Analyze inventory and stock management"""
        insights = []
        
        products = Product.objects.filter(shop=self.shop, is_active=True)
        
        # Low stock alerts
        low_stock = products.filter(stock__lte=5)
        if low_stock.exists():
            insights.append({
                'type': 'stock_alert',
                'title': f'{low_stock.count()} Products Low on Stock',
                'message': f'Products running low: {", ".join([p.name for p in low_stock[:3]])}{"..." if low_stock.count() > 3 else ""}',
                'priority': 'critical',
                'confidence': 1.0
            })
        
        # Overstock analysis
        last_30_days = datetime.now().date() - timedelta(days=30)
        for product in products.filter(stock__gt=50):
            sold_qty = BillItem.objects.filter(
                product=product,
                bill__date__date__gte=last_30_days
            ).aggregate(Sum('quantity'))['quantity__sum'] or 0
            
            if sold_qty == 0 and product.stock > 20:
                insights.append({
                    'type': 'overstock',
                    'title': 'Overstock Alert',
                    'message': f'{product.name} has {product.stock} units but no sales in 30 days. Consider promotions or price reduction.',
                    'priority': 'medium',
                    'confidence': 0.9
                })
        
        return insights
    
    def _analyze_pricing(self):
        """Analyze pricing strategy"""
        insights = []
        
        products = Product.objects.filter(shop=self.shop, is_active=True)
        
        # Low margin products
        low_margin = []
        high_margin = []
        
        for product in products:
            if product.cost_price and product.sale_price:
                margin_pct = ((product.sale_price - product.cost_price) / product.sale_price) * 100
                
                if margin_pct < 15:
                    low_margin.append(product.name)
                elif margin_pct > 60:
                    high_margin.append(product.name)
        
        if low_margin:
            insights.append({
                'type': 'pricing_alert',
                'title': 'Low Margin Products Detected',
                'message': f'{len(low_margin)} products have margins below 15%: {", ".join(low_margin[:3])}. Consider price adjustments.',
                'priority': 'high',
                'confidence': 0.95
            })
        
        if high_margin:
            insights.append({
                'type': 'pricing_opportunity',
                'title': 'High Margin Products',
                'message': f'{len(high_margin)} products have excellent margins (>60%). Great pricing strategy!',
                'priority': 'low',
                'confidence': 0.8
            })
        
        return insights
    
    def _analyze_customer_behavior(self):
        """Analyze customer purchasing patterns"""
        insights = []
        
        last_30_days = datetime.now().date() - timedelta(days=30)
        bills = Bill.objects.filter(shop=self.shop, date__date__gte=last_30_days)
        
        if bills.exists():
            # Average transaction value
            avg_transaction = bills.aggregate(Avg('total'))['total__avg'] or 0
            
            # Customer frequency
            unique_customers = bills.exclude(customer_name='').values('customer_name').distinct().count()
            total_transactions = bills.count()
            
            if avg_transaction > 500:
                insights.append({
                    'type': 'customer_value',
                    'title': 'High-Value Customers',
                    'message': f'Your average transaction value is ₨{avg_transaction:.0f}. Focus on customer retention strategies.',
                    'priority': 'medium',
                    'confidence': 0.8
                })
            
            if unique_customers > 0:
                repeat_rate = (total_transactions - unique_customers) / unique_customers
                if repeat_rate > 1.5:
                    insights.append({
                        'type': 'customer_loyalty',
                        'title': 'Strong Customer Loyalty',
                        'message': f'Customers are making {repeat_rate:.1f} repeat purchases on average. Excellent retention!',
                        'priority': 'low',
                        'confidence': 0.85
                    })
        
        return insights
    
    def _analyze_product_performance(self):
        """Analyze individual product performance"""
        insights = []
        
        last_30_days = datetime.now().date() - timedelta(days=30)
        
        # Best sellers
        best_sellers = BillItem.objects.filter(
            bill__shop=self.shop,
            bill__date__date__gte=last_30_days
        ).values('product__name').annotate(
            total_sold=Sum('quantity'),
            total_revenue=Sum('total_price')
        ).order_by('-total_sold')[:3]
        
        if best_sellers:
            top_product = best_sellers[0]
            insights.append({
                'type': 'product_performance',
                'title': 'Top Performing Product',
                'message': f'{top_product["product__name"]} is your star performer with {top_product["total_sold"]} units sold (₨{top_product["total_revenue"]:.0f} revenue).',
                'priority': 'medium',
                'confidence': 0.9
            })
        
        # Slow movers
        slow_movers = BillItem.objects.filter(
            bill__shop=self.shop,
            bill__date__date__gte=last_30_days
        ).values('product__name').annotate(
            total_sold=Sum('quantity')
        ).filter(total_sold__lte=2)
        
        if slow_movers.exists():
            insights.append({
                'type': 'product_alert',
                'title': 'Slow Moving Products',
                'message': f'{slow_movers.count()} products have very low sales. Consider bundling or promotional offers.',
                'priority': 'medium',
                'confidence': 0.8
            })
        
        return insights
    
    def get_sales_predictions(self):
        """Get ML-based sales predictions"""
        if not self.sales_predictor:
            return self._get_simple_predictions()
        
        try:
            # Get historical data
            last_60_days = datetime.now().date() - timedelta(days=60)
            bills = Bill.objects.filter(shop=self.shop, date__date__gte=last_60_days)
            
            bills_data = list(bills.values('date', 'total'))
            
            if len(bills_data) > 10:  # Need minimum data for training
                self.sales_predictor.train(bills_data)
                return self.sales_predictor.predict_next_days(7)
            else:
                return self._get_simple_predictions()
        
        except Exception as e:
            logger.error(f"Error in sales prediction: {e}")
            return self._get_simple_predictions()
    
    def _get_simple_predictions(self):
        """Simple prediction fallback"""
        last_30_days = datetime.now().date() - timedelta(days=30)
        bills = Bill.objects.filter(shop=self.shop, date__date__gte=last_30_days)
        
        if bills.exists():
            avg_daily = (bills.aggregate(Sum('total'))['total__sum'] or 0) / 30
        else:
            avg_daily = 1000  # Default assumption
        
        predictions = []
        for i in range(1, 8):
            future_date = datetime.now().date() + timedelta(days=i)
            # Add some variation
            variation = 1 + (i % 3 - 1) * 0.1  # ±10% variation
            predicted_sales = avg_daily * variation
            
            predictions.append({
                'date': future_date,
                'predicted_sales': max(0, predicted_sales),
                'confidence': 0.7
            })
        
        return predictions
    
    def get_stock_predictions(self):
        """Get stock-out predictions"""
        if not self.stock_optimizer:
            return []
        
        predictions = []
        products = Product.objects.filter(shop=self.shop, is_active=True, stock__gt=0)
        
        last_30_days = datetime.now().date() - timedelta(days=30)
        
        for product in products:
            # Get sales data for this product
            sales_data = list(BillItem.objects.filter(
                product=product,
                bill__date__date__gte=last_30_days
            ).values('quantity', 'bill__date'))
            
            # Format for ML model
            formatted_sales = [
                {'quantity': item['quantity'], 'date': item['bill__date'].strftime('%Y-%m-%d')}
                for item in sales_data
            ]
            
            product_data = {
                'id': product.id,
                'name': product.name,
                'stock': product.stock,
                'min_stock_alert': getattr(product, 'min_stock_alert', 10)
            }
            
            prediction = self.stock_optimizer.predict_stockout(product_data, formatted_sales)
            if prediction:
                predictions.append(prediction)
        
        return sorted(predictions, key=lambda x: x['days_until_stockout'])[:10]
    
    def get_price_recommendations(self):
        """Get AI-based price recommendations"""
        if not self.price_optimizer:
            return []
        
        recommendations = []
        products = Product.objects.filter(shop=self.shop, is_active=True)
        
        last_30_days = datetime.now().date() - timedelta(days=30)
        
        for product in products[:10]:  # Limit to 10 products
            # Get sales data
            sales_data = list(BillItem.objects.filter(
                product=product,
                bill__date__date__gte=last_30_days
            ).values('quantity', 'total_price'))
            
            product_data = {
                'id': product.id,
                'name': product.name,
                'sale_price': product.sale_price,
                'cost_price': product.cost_price or 0
            }
            
            recommendation = self.price_optimizer.analyze_price_elasticity(product_data, sales_data)
            if recommendation['price_change'] != 0:  # Only include if there's a change
                recommendations.append(recommendation)
        
        return recommendations[:5]  # Return top 5 recommendations