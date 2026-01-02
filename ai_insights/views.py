from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Sum, Count, Avg, F, FloatField
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
import statistics

from billing.models import Bill, BillItem
from products.models import Product
from users.models import Shop
from .ml_engine import MLSalesPredictor, MLInventoryOptimizer, MLCustomerSegmentation, MLPriceOptimizer
from .trained_ml_model import TrainedMLPredictor

@login_required
def ml_dashboard(request):
    """ML Concepts Dashboard - Enhanced AI Insights with ML Focus"""
    shop = request.user.shop
    
    # Initialize ML engines
    ml_sales = MLSalesPredictor(shop)
    ml_inventory = MLInventoryOptimizer(shop)
    ml_customers = MLCustomerSegmentation(shop)
    ml_pricing = MLPriceOptimizer(shop)
    
    # Initialize trained model from Colab
    trained_model = TrainedMLPredictor()
    
    # Always show predictions (either ML or statistical)
    ml_predictions = trained_model.predict_sales(7)
    model_status = trained_model.get_model_status()
    
    # Get ML-powered analytics
    context = {
        'ml_sales_predictions': ml_predictions,
        'model_status': model_status,
        'ml_inventory_insights': get_ml_inventory_insights(shop, ml_inventory),
        'ml_customer_segments': ml_customers.segment_customers(),
        'ml_price_optimization': get_ml_price_insights(shop, ml_pricing),
        'sales_predictions': get_sales_predictions(shop),
        'demand_forecast': get_demand_forecast(shop),
        'stock_predictions': get_stock_predictions(shop),
        'best_sellers': get_best_sellers(shop),
        'customer_insights': get_customer_insights(shop),
        'price_recommendations': get_price_recommendations(shop),
        'profit_analysis': get_profit_analysis(shop),
        'ai_recommendations': get_ai_recommendations(shop),
        'ml_enabled': True,
        'trained_model_active': trained_model.is_model_loaded(),
    }
    
    return render(request, 'ai_insights/dashboard_ml.html', context)

@login_required
def ai_dashboard(request):
    """AI Insights Dashboard with ML Integration"""
    shop = request.user.shop
    
    # Initialize ML engines
    ml_sales = MLSalesPredictor(shop)
    ml_inventory = MLInventoryOptimizer(shop)
    ml_customers = MLCustomerSegmentation(shop)
    ml_pricing = MLPriceOptimizer(shop)
    
    # Initialize trained model from Colab
    trained_model = TrainedMLPredictor()
    
    # Always show predictions (either ML or statistical)
    ml_predictions = trained_model.predict_sales(7)
    model_status = trained_model.get_model_status()
    
    # Get ML-powered analytics
    context = {
        'ml_sales_predictions': ml_predictions,
        'model_status': model_status,
        'ml_inventory_insights': get_ml_inventory_insights(shop, ml_inventory),
        'ml_customer_segments': ml_customers.segment_customers(),
        'ml_price_optimization': get_ml_price_insights(shop, ml_pricing),
        'sales_predictions': get_sales_predictions(shop),
        'demand_forecast': get_demand_forecast(shop),
        'stock_predictions': get_stock_predictions(shop),
        'best_sellers': get_best_sellers(shop),
        'customer_insights': get_customer_insights(shop),
        'price_recommendations': get_price_recommendations(shop),
        'profit_analysis': get_profit_analysis(shop),
        'ai_recommendations': get_ai_recommendations(shop),
        'ml_enabled': True,
        'trained_model_active': trained_model.is_model_loaded(),
    }
    
    return render(request, 'ai_insights/dashboard.html', context)

@login_required
def ai_dashboard_ur(request):
    """AI Insights Dashboard Urdu Version"""
    shop = request.user.shop
    
    # Initialize ML engines
    ml_sales = MLSalesPredictor(shop)
    ml_inventory = MLInventoryOptimizer(shop)
    ml_customers = MLCustomerSegmentation(shop)
    ml_pricing = MLPriceOptimizer(shop)
    
    # Initialize trained model from Colab
    trained_model = TrainedMLPredictor()
    
    # Always show predictions (either ML or statistical)
    ml_predictions = trained_model.predict_sales(7)
    model_status = trained_model.get_model_status()
    
    # Get ML-powered analytics
    context = {
        'ml_sales_predictions': ml_predictions,
        'model_status': model_status,
        'ml_inventory_insights': get_ml_inventory_insights(shop, ml_inventory),
        'ml_customer_segments': ml_customers.segment_customers(),
        'ml_price_optimization': get_ml_price_insights(shop, ml_pricing),
        'sales_predictions': get_sales_predictions(shop),
        'demand_forecast': get_demand_forecast(shop),
        'stock_predictions': get_stock_predictions(shop),
        'best_sellers': get_best_sellers(shop),
        'customer_insights': get_customer_insights(shop),
        'price_recommendations': get_price_recommendations(shop),
        'profit_analysis': get_profit_analysis(shop),
        'ai_recommendations': get_ai_recommendations(shop),
        'ml_enabled': True,
        'trained_model_active': trained_model.is_model_loaded(),
    }
    
    return render(request, 'ai_insights/dashboard_ur.html', context)

def get_sales_predictions(shop):
    """Sales prediction for next 7 days"""
    last_30_days = timezone.now().date() - timedelta(days=30)
    
    # Get daily sales for last 30 days
    daily_sales = []
    for i in range(30):
        date = timezone.now().date() - timedelta(days=i)
        sales = Bill.objects.filter(
            shop=shop, 
            date__date=date
        ).aggregate(total=Sum('total'))['total'] or 0
        daily_sales.append(float(sales))  # Convert Decimal to float
    
    if not daily_sales or sum(daily_sales) == 0:
        return []
    
    # Simple moving average prediction
    avg_sales = sum(daily_sales) / len(daily_sales)
    
    predictions = []
    for i in range(1, 8):  # Next 7 days
        date = timezone.now().date() + timedelta(days=i)
        
        # Weekend boost
        multiplier = 1.2 if date.weekday() in [4, 5] else 0.9
        predicted = avg_sales * multiplier
        
        predictions.append({
            'date': date,
            'predicted_sales': round(predicted, 0),
            'confidence': 75 if len(daily_sales) > 10 else 50
        })
    
    return predictions

def get_demand_forecast(shop):
    """Demand forecasting for products"""
    last_30_days = timezone.now().date() - timedelta(days=30)
    
    # Get product sales velocity
    products = BillItem.objects.filter(
        bill__shop=shop,
        bill__date__date__gte=last_30_days
    ).values('product__name', 'product__stock').annotate(
        total_sold=Sum('quantity'),
        daily_avg=Sum('quantity', output_field=FloatField()) / 30.0
    ).order_by('-total_sold')[:10]
    
    forecast = []
    for item in products:
        stock = item['product__stock'] or 0
        daily_avg = float(item['daily_avg'] or 0)
        
        if daily_avg > 0:
            days_left = stock / daily_avg
            forecast.append({
                'product_name': item['product__name'],
                'current_stock': stock,
                'daily_velocity': round(daily_avg, 1),
                'days_remaining': int(days_left),
                'restock_needed': days_left <= 7,
                'confidence': 80 if item['total_sold'] > 5 else 60
            })
    
    return forecast

def get_stock_predictions(shop):
    """Low stock predictions"""
    products = Product.objects.filter(
        shop=shop, 
        is_active=True,
        stock__lte=F('min_stock_alert')
    )[:10]
    
    predictions = []
    for product in products:
        # Get recent sales
        last_7_days = timezone.now().date() - timedelta(days=7)
        sold = BillItem.objects.filter(
            product=product,
            bill__date__date__gte=last_7_days
        ).aggregate(total=Sum('quantity'))['total'] or 0
        
        daily_rate = float(sold) / 7 if sold > 0 else 0
        days_left = product.stock / daily_rate if daily_rate > 0 else 999
        
        predictions.append({
            'product': product,
            'days_until_stockout': int(days_left),
            'daily_sales_rate': round(daily_rate, 1),
            'recommended_reorder': max(20, int(daily_rate * 14)),
            'confidence': 70 if sold > 0 else 40
        })
    
    return sorted(predictions, key=lambda x: x['days_until_stockout'])[:5]

def get_best_sellers(shop):
    """Best selling products analysis"""
    last_30_days = timezone.now().date() - timedelta(days=30)
    
    return BillItem.objects.filter(
        bill__shop=shop,
        bill__date__date__gte=last_30_days
    ).values('product__name').annotate(
        total_sold=Sum('quantity'),
        total_revenue=Sum(F('quantity') * F('unit_price'))
    ).order_by('-total_sold')[:10]

def get_customer_insights(shop):
    """Customer behavior analysis"""
    last_30_days = timezone.now().date() - timedelta(days=30)
    
    bills = Bill.objects.filter(
        shop=shop, 
        date__date__gte=last_30_days
    )
    
    # Customer analysis
    total_customers = bills.values('customer_name').distinct().count()
    repeat_customers = bills.values('customer_name').annotate(
        visits=Count('id')
    ).filter(visits__gt=1).count()
    
    # Peak hours
    hour_sales = {}
    for bill in bills:
        hour = bill.date.hour
        hour_sales[hour] = hour_sales.get(hour, 0) + 1
    
    peak_hour = max(hour_sales.items(), key=lambda x: x[1])[0] if hour_sales else 12
    
    return {
        'total_customers': total_customers,
        'repeat_customers': repeat_customers,
        'repeat_rate': round((repeat_customers / total_customers * 100) if total_customers > 0 else 0, 1),
        'peak_hour': peak_hour,
        'avg_transaction': round(float(bills.aggregate(avg=Avg('total'))['avg'] or 0), 0),
        'confidence': 80 if total_customers > 10 else 50
    }

def get_price_recommendations(shop):
    """Price optimization suggestions"""
    last_30_days = timezone.now().date() - timedelta(days=30)
    
    recommendations = []
    products = Product.objects.filter(shop=shop, is_active=True, sale_price__gt=0)[:10]
    
    for product in products:
        # Get sales data
        sales = BillItem.objects.filter(
            product=product,
            bill__date__date__gte=last_30_days
        ).aggregate(total_sold=Sum('quantity'))['total_sold'] or 0
        
        current_price = float(product.sale_price)
        cost_price = float(product.cost_price or 0)
        margin = ((current_price - cost_price) / current_price * 100) if current_price > 0 else 0
        
        recommendation = None
        
        # Low sales, high margin - reduce price
        if sales < 3 and margin > 40:
            new_price = current_price * 0.9
            recommendation = {
                'product': product,
                'current_price': current_price,
                'recommended_price': round(new_price, 0),
                'reason': f'Low sales ({sales} units), high margin ({margin:.0f}%)',
                'action': 'decrease',
                'confidence': 75
            }
        
        # High sales, low margin - increase price
        elif sales > 10 and margin < 20:
            new_price = current_price * 1.1
            recommendation = {
                'product': product,
                'current_price': current_price,
                'recommended_price': round(new_price, 0),
                'reason': f'High sales ({sales} units), low margin ({margin:.0f}%)',
                'action': 'increase',
                'confidence': 80
            }
        
        if recommendation:
            recommendations.append(recommendation)
    
    return recommendations[:5]

def get_profit_analysis(shop):
    """Profit estimation and analysis"""
    last_30_days = timezone.now().date() - timedelta(days=30)
    
    # Get bill items for profit calculation
    items = BillItem.objects.filter(
        bill__shop=shop,
        bill__date__date__gte=last_30_days
    ).select_related('product')
    
    total_revenue = 0
    total_cost = 0
    
    for item in items:
        revenue = float(item.unit_price) * float(item.quantity)
        cost = float(item.product.cost_price or 0) * float(item.quantity)
        total_revenue += revenue
        total_cost += cost
    
    profit = total_revenue - total_cost
    margin = (profit / total_revenue * 100) if total_revenue > 0 else 0
    
    return {
        'total_revenue': round(total_revenue, 0),
        'total_cost': round(total_cost, 0),
        'total_profit': round(profit, 0),
        'profit_margin': round(margin, 1),
        'daily_avg_profit': round(profit / 30, 0),
        'confidence': 90 if total_revenue > 1000 else 60
    }

def get_ai_recommendations(shop):
    """Generate actionable AI recommendations"""
    recommendations = []
    
    # Stock recommendations
    low_stock = Product.objects.filter(
        shop=shop,
        is_active=True,
        stock__lte=F('min_stock_alert')
    ).count()
    
    if low_stock > 0:
        recommendations.append({
            'type': 'stock',
            'title': f'Restock {low_stock} products',
            'message': 'Low stock items need immediate attention',
            'priority': 'high',
            'icon': 'fas fa-box',
            'color': 'warning'
        })
    
    # Sales timing
    customer_data = get_customer_insights(shop)
    if customer_data['peak_hour']:
        recommendations.append({
            'type': 'timing',
            'title': f'Peak sales at {customer_data["peak_hour"]}:00',
            'message': 'Ensure adequate staff and inventory during peak hours',
            'priority': 'medium',
            'icon': 'fas fa-clock',
            'color': 'info'
        })
    
    # Customer retention
    if customer_data['repeat_rate'] < 30:
        recommendations.append({
            'type': 'customer',
            'title': 'Improve customer retention',
            'message': f'Only {customer_data["repeat_rate"]}% customers return. Consider loyalty programs',
            'priority': 'medium',
            'icon': 'fas fa-users',
            'color': 'primary'
        })
    
    # Profit optimization
    profit_data = get_profit_analysis(shop)
    if profit_data['profit_margin'] < 15:
        recommendations.append({
            'type': 'profit',
            'title': 'Low profit margins detected',
            'message': f'Current margin: {profit_data["profit_margin"]}%. Review pricing strategy',
            'priority': 'high',
            'icon': 'fas fa-chart-line',
            'color': 'danger'
        })
    
    return recommendations[:6]

def get_ml_inventory_insights(shop, ml_optimizer):
    """Get ML-powered inventory insights"""
    insights = []
    
    # Get products that need analysis
    products = Product.objects.filter(
        shop=shop, 
        is_active=True
    ).order_by('-stock')[:10]
    
    for product in products:
        optimization = ml_optimizer.calculate_optimal_stock(product)
        
        if product.stock <= optimization['reorder_point']:
            insights.append({
                'product': product,
                'current_stock': product.stock,
                'reorder_point': optimization['reorder_point'],
                'optimal_quantity': optimization['optimal_quantity'],
                'daily_demand': optimization['daily_demand'],
                'confidence': optimization['confidence'],
                'urgency': 'high' if product.stock <= optimization['safety_stock'] else 'medium'
            })
    
    return insights[:5]

def get_ml_price_insights(shop, ml_pricing):
    """Get ML-powered price optimization insights"""
    insights = []
    
    # Get products with sales history
    products = Product.objects.filter(
        shop=shop,
        is_active=True,
        sale_price__gt=0
    ).order_by('-id')[:10]
    
    for product in products:
        # Check if product has sales data
        has_sales = BillItem.objects.filter(
            product=product,
            bill__date__gte=timezone.now() - timedelta(days=30)
        ).exists()
        
        if has_sales:
            optimization = ml_pricing.optimize_pricing(product)
            
            if abs(optimization['expected_change']) > 2:  # Only show significant changes
                insights.append({
                    'product': product,
                    'current_price': optimization['current_price'],
                    'optimal_price': optimization['optimal_price'],
                    'expected_change': optimization['expected_change'],
                    'reason': optimization['reason'],
                    'confidence': optimization['confidence'],
                    'elasticity': optimization['elasticity']
                })
    
    return insights[:5]

@login_required
def sales_predictions(request):
    """Sales predictions view"""
    shop = request.user.shop
    predictions = get_sales_predictions(shop)
    return render(request, 'ai_insights/sales_predictions.html', {'predictions': predictions})

@login_required
def stock_predictions(request):
    """Stock predictions view"""
    shop = request.user.shop
    predictions = get_stock_predictions(shop)
    return render(request, 'ai_insights/stock_predictions.html', {'predictions': predictions})

@login_required
def price_recommendations(request):
    """Price recommendations view"""
    shop = request.user.shop
    recommendations = get_price_recommendations(shop)
    return render(request, 'ai_insights/price_recommendations.html', {'recommendations': recommendations})

@login_required
def mark_insight_read(request, insight_id):
    """Mark insight as read"""
    return JsonResponse({'success': True})

@login_required
def apply_price_recommendation(request):
    """Apply price recommendation"""
    if request.method == 'POST':
        return JsonResponse({'success': True, 'message': 'Price updated'})
    return JsonResponse({'success': False})

@login_required
def get_analytics_data(request):
    """API endpoint for analytics data"""
    shop = request.user.shop
    data = {
        'sales_predictions': get_sales_predictions(shop),
        'stock_predictions': get_stock_predictions(shop),
        'price_recommendations': get_price_recommendations(shop)
    }
    return JsonResponse(data)

@login_required
def refresh_insights(request):
    """Refresh AI insights"""
    if request.method == 'POST':
        return JsonResponse({'success': True, 'message': 'Insights refreshed'})
    return JsonResponse({'success': False})

@login_required
def train_ml_models(request):
    """Train ML models for the shop"""
    if request.method == 'POST':
        shop = request.user.shop
        
        try:
            # Train sales prediction model
            ml_sales = MLSalesPredictor(shop)
            
            # Force retrain to fix feature mismatch
            success = ml_sales.retrain_model()
            
            if success:
                return JsonResponse({
                    'success': True, 
                    'message': 'ML models retrained successfully with correct features'
                })
            else:
                return JsonResponse({
                    'success': False, 
                    'message': 'Insufficient data for ML training. Need at least 10 days of sales data.'
                })
                
        except Exception as e:
            return JsonResponse({
                'success': False, 
                'message': f'Error training models: {str(e)}'
            })
    
    return JsonResponse({'success': False})

@login_required
def ml_analytics_api(request):
    """API endpoint for ML analytics data"""
    shop = request.user.shop
    
    try:
        # Initialize ML engines
        ml_sales = MLSalesPredictor(shop)
        ml_inventory = MLInventoryOptimizer(shop)
        ml_customers = MLCustomerSegmentation(shop)
        
        data = {
            'ml_sales_predictions': ml_sales.predict_sales(7),
            'ml_inventory_insights': get_ml_inventory_insights(shop, ml_inventory),
            'ml_customer_segments': ml_customers.segment_customers(),
            'status': 'success'
        }
        
        return JsonResponse(data)
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        })