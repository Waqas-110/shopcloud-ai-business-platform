from django.db.models import Sum, Count, Q, F
from django.utils import timezone
from datetime import datetime, timedelta
from billing.models import Bill, BillItem
from products.models import Product, Category
from .models import SalesAnalytics, ProductSalesReport, CategorySalesReport
from decimal import Decimal

def calculate_daily_analytics(shop, date=None):
    """Calculate and store daily analytics for a shop"""
    if not date:
        date = timezone.now().date()
    
    # Get all bills for the date
    bills = Bill.objects.filter(shop=shop, date__date=date)
    
    # Calculate totals
    total_sales = bills.aggregate(Sum('total'))['total__sum'] or Decimal('0')
    total_bills = bills.count()
    
    # Calculate profit from bill items
    bill_items = BillItem.objects.filter(bill__in=bills)
    total_profit = Decimal('0')
    
    for item in bill_items:
        cost = item.product.cost_price * item.quantity
        profit = item.total_price - cost
        total_profit += profit
    
    # Update or create analytics record
    analytics, created = SalesAnalytics.objects.update_or_create(
        shop=shop,
        date=date,
        defaults={
            'total_sales': total_sales,
            'total_bills': total_bills,
            'total_profit': total_profit
        }
    )
    
    return analytics

def get_sales_report(shop, start_date, end_date):
    """Get sales report for date range"""
    bills = Bill.objects.filter(
        shop=shop,
        date__date__range=[start_date, end_date]
    )
    
    total_sales = bills.aggregate(Sum('total'))['total__sum'] or Decimal('0')
    total_bills = bills.count()
    
    # Calculate profit
    bill_items = BillItem.objects.filter(bill__in=bills)
    total_profit = Decimal('0')
    total_cost = Decimal('0')
    
    for item in bill_items:
        cost = item.product.cost_price * item.quantity
        total_cost += cost
        total_profit += (item.total_price - cost)
    
    return {
        'total_sales': total_sales,
        'total_bills': total_bills,
        'total_profit': total_profit,
        'total_cost': total_cost,
        'profit_margin': (total_profit / total_sales * 100) if total_sales > 0 else 0
    }

def get_top_products(shop, start_date, end_date, limit=10):
    """Get top selling products for date range"""
    top_products = BillItem.objects.filter(
        bill__shop=shop,
        bill__date__date__range=[start_date, end_date]
    ).values(
        'product__name',
        'product__id'
    ).annotate(
        total_quantity=Sum('quantity'),
        total_revenue=Sum('total_price')
    ).order_by('-total_quantity')[:limit]
    
    return top_products

def get_category_sales(shop, start_date, end_date):
    """Get category-wise sales for date range"""
    category_sales = BillItem.objects.filter(
        bill__shop=shop,
        bill__date__date__range=[start_date, end_date],
        product__category__isnull=False
    ).values(
        'product__category__name',
        'product__category__id'
    ).annotate(
        total_quantity=Sum('quantity'),
        total_revenue=Sum('total_price'),
        items_count=Count('id')
    ).order_by('-total_revenue')
    
    return category_sales

def get_daily_sales_chart_data(shop, days=30):
    """Get daily sales data for charts"""
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days-1)
    
    # Get sales data for each day
    sales_data = []
    current_date = start_date
    
    while current_date <= end_date:
        daily_sales = Bill.objects.filter(
            shop=shop,
            date__date=current_date
        ).aggregate(Sum('total'))['total__sum'] or Decimal('0')
        
        sales_data.append({
            'date': current_date.strftime('%Y-%m-%d'),
            'sales': float(daily_sales)
        })
        current_date += timedelta(days=1)
    
    return sales_data

def get_payment_method_stats(shop, start_date, end_date):
    """Get payment method statistics"""
    payment_stats = Bill.objects.filter(
        shop=shop,
        date__date__range=[start_date, end_date]
    ).values('payment_type').annotate(
        count=Count('id'),
        total=Sum('total')
    ).order_by('-total')
    
    return payment_stats

def get_hourly_sales_pattern(shop, date=None):
    """Get hourly sales pattern for a specific date"""
    if not date:
        date = timezone.now().date()
    
    hourly_sales = Bill.objects.filter(
        shop=shop,
        date__date=date
    ).extra(
        select={'hour': 'EXTRACT(hour FROM date)'}
    ).values('hour').annotate(
        count=Count('id'),
        total=Sum('total')
    ).order_by('hour')
    
    return hourly_sales