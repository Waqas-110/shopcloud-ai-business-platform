from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from datetime import datetime, timedelta
from django.db.models import Sum, Count, F
from billing.models import Bill, BillItem
from products.models import Product
from shopcloud.language_utils import get_user_language, get_template_name
from .utils import (
    get_sales_report, get_top_products, get_category_sales,
    get_daily_sales_chart_data, get_payment_method_stats,
    get_hourly_sales_pattern, calculate_daily_analytics
)
import json
from django.core.serializers.json import DjangoJSONEncoder
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO
from django.db import models

@login_required
def main_dashboard(request):
    shop = request.user.shop
    today = timezone.now().date()
    
    # Calculate today's analytics
    calculate_daily_analytics(shop, today)
    
    # Get today's summary
    today_report = get_sales_report(shop, today, today)
    
    # Get this week's data
    week_start = today - timedelta(days=today.weekday())
    week_report = get_sales_report(shop, week_start, today)
    
    # Get this month's data
    month_start = today.replace(day=1)
    month_report = get_sales_report(shop, month_start, today)
    
    # Get top products (last 7 days)
    week_ago = today - timedelta(days=7)
    top_products = get_top_products(shop, week_ago, today, 5)
    
    # Get low stock products
    low_stock_products = Product.objects.filter(
        shop=shop,
        stock__lte=models.F('min_stock_alert'),
        is_active=True
    )[:5]
    
    context = {
        'today_report': today_report,
        'week_report': week_report,
        'month_report': month_report,
        'top_products': top_products,
        'low_stock_products': low_stock_products,
    }
    
    language = get_user_language(request)
    template_name = get_template_name('dashboard/main.html', language)
    return render(request, template_name, context)

@login_required
def reports_dashboard(request):
    """Main reports dashboard"""
    return render(request, 'dashboard/reports.html')

@login_required
def sales_report(request):
    """Sales report with date filtering"""
    shop = request.user.shop
    
    # Get date range from request
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    if not start_date or not end_date:
        # Default to last 30 days
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=30)
    else:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    # Get sales report
    report = get_sales_report(shop, start_date, end_date)
    
    # Get top products
    top_products = get_top_products(shop, start_date, end_date, 10)
    
    # Get category sales
    category_sales = get_category_sales(shop, start_date, end_date)
    
    # Get payment method stats
    payment_stats = get_payment_method_stats(shop, start_date, end_date)
    
    context = {
        'report': report,
        'top_products': top_products,
        'category_sales': category_sales,
        'payment_stats': payment_stats,
        'start_date': start_date,
        'end_date': end_date,
    }
    
    return render(request, 'dashboard/sales_report.html', context)

@login_required
def chart_data_api(request):
    """API endpoint for chart data"""
    shop = request.user.shop
    chart_type = request.GET.get('type', 'daily_sales')
    days = int(request.GET.get('days', 30))
    
    if chart_type == 'daily_sales':
        data = get_daily_sales_chart_data(shop, days)
    elif chart_type == 'hourly_pattern':
        date_str = request.GET.get('date')
        if date_str:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
        else:
            date = timezone.now().date()
        data = list(get_hourly_sales_pattern(shop, date))
    else:
        data = []
    
    return JsonResponse(data, safe=False, encoder=DjangoJSONEncoder)

@login_required
def export_sales_report(request):
    """Export sales report as PDF"""
    shop = request.user.shop
    
    # Get date range
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    if not start_date or not end_date:
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=30)
    else:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    # Create PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title = Paragraph(f"<b>{shop.name} - Sales Report</b>", styles['Title'])
    story.append(title)
    story.append(Spacer(1, 12))
    
    # Date range
    date_range = Paragraph(f"Period: {start_date} to {end_date}", styles['Normal'])
    story.append(date_range)
    story.append(Spacer(1, 12))
    
    # Get report data
    report = get_sales_report(shop, start_date, end_date)
    top_products = get_top_products(shop, start_date, end_date, 10)
    
    # Summary table
    summary_data = [
        ['Metric', 'Value'],
        ['Total Sales', f"Rs. {report['total_sales']:,.2f}"],
        ['Total Bills', f"{report['total_bills']:,}"],
        ['Total Profit', f"Rs. {report['total_profit']:,.2f}"],
        ['Profit Margin', f"{report['profit_margin']:.1f}%"],
    ]
    
    summary_table = Table(summary_data)
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(summary_table)
    story.append(Spacer(1, 20))
    
    # Top products table
    if top_products:
        products_title = Paragraph("<b>Top Selling Products</b>", styles['Heading2'])
        story.append(products_title)
        story.append(Spacer(1, 12))
        
        products_data = [['Product', 'Quantity Sold', 'Revenue']]
        for product in top_products:
            products_data.append([
                product['product__name'],
                str(product['total_quantity']),
                f"Rs. {product['total_revenue']:,.2f}"
            ])
        
        products_table = Table(products_data)
        products_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(products_table)
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    
    # Return PDF response
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="sales_report_{start_date}_to_{end_date}.pdf"'
    
    return response

@login_required
def ai_dashboard(request):
    """AI Insights Dashboard with comprehensive analytics"""
    shop = request.user.shop
    
    # Get AI insights and analytics
    insights = generate_ai_insights(shop)
    sales_predictions = get_sales_predictions(shop)
    demand_forecast = get_demand_forecast(shop)
    customer_insights = get_customer_insights(shop)
    profit_analysis = get_profit_analysis(shop)
    best_sellers = get_best_selling_products(shop)
    
    context = {
        'insights': insights,
        'unread_insights': len([i for i in insights if not i.get('read', False)]),
        'sales_predictions': sales_predictions,
        'stock_predictions': [d for d in demand_forecast if d.get('restock_needed')],
        'demand_forecast': demand_forecast,
        'customer_insights': customer_insights,
        'profit_analysis': profit_analysis,
        'best_sellers': best_sellers,
        'price_recommendations': []  # Placeholder for future implementation
    }
    
    return render(request, 'ai_insights/dashboard.html', context)

def generate_ai_insights(shop):
    """Generate AI-powered business insights"""
    insights = []
    today = timezone.now().date()
    last_30_days = today - timedelta(days=30)
    
    # Get recent sales data
    recent_bills = Bill.objects.filter(
        shop=shop,
        date__date__gte=last_30_days
    )
    
    # Low stock alerts
    low_stock_products = Product.objects.filter(
        shop=shop,
        stock__lte=models.F('min_stock_alert'),
        is_active=True
    )
    
    for product in low_stock_products[:3]:
        insights.append({
            'title': f'Low Stock Alert: {product.name}',
            'message': f'Only {product.stock} units left. Consider restocking soon.',
            'insight_type': 'stock_alert',
            'priority': 'high' if product.stock <= 5 else 'medium',
            'created_at': timezone.now(),
            'read': False
        })
    
    # Sales trend analysis
    if recent_bills.exists():
        total_sales = recent_bills.aggregate(
            total=Sum('total')
        )['total'] or 0
        
        avg_daily_sales = total_sales / 30
        
        if avg_daily_sales > 1000:
            insights.append({
                'title': 'Strong Sales Performance',
                'message': f'Your daily average of ₨{avg_daily_sales:.0f} is excellent. Consider expanding inventory.',
                'insight_type': 'sales_tip',
                'priority': 'low',
                'created_at': timezone.now(),
                'read': False
            })
    
    return insights

def get_sales_predictions(shop):
    """Generate sales predictions for next 7 days"""
    predictions = []
    today = timezone.now().date()
    last_30_days = today - timedelta(days=30)
    
    # Get historical sales data
    daily_sales = Bill.objects.filter(
        shop=shop,
        date__date__gte=last_30_days
    ).extra(
        select={'day': 'date(date)'}
    ).values('day').annotate(
        total_sales=Sum('total')
    ).order_by('day')
    
    if daily_sales:
        # Simple moving average prediction
        sales_values = [float(day['total_sales'] or 0) for day in daily_sales]
        avg_sales = sum(sales_values) / len(sales_values)
        
        for i in range(7):
            prediction_date = today + timedelta(days=i+1)
            # Add some variance based on day of week
            day_multiplier = 1.2 if prediction_date.weekday() in [4, 5, 6] else 0.9
            predicted_amount = float(avg_sales) * day_multiplier
            
            predictions.append({
                'date': prediction_date,
                'predicted_sales': predicted_amount,
                'confidence': min(85, 60 + len(sales_values))  # Higher confidence with more data
            })
    
    return predictions

def get_demand_forecast(shop):
    """Analyze product demand and forecast restocking needs"""
    forecast = []
    last_30_days = timezone.now().date() - timedelta(days=30)
    
    # Get products with sales history
    products_with_sales = BillItem.objects.filter(
        bill__shop=shop,
        bill__date__date__gte=last_30_days
    ).values('product').annotate(
        total_sold=Sum('quantity'),
        avg_daily=Sum('quantity') / 30.0
    )
    
    for item in products_with_sales:
        try:
            product = Product.objects.get(id=item['product'])
            daily_velocity = item['avg_daily']
            current_stock = product.stock
            
            if daily_velocity > 0:
                days_remaining = float(current_stock) / float(daily_velocity)
                restock_needed = days_remaining <= 7  # Restock if less than 7 days left
                
                forecast.append({
                    'product_name': product.name,
                    'current_stock': current_stock,
                    'daily_velocity': round(daily_velocity, 1),
                    'days_remaining': int(days_remaining),
                    'restock_needed': restock_needed
                })
        except Product.DoesNotExist:
            continue
    
    return sorted(forecast, key=lambda x: x['days_remaining'])

def get_customer_insights(shop):
    """Analyze customer behavior patterns"""
    last_30_days = timezone.now().date() - timedelta(days=30)
    
    # Get customer data
    bills = Bill.objects.filter(
        shop=shop,
        date__date__gte=last_30_days
    )
    
    total_customers = bills.values('customer_name').distinct().count()
    total_bills = bills.count()
    
    # Calculate repeat customers (customers with more than 1 bill)
    customer_bill_counts = bills.values('customer_name').annotate(
        bill_count=Count('id')
    )
    repeat_customers = customer_bill_counts.filter(bill_count__gt=1).count()
    repeat_rate = (repeat_customers / total_customers * 100) if total_customers > 0 else 0
    
    # Find peak hour
    hourly_sales = bills.extra(
        select={'hour': 'EXTRACT(hour FROM date)'}
    ).values('hour').annotate(
        count=Count('id')
    ).order_by('-count')
    
    peak_hour = hourly_sales.first()['hour'] if hourly_sales else 12
    
    return {
        'total_customers': total_customers,
        'repeat_customers': repeat_customers,
        'repeat_rate': repeat_rate,
        'peak_hour': int(peak_hour)
    }

def get_profit_analysis(shop):
    """Analyze profit margins and trends"""
    last_30_days = timezone.now().date() - timedelta(days=30)
    
    # Get bill items with profit calculation
    bill_items = BillItem.objects.filter(
        bill__shop=shop,
        bill__date__date__gte=last_30_days
    ).select_related('product')
    
    total_revenue = 0
    total_cost = 0
    
    for item in bill_items:
        revenue = float(item.unit_price) * float(item.quantity)
        cost = float(item.product.cost_price or 0) * float(item.quantity)
        total_revenue += revenue
        total_cost += cost
    
    total_profit = total_revenue - total_cost
    profit_margin = (total_profit / total_revenue * 100) if total_revenue > 0 else 0
    daily_avg_profit = total_profit / 30
    
    return {
        'total_revenue': total_revenue,
        'total_cost': total_cost,
        'total_profit': total_profit,
        'profit_margin': profit_margin,
        'daily_avg_profit': daily_avg_profit
    }

def get_best_selling_products(shop):
    """Get best selling products with analytics"""
    last_30_days = timezone.now().date() - timedelta(days=30)
    
    return BillItem.objects.filter(
        bill__shop=shop,
        bill__date__date__gte=last_30_days
    ).values('product__name').annotate(
        total_sold=Sum('quantity'),
        total_revenue=Sum(F('unit_price') * F('quantity')),
        avg_price=Sum(F('unit_price') * F('quantity')) / Sum('quantity')
    ).order_by('-total_revenue')[:10]