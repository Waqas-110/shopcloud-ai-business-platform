from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core import serializers
from django.utils import timezone
from users.models import Shop
from products.models import Product, Category
from billing.models import Bill, BillItem
import json
import csv
from io import StringIO

@login_required
def shop_settings(request):
    shop = get_object_or_404(Shop, user=request.user)
    
    if request.method == 'POST':
        shop.name = request.POST.get('name')
        shop.address = request.POST.get('address')
        shop.whatsapp_number = request.POST.get('whatsapp_number')
        shop.email = request.POST.get('email')
        
        if 'logo' in request.FILES:
            shop.logo = request.FILES['logo']
        
        shop.save()
        messages.success(request, 'Shop settings updated successfully!')
        return redirect('settings:shop_settings')
    
    return render(request, 'settings/shop_settings.html', {'shop': shop})

@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Password changed successfully!')
            return redirect('settings:change_password')
    else:
        form = PasswordChangeForm(request.user)
    
    return render(request, 'settings/change_password.html', {'form': form})

@login_required
def preferences(request):
    shop = get_object_or_404(Shop, user=request.user)
    
    if request.method == 'POST':
        # Save user preferences
        currency = request.POST.get('currency', 'PKR')
        tax_rate = request.POST.get('tax_rate', '0')
        low_stock_alert = request.POST.get('low_stock_alert', '10')
        
        # Store preferences in session
        request.session['preferences'] = {
            'currency': currency,
            'tax_rate': float(tax_rate),
            'low_stock_alert': int(low_stock_alert),
        }
        
        messages.success(request, 'Preferences updated successfully!')
        return redirect('settings:preferences')
    
    # Get current preferences
    preferences = request.session.get('preferences', {
        'currency': 'PKR',
        'tax_rate': 0.0,
        'low_stock_alert': 10,
    })
    
    context = {
        'shop': shop,
        'preferences': preferences,
    }
    return render(request, 'settings/preferences.html', context)

@login_required
def payment_options(request):
    shop = get_object_or_404(Shop, user=request.user)
    
    if request.method == 'POST':
        # Save payment method settings
        cash_enabled = request.POST.get('cash_enabled') == 'on'
        card_enabled = request.POST.get('card_enabled') == 'on'
        mobile_banking = request.POST.get('mobile_banking') == 'on'
        credit_enabled = request.POST.get('credit_enabled') == 'on'
        
        # Store payment settings
        request.session['payment_settings'] = {
            'cash_enabled': cash_enabled,
            'card_enabled': card_enabled,
            'mobile_banking': mobile_banking,
            'credit_enabled': credit_enabled,
        }
        
        messages.success(request, 'Payment options updated successfully!')
        return redirect('settings:payment_options')
    
    # Get current settings
    payment_settings = request.session.get('payment_settings', {
        'cash_enabled': True,
        'card_enabled': False,
        'mobile_banking': False,
        'credit_enabled': False,
    })
    
    context = {
        'shop': shop,
        'payment_settings': payment_settings,
    }
    return render(request, 'settings/payment_options.html', context)

@login_required
def data_backup(request):
    shop = get_object_or_404(Shop, user=request.user)
    
    context = {
        'shop': shop,
        'products_count': Product.objects.filter(shop=shop).count(),
        'bills_count': Bill.objects.filter(shop=shop).count(),
        'categories_count': Category.objects.filter(shop=shop).count(),
    }
    return render(request, 'settings/data_backup.html', context)

@login_required
def export_data(request):
    shop = get_object_or_404(Shop, user=request.user)
    export_type = request.GET.get('type', 'all')
    
    if export_type == 'products':
        return export_products_csv(shop)
    elif export_type == 'bills':
        return export_bills_csv(shop)
    elif export_type == 'all':
        return export_all_data_json(shop)
    
    return JsonResponse({'error': 'Invalid export type'})

def export_products_csv(shop):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="products_{shop.name}_{timezone.now().strftime("%Y%m%d")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Name', 'Category', 'Cost Price', 'Sale Price', 'Stock', 'Barcode', 'Unit'])
    
    products = Product.objects.filter(shop=shop)
    for product in products:
        writer.writerow([
            product.name,
            product.category.name if product.category else '',
            product.cost_price,
            product.sale_price,
            product.stock,
            product.barcode or '',
            product.unit
        ])
    
    return response

def export_bills_csv(shop):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="bills_{shop.name}_{timezone.now().strftime("%Y%m%d")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Bill Number', 'Date', 'Customer Name', 'Subtotal', 'Tax', 'Total', 'Payment Method'])
    
    bills = Bill.objects.filter(shop=shop).order_by('-date')
    for bill in bills:
        writer.writerow([
            bill.bill_number,
            bill.date.strftime('%Y-%m-%d %H:%M'),
            bill.customer_name or 'Walk-in Customer',
            bill.subtotal,
            bill.tax,
            bill.total,
            bill.payment_method
        ])
    
    return response

def export_all_data_json(shop):
    response = HttpResponse(content_type='application/json')
    response['Content-Disposition'] = f'attachment; filename="backup_{shop.name}_{timezone.now().strftime("%Y%m%d")}.json"'
    
    # Collect all data
    data = {
        'shop': {
            'name': shop.name,
            'address': shop.address,
            'whatsapp_number': shop.whatsapp_number,
            'email': shop.email,
        },
        'categories': list(Category.objects.filter(shop=shop).values()),
        'products': list(Product.objects.filter(shop=shop).values()),
        'bills': list(Bill.objects.filter(shop=shop).values()),
        'bill_items': list(BillItem.objects.filter(bill__shop=shop).values()),
        'export_date': timezone.now().isoformat(),
    }
    
    # Convert Decimal to string for JSON serialization
    def decimal_to_str(obj):
        if hasattr(obj, '__iter__') and not isinstance(obj, (str, bytes)):
            return [decimal_to_str(item) for item in obj]
        elif isinstance(obj, dict):
            return {key: decimal_to_str(value) for key, value in obj.items()}
        elif hasattr(obj, '__dict__'):
            return str(obj)
        return obj
    
    data = decimal_to_str(data)
    
    json.dump(data, response, indent=2, default=str)
    return response