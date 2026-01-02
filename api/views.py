from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.shortcuts import get_object_or_404
from django.db.models import Q, F, Sum
from django.utils import timezone
from products.models import Product, Category
from billing.models import Bill, BillItem
from .utils import APIResponse, APIValidator, handle_api_errors
import json

@login_required
@require_http_methods(["GET"])
@handle_api_errors
def products_api(request):
    search = request.GET.get('search', '').strip()
    category_id = request.GET.get('category')
    limit = min(int(request.GET.get('limit', 20)), 100)
    
    products = Product.objects.filter(shop=request.user.shop, is_active=True)
    
    if search:
        products = products.filter(
            Q(name__icontains=search) | Q(barcode__icontains=search)
        )
    
    if category_id:
        products = products.filter(category_id=category_id)
    
    products = products.select_related('category')[:limit]
    
    data = [{
        'id': p.id,
        'name': p.name,
        'price': float(p.sale_price),
        'cost_price': float(p.cost_price),
        'stock': p.stock,
        'unit': p.unit,
        'barcode': p.barcode,
        'category': p.category.name if p.category else None,
        'is_low_stock': p.is_low_stock,
        'profit_margin': float(p.profit_margin)
    } for p in products]
    
    return APIResponse.success(data)

@login_required
@require_http_methods(["POST"])
@handle_api_errors
def create_product_api(request):
    data = json.loads(request.body)
    
    name = APIValidator.validate_required(data.get('name'), 'Product name')
    cost_price = APIValidator.validate_decimal(data.get('cost_price', 0), 'Cost price', 0)
    sale_price = APIValidator.validate_decimal(data.get('sale_price'), 'Sale price', 0.01)
    stock = APIValidator.validate_integer(data.get('stock', 0), 'Stock', 0)
    min_stock_alert = APIValidator.validate_integer(data.get('min_stock_alert', 5), 'Min stock alert', 0)
    
    product = Product.objects.create(
        name=name,
        cost_price=cost_price,
        sale_price=sale_price,
        stock=stock,
        min_stock_alert=min_stock_alert,
        unit=data.get('unit', 'piece'),
        barcode=data.get('barcode', '').strip() or None,
        description=data.get('description', '').strip(),
        shop=request.user.shop
    )
    
    if data.get('category_id'):
        try:
            category = Category.objects.get(id=data['category_id'], shop=request.user.shop)
            product.category = category
            product.save()
        except Category.DoesNotExist:
            pass
    
    return APIResponse.success({
        'id': product.id,
        'name': product.name,
        'message': 'Product created successfully'
    }, status=201)

@login_required
@require_http_methods(["PUT"])
@handle_api_errors
def update_product_api(request, product_id):
    product = get_object_or_404(Product, id=product_id, shop=request.user.shop)
    data = json.loads(request.body)
    
    if 'name' in data:
        product.name = APIValidator.validate_required(data['name'], 'Product name')
    if 'cost_price' in data:
        product.cost_price = APIValidator.validate_decimal(data['cost_price'], 'Cost price', 0)
    if 'sale_price' in data:
        product.sale_price = APIValidator.validate_decimal(data['sale_price'], 'Sale price', 0.01)
    if 'stock' in data:
        product.stock = APIValidator.validate_integer(data['stock'], 'Stock', 0)
    if 'min_stock_alert' in data:
        product.min_stock_alert = APIValidator.validate_integer(data['min_stock_alert'], 'Min stock alert', 0)
    
    product.save()
    
    return APIResponse.success({
        'id': product.id,
        'name': product.name,
        'message': 'Product updated successfully'
    })

@login_required
@require_http_methods(["POST"])
@handle_api_errors
def bulk_update_stock_api(request):
    data = json.loads(request.body)
    updates = data.get('updates', [])
    
    if not updates:
        return APIResponse.error("No updates provided")
    
    updated_count = 0
    errors = []
    
    for update in updates:
        try:
            product_id = update.get('product_id')
            new_stock = APIValidator.validate_integer(update.get('stock'), 'Stock', 0)
            
            product = Product.objects.get(id=product_id, shop=request.user.shop)
            product.stock = new_stock
            product.save()
            updated_count += 1
        except Product.DoesNotExist:
            errors.append(f"Product {product_id} not found")
        except Exception as e:
            errors.append(f"Error updating product {product_id}: {str(e)}")
    
    return APIResponse.success({
        'updated_count': updated_count,
        'errors': errors
    })

@login_required
@require_http_methods(["GET"])
@handle_api_errors
def low_stock_products_api(request):
    products = Product.objects.filter(
        shop=request.user.shop,
        is_active=True,
        stock__lte=F('min_stock_alert')
    ).select_related('category')
    
    data = [{
        'id': p.id,
        'name': p.name,
        'stock': p.stock,
        'min_stock_alert': p.min_stock_alert,
        'category': p.category.name if p.category else 'No Category'
    } for p in products]
    
    return APIResponse.success({
        'count': len(data),
        'products': data
    })

@login_required
@require_http_methods(["POST"])
@handle_api_errors
def create_bill_api(request):
    data = json.loads(request.body)
    
    items = data.get('items', [])
    if not items:
        return APIResponse.error("No items provided")
    
    subtotal = APIValidator.validate_decimal(data.get('subtotal', 0), 'Subtotal', 0)
    tax = APIValidator.validate_decimal(data.get('tax', 0), 'Tax', 0)
    discount = APIValidator.validate_decimal(data.get('discount', 0), 'Discount', 0)
    total = APIValidator.validate_decimal(data.get('total'), 'Total', 0.01)
    
    bill = Bill.objects.create(
        shop=request.user.shop,
        customer_name=data.get('customer_name', '').strip()[:100],
        customer_phone=data.get('customer_phone', '').strip()[:15],
        payment_type=data.get('payment_type', 'cash'),
        subtotal=subtotal,
        tax=tax,
        discount=discount,
        total=total
    )
    
    for item_data in items:
        product = get_object_or_404(Product, id=item_data['product_id'], shop=request.user.shop)
        quantity = APIValidator.validate_integer(item_data['quantity'], 'Quantity', 1)
        unit_price = APIValidator.validate_decimal(item_data['unit_price'], 'Unit price', 0)
        
        if product.stock < quantity:
            return APIResponse.error(f"Insufficient stock for {product.name}")
        
        BillItem.objects.create(
            bill=bill,
            product=product,
            quantity=quantity,
            unit_price=unit_price,
            total_price=unit_price * quantity
        )
        
        product.stock -= quantity
        product.save()
    
    return APIResponse.success({
        'bill_id': bill.id,
        'bill_number': bill.bill_number,
        'message': 'Bill created successfully'
    }, status=201)

@login_required
@require_http_methods(["GET"])
@handle_api_errors
def sales_summary_api(request):
    from datetime import datetime, timedelta
    
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    bills = Bill.objects.filter(shop=request.user.shop)
    
    today_sales = bills.filter(date__date=today).aggregate(
        total=Sum('total'), count=Sum('id')
    )
    week_sales = bills.filter(date__date__gte=week_ago).aggregate(
        total=Sum('total'), count=Sum('id')
    )
    month_sales = bills.filter(date__date__gte=month_ago).aggregate(
        total=Sum('total'), count=Sum('id')
    )
    
    return APIResponse.success({
        'today': {
            'total': float(today_sales['total'] or 0),
            'count': today_sales['count'] or 0
        },
        'week': {
            'total': float(week_sales['total'] or 0),
            'count': week_sales['count'] or 0
        },
        'month': {
            'total': float(month_sales['total'] or 0),
            'count': month_sales['count'] or 0
        }
    })

@login_required
@require_http_methods(["GET"])
@handle_api_errors
def dashboard_stats_api(request):
    products = Product.objects.filter(shop=request.user.shop, is_active=True)
    bills = Bill.objects.filter(shop=request.user.shop)
    
    low_stock_count = products.filter(stock__lte=F('min_stock_alert')).count()
    out_of_stock_count = products.filter(stock=0).count()
    
    today = timezone.now().date()
    today_sales = bills.filter(date__date=today).aggregate(
        total=Sum('total'), count=Sum('id')
    )
    
    return APIResponse.success({
        'total_products': products.count(),
        'low_stock_products': low_stock_count,
        'out_of_stock_products': out_of_stock_count,
        'today_sales': float(today_sales['total'] or 0),
        'today_bills': today_sales['count'] or 0
    })