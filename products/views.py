from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse, HttpResponse
from .models import Product, Category
from django.db import models
from decimal import Decimal, InvalidOperation
from shopcloud.language_utils import get_user_language, get_template_name
import csv
import uuid

@login_required
def product_list(request):
    products = Product.objects.filter(shop=request.user.shop, is_active=True)
    categories = Category.objects.filter(shop=request.user.shop)
    
    # Search and filter
    search = request.GET.get('search')
    category_filter = request.GET.get('category')
    stock_filter = request.GET.get('stock')
    
    if search:
        products = products.filter(
            Q(name__icontains=search) | Q(barcode__icontains=search)
        )
    
    if category_filter:
        products = products.filter(category_id=category_filter)
    
    if stock_filter == 'low':
        products = [p for p in products if p.is_low_stock]
    elif stock_filter == 'out':
        products = products.filter(stock=0)
    
    context = {
        'products': products,
        'categories': categories,
        'search': search,
        'category_filter': category_filter,
        'stock_filter': stock_filter,
    }
    language = get_user_language(request)
    template_name = get_template_name('products/list.html', language)
    return render(request, template_name, context)

@login_required
def add_product(request):
    categories = Category.objects.filter(shop=request.user.shop)
    
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        category_id = request.POST.get('category')
        unit = request.POST.get('unit', 'piece')
        cost_price_str = request.POST.get('cost_price', '0')
        sale_price_str = request.POST.get('sale_price', '0')
        stock_str = request.POST.get('stock', '0')
        min_stock_alert_str = request.POST.get('min_stock_alert', '5')
        barcode = request.POST.get('barcode', '').strip()
        description = request.POST.get('description', '').strip()
        image = request.FILES.get('image')
        
        # Validation
        errors = []
        
        if not name:
            errors.append('Product name is required!')
        
        # Validate prices
        try:
            cost_price = Decimal(cost_price_str)
            if cost_price < 0:
                errors.append('Cost price cannot be negative!')
        except (ValueError, InvalidOperation):
            errors.append('Invalid cost price format!')
            cost_price = Decimal('0')
        
        try:
            sale_price = Decimal(sale_price_str)
            if sale_price < 0:
                errors.append('Sale price cannot be negative!')
            elif sale_price == 0:
                errors.append('Sale price must be greater than zero!')
        except (ValueError, InvalidOperation):
            errors.append('Invalid sale price format!')
            sale_price = Decimal('0')
        
        # Validate stock
        try:
            stock = int(stock_str)
            if stock < 0:
                errors.append('Stock cannot be negative!')
        except ValueError:
            errors.append('Invalid stock format!')
            stock = 0
        
        try:
            min_stock_alert = int(min_stock_alert_str)
            if min_stock_alert < 0:
                errors.append('Minimum stock alert cannot be negative!')
        except ValueError:
            errors.append('Invalid minimum stock alert format!')
            min_stock_alert = 5
        
        # Validate unit
        valid_units = [choice[0] for choice in Product.UNIT_CHOICES]
        if unit not in valid_units:
            unit = 'piece'
        
        if errors:
            for error in errors:
                messages.error(request, error)
            language = get_user_language(request)
            template_name = get_template_name('products/add.html', language)
            return render(request, template_name, {'categories': categories})
        
        # Get category
        category = None
        if category_id:
            try:
                category = Category.objects.get(id=category_id, shop=request.user.shop)
            except Category.DoesNotExist:
                messages.error(request, 'Selected category not found!')
                language = get_user_language(request)
                template_name = get_template_name('products/add.html', language)
                return render(request, template_name, {'categories': categories})
        
        try:
            Product.objects.create(
                name=name,
                category=category,
                unit=unit,
                cost_price=cost_price,
                sale_price=sale_price,
                stock=stock,
                min_stock_alert=min_stock_alert,
                barcode=barcode if barcode else None,
                description=description,
                image=image,
                shop=request.user.shop
            )
            messages.success(request, 'Product added successfully!')
            return redirect('products:list')
        except Exception as e:
            messages.error(request, f'Error adding product: {str(e)}')
            language = get_user_language(request)
            template_name = get_template_name('products/add.html', language)
            return render(request, template_name, {'categories': categories})
    
    language = get_user_language(request)
    template_name = get_template_name('products/add.html', language)
    return render(request, template_name, {'categories': categories})

@login_required
def edit_product(request, product_id):
    product = get_object_or_404(Product, id=product_id, shop=request.user.shop)
    categories = Category.objects.filter(shop=request.user.shop)
    
    if request.method == 'POST':
        print(f"Edit form submitted for product: {product.name}")  # Debug line
        name = request.POST.get('name', '').strip()
        category_id = request.POST.get('category')
        unit = request.POST.get('unit', 'piece')
        cost_price_str = request.POST.get('cost_price', '0')
        sale_price_str = request.POST.get('sale_price', '0')
        stock_str = request.POST.get('stock', '0')
        min_stock_alert_str = request.POST.get('min_stock_alert', '5')
        barcode = request.POST.get('barcode', '').strip()
        description = request.POST.get('description', '').strip()
        
        # Validation
        errors = []
        
        if not name:
            errors.append('Product name is required!')
        
        try:
            cost_price = Decimal(cost_price_str)
            if cost_price < 0:
                errors.append('Cost price cannot be negative!')
        except (ValueError, InvalidOperation):
            errors.append('Invalid cost price format!')
            cost_price = product.cost_price
        
        try:
            sale_price = Decimal(sale_price_str)
            if sale_price < 0:
                errors.append('Sale price cannot be negative!')
            elif sale_price == 0:
                errors.append('Sale price must be greater than zero!')
        except (ValueError, InvalidOperation):
            errors.append('Invalid sale price format!')
            sale_price = product.sale_price
        
        try:
            stock = int(stock_str)
            if stock < 0:
                errors.append('Stock cannot be negative!')
        except ValueError:
            errors.append('Invalid stock format!')
            stock = product.stock
        
        try:
            min_stock_alert = int(min_stock_alert_str)
            if min_stock_alert < 0:
                errors.append('Minimum stock alert cannot be negative!')
        except ValueError:
            errors.append('Invalid minimum stock alert format!')
            min_stock_alert = product.min_stock_alert
        
        valid_units = [choice[0] for choice in Product.UNIT_CHOICES]
        if unit not in valid_units:
            unit = product.unit
        
        if errors:
            for error in errors:
                messages.error(request, error)
            language = get_user_language(request)
            template_name = get_template_name('products/edit.html', language)
            return render(request, template_name, {'product': product, 'categories': categories})
        
        # Update product
        try:
            product.name = name
            product.unit = unit
            product.cost_price = cost_price
            product.sale_price = sale_price
            product.stock = stock
            product.min_stock_alert = min_stock_alert
            product.barcode = barcode if barcode else None
            product.description = description
            
            if category_id:
                try:
                    product.category = Category.objects.get(id=category_id, shop=request.user.shop)
                except Category.DoesNotExist:
                    product.category = None
            else:
                product.category = None
                
            if request.FILES.get('image'):
                product.image = request.FILES['image']
                
            product.save()
            messages.success(request, 'Product updated successfully!')
            print(f"Product {product.name} updated successfully")  # Debug line
            return redirect('products:list')
        except Exception as e:
            print(f"Error updating product: {str(e)}")  # Debug line
            messages.error(request, f'Error updating product: {str(e)}')
            language = get_user_language(request)
            template_name = get_template_name('products/edit.html', language)
            return render(request, template_name, {'product': product, 'categories': categories})
    
    language = get_user_language(request)
    template_name = get_template_name('products/edit.html', language)
    return render(request, template_name, {'product': product, 'categories': categories})

@login_required
def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id, shop=request.user.shop)
    product.is_active = False
    product.save()
    messages.success(request, 'Product deleted successfully!')
    return redirect('products:list')

# Category Management
@login_required
def category_list(request):
    categories = Category.objects.filter(shop=request.user.shop)
    language = get_user_language(request)
    template_name = get_template_name('products/categories.html', language)
    return render(request, template_name, {'categories': categories})

@login_required
def add_category(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        
        # Validation
        if not name:
            messages.error(request, 'Category name is required!')
            return render(request, 'products/add_category.html')
        
        # Check if category with same name already exists
        if Category.objects.filter(name=name, shop=request.user.shop).exists():
            messages.error(request, 'Category with this name already exists!')
            return render(request, 'products/add_category.html')
        
        try:
            Category.objects.create(
                name=name,
                description=description,
                shop=request.user.shop
            )
            messages.success(request, 'Category added successfully!')
            return redirect('products:categories')
        except Exception as e:
            messages.error(request, f'Error adding category: {str(e)}')
            return render(request, 'products/add_category.html')
    
    return render(request, 'products/add_category.html')

@login_required
def edit_category(request, category_id):
    category = get_object_or_404(Category, id=category_id, shop=request.user.shop)
    
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        
        # Validation
        if not name:
            messages.error(request, 'Category name is required!')
            return render(request, 'products/edit_category.html', {'category': category})
        
        # Check if another category with same name exists
        if Category.objects.filter(name=name, shop=request.user.shop).exclude(id=category_id).exists():
            messages.error(request, 'Category with this name already exists!')
            return render(request, 'products/edit_category.html', {'category': category})
        
        try:
            category.name = name
            category.description = description
            category.save()
            messages.success(request, 'Category updated successfully!')
            return redirect('products:categories')
        except Exception as e:
            messages.error(request, f'Error updating category: {str(e)}')
            return render(request, 'products/edit_category.html', {'category': category})
    
    return render(request, 'products/edit_category.html', {'category': category})

@login_required
def delete_category(request, category_id):
    category = get_object_or_404(Category, id=category_id, shop=request.user.shop)
    
    if category.product_set.exists():
        messages.error(request, 'Cannot delete category with products!')
    else:
        category.delete()
        messages.success(request, 'Category deleted successfully!')
    
    return redirect('products:categories')

# Bulk Operations
@login_required
def export_products(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="products.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Name', 'Category', 'Unit', 'Cost Price', 'Sale Price', 'Stock', 'Min Stock Alert', 'Barcode', 'Description'])
    
    products = Product.objects.filter(shop=request.user.shop, is_active=True)
    for product in products:
        writer.writerow([
            product.name,
            product.category.name if product.category else '',
            product.unit,
            product.cost_price,
            product.sale_price,
            product.stock,
            product.min_stock_alert,
            product.barcode,
            product.description
        ])
    
    return response

@login_required
def import_products(request):
    if request.method == 'POST' and request.FILES.get('csv_file'):
        csv_file = request.FILES['csv_file']
        
        try:
            decoded_file = csv_file.read().decode('utf-8')
            csv_data = csv.reader(decoded_file.splitlines())
            
            # Skip header row
            next(csv_data)
            
            imported_count = 0
            for row in csv_data:
                if len(row) >= 6:  # Minimum required fields
                    name, category_name, unit, cost_price, sale_price, stock = row[:6]
                    
                    # Get or create category
                    category = None
                    if category_name:
                        category, created = Category.objects.get_or_create(
                            name=category_name,
                            shop=request.user.shop,
                            defaults={'description': f'Auto-created for {category_name}'}
                        )
                    
                    # Create product
                    Product.objects.create(
                        name=name,
                        category=category,
                        unit=unit if unit in dict(Product.UNIT_CHOICES) else 'piece',
                        cost_price=float(cost_price) if cost_price else 0,
                        sale_price=float(sale_price),
                        stock=int(stock) if stock else 0,
                        shop=request.user.shop
                    )
                    imported_count += 1
            
            messages.success(request, f'{imported_count} products imported successfully!')
        except Exception as e:
            messages.error(request, f'Error importing products: {str(e)}')
    
    return redirect('products:list')

@login_required
def generate_barcode(request):
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        product = get_object_or_404(Product, id=product_id, shop=request.user.shop)
        
        # Generate new barcode
        import uuid
        product.barcode = str(uuid.uuid4())[:12].upper()
        product.save()
        
        return JsonResponse({
            'success': True,
            'barcode': product.barcode
        })
    
    return JsonResponse({'success': False})

@login_required
def low_stock_alert(request):
    low_stock_products = Product.objects.filter(
        shop=request.user.shop, 
        is_active=True
    ).filter(stock__lte=models.F('min_stock_alert'))
    
    return JsonResponse({
        'count': low_stock_products.count(),
        'products': [{
            'id': p.id,
            'name': p.name,
            'stock': p.stock,
            'min_stock': p.min_stock_alert,
            'category': p.category.name if p.category else 'No Category'
        } for p in low_stock_products]
    })

@login_required
def bulk_update_stock(request):
    if request.method == 'POST':
        updates = request.POST.getlist('updates')
        updated_count = 0
        
        for update in updates:
            try:
                product_id, new_stock = update.split(':')
                product = Product.objects.get(id=product_id, shop=request.user.shop)
                product.stock = int(new_stock)
                product.save()
                updated_count += 1
            except (ValueError, Product.DoesNotExist):
                continue
        
        return JsonResponse({
            'success': True,
            'updated_count': updated_count
        })
    
    return JsonResponse({'success': False})