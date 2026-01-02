from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from .models import Bill, BillItem, Customer
from products.models import Product, Category
from shopcloud.language_utils import get_user_language, get_template_name
import json
from decimal import Decimal, InvalidOperation
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch

@login_required
def pos_interface(request):
    products = Product.objects.filter(shop=request.user.shop, stock__gt=0)[:20]
    categories = Category.objects.filter(shop=request.user.shop)
    
    # Check language preference
    language = get_user_language(request)
    if language == 'ur':
        template_name = 'billing/pos_new_ur.html'
    else:
        template_name = 'billing/pos_new.html'
    
    return render(request, template_name, {
        'products': products,
        'categories': categories
    })

@login_required
def search_products(request):
    query = request.GET.get('q', '').strip()
    if len(query) < 1:
        return JsonResponse({'products': []})
    
    products = Product.objects.filter(
        Q(name__icontains=query) | Q(barcode__icontains=query),
        shop=request.user.shop,
        is_active=True
    ).order_by('-stock', 'name')[:10]
    
    product_list = []
    for product in products:
        product_list.append({
            'id': product.id,
            'name': product.name,
            'price': float(product.sale_price),
            'stock': product.stock,
            'barcode': product.barcode or '',
            'image': product.image.url if product.image else None,
            'unit': product.unit
        })
    
    return JsonResponse({'products': product_list})

@login_required
def add_to_cart(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        product_id = data.get('product_id')
        quantity = int(data.get('quantity', 1))
        
        try:
            product = Product.objects.get(id=product_id, shop=request.user.shop)
            
            if product.stock < quantity:
                return JsonResponse({'success': False, 'error': 'Insufficient stock'})
            
            # Get or create cart in session
            cart = request.session.get('cart', {})
            
            if str(product_id) in cart:
                cart[str(product_id)]['quantity'] += quantity
            else:
                cart[str(product_id)] = {
                    'name': product.name,
                    'price': float(product.sale_price),
                    'quantity': quantity,
                    'stock': product.stock,
                    'unit': product.unit
                }
            
            # Check total quantity doesn't exceed stock
            if cart[str(product_id)]['quantity'] > product.stock:
                cart[str(product_id)]['quantity'] = product.stock
            
            request.session['cart'] = cart
            request.session.modified = True
            
            return JsonResponse({'success': True, 'cart': cart})
            
        except Product.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Product not found'})
    
    return JsonResponse({'success': False})

@login_required
def update_cart(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        product_id = str(data.get('product_id'))
        quantity = data.get('quantity', 1)
        
        cart = request.session.get('cart', {})
        
        if product_id in cart:
            if quantity <= 0:
                del cart[product_id]
            else:
                # Check stock and validate quantity based on unit
                try:
                    product = Product.objects.get(id=product_id, shop=request.user.shop)
                    
                    # Validate quantity based on unit type
                    if product.unit in ['kg', 'liter']:
                        quantity = float(quantity)
                        if quantity <= 0:
                            return JsonResponse({'success': False, 'error': 'Invalid quantity'})
                    else:
                        quantity = int(float(quantity))
                        if quantity != float(quantity) or quantity <= 0:
                            return JsonResponse({'success': False, 'error': f'{product.unit} must be whole numbers only'})
                    
                    if quantity > product.stock:
                        quantity = product.stock
                    
                    cart[product_id]['quantity'] = quantity
                    cart[product_id]['unit'] = product.unit  # Ensure unit is updated
                    
                except Product.DoesNotExist:
                    del cart[product_id]
                except ValueError:
                    return JsonResponse({'success': False, 'error': 'Invalid quantity format'})
        
        request.session['cart'] = cart
        request.session.modified = True
        
        return JsonResponse({'success': True, 'cart': cart})
    
    return JsonResponse({'success': False})

@login_required
def remove_from_cart(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        product_id = str(data.get('product_id'))
        
        cart = request.session.get('cart', {})
        
        if product_id in cart:
            del cart[product_id]
        
        request.session['cart'] = cart
        request.session.modified = True
        
        return JsonResponse({'success': True, 'cart': cart})
    
    return JsonResponse({'success': False})

@login_required
def clear_cart(request):
    if request.method == 'POST':
        request.session['cart'] = {}
        request.session.modified = True
        return JsonResponse({'success': True})
    
    return JsonResponse({'success': False})

@login_required
def create_bill(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON data'})
        
        cart = request.session.get('cart', {})
        
        if not cart:
            return JsonResponse({'success': False, 'error': 'Cart is empty'})
        
        try:
            # Validate payment type
            payment_type = data.get('payment_type', 'cash')
            valid_payment_types = [choice[0] for choice in Bill.PAYMENT_CHOICES]
            if payment_type not in valid_payment_types:
                payment_type = 'cash'
            
            # Validate amounts
            try:
                subtotal = Decimal(str(data.get('subtotal', 0)))
                tax = Decimal(str(data.get('tax', 0)))
                discount = Decimal(str(data.get('discount', 0)))
                total = Decimal(str(data.get('total', 0)))
                
                if subtotal < 0 or tax < 0 or discount < 0 or total < 0:
                    return JsonResponse({'success': False, 'error': 'Invalid amount values'})
            except (ValueError, InvalidOperation):
                return JsonResponse({'success': False, 'error': 'Invalid amount format'})
            
            # Create or get customer
            customer_phone = data.get('customer_phone', '').strip()[:15]
            customer_name = data.get('customer_name', '').strip()[:100]
            customer_email = data.get('customer_email', '').strip()
            
            if customer_phone and customer_name:
                # Try to find existing customer
                customer, created = Customer.objects.get_or_create(
                    phone=customer_phone,
                    shop=request.user.shop,
                    defaults={
                        'name': customer_name,
                        'email': customer_email
                    }
                )
                # Update if exists but data changed
                if not created and (customer.name != customer_name or customer.email != customer_email):
                    customer.name = customer_name
                    customer.email = customer_email
                    customer.save()
            
            # Create bill
            bill = Bill.objects.create(
                shop=request.user.shop,
                customer_name=customer_name,
                customer_phone=customer_phone,
                payment_type=payment_type,
                subtotal=subtotal,
                tax=tax,
                discount=discount,
                total=total
            )
            
            # Create bill items and update stock
            for product_id, item in cart.items():
                try:
                    product = Product.objects.get(id=product_id, shop=request.user.shop)
                except Product.DoesNotExist:
                    return JsonResponse({'success': False, 'error': f'Product {product_id} not found'})
                
                # Handle quantity based on unit type
                if product.unit in ['kg', 'liter']:
                    quantity = float(item.get('quantity', 0))
                else:
                    quantity = int(item.get('quantity', 0))
                
                if quantity <= 0:
                    continue
                
                if product.stock < quantity:
                    return JsonResponse({'success': False, 'error': f'Insufficient stock for {product.name}'})
                
                try:
                    unit_price = Decimal(str(item.get('price', 0)))
                    quantity_decimal = Decimal(str(quantity))
                    if unit_price < 0:
                        return JsonResponse({'success': False, 'error': 'Invalid product price'})
                except (ValueError, InvalidOperation):
                    return JsonResponse({'success': False, 'error': 'Invalid price format'})
                
                BillItem.objects.create(
                    bill=bill,
                    product=product,
                    quantity=quantity_decimal,
                    unit_price=unit_price,
                    total_price=unit_price * quantity_decimal
                )
                
                # Update stock
                product.stock -= quantity
                if product.stock < 0:
                    product.stock = 0
                product.save()
            
            # Clear cart
            request.session['cart'] = {}
            request.session.modified = True
            
            return JsonResponse({
                'success': True, 
                'bill_id': bill.id,
                'bill_number': bill.bill_number
            })
            
        except Product.DoesNotExist as e:
            return JsonResponse({'success': False, 'error': 'Product not found'})
        except ValueError as e:
            import traceback
            print(f"ValueError: {str(e)}")
            print(traceback.format_exc())
            return JsonResponse({'success': False, 'error': f'Invalid data: {str(e)}'})
        except Exception as e:
            import traceback
            print(f"Error creating bill: {str(e)}")
            print(traceback.format_exc())
            return JsonResponse({'success': False, 'error': f'Error creating bill: {str(e)}'})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
def bill_detail(request, bill_id):
    bill = get_object_or_404(Bill, id=bill_id, shop=request.user.shop)
    return render(request, 'billing/bill_detail.html', {'bill': bill})

@login_required
def bills_list(request):
    search = request.GET.get('search', '')
    payment_type = request.GET.get('payment_type', '')
    from_date = request.GET.get('from_date', '')
    to_date = request.GET.get('to_date', '')
    bills = Bill.objects.filter(shop=request.user.shop)
    
    if search:
        bills = bills.filter(
            Q(bill_number__icontains=search) |
            Q(customer_name__icontains=search) |
            Q(customer_phone__icontains=search)
        )
    
    if payment_type:
        bills = bills.filter(payment_type=payment_type)
    
    if from_date:
        bills = bills.filter(date__date__gte=from_date)
    
    if to_date:
        bills = bills.filter(date__date__lte=to_date)
    
    bills = bills.order_by('-date')[:100]
    
    # Calculate stats
    total_amount = sum(bill.total for bill in bills)
    
    language = get_user_language(request)
    template_name = get_template_name('billing/bills_list.html', language)
    return render(request, template_name, {
        'bills': bills, 
        'search': search,
        'from_date': from_date,
        'to_date': to_date,
        'total_amount': total_amount
    })

@login_required
def bill_pdf(request, bill_id):
    bill = get_object_or_404(Bill, id=bill_id, shop=request.user.shop)
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="bill_{bill.bill_number}.pdf"'
    
    p = canvas.Canvas(response, pagesize=letter)
    width, height = letter
    
    # Header
    p.setFont("Helvetica-Bold", 20)
    p.drawString(width/2 - 100, height-50, bill.shop.name)
    p.setFont("Helvetica", 12)
    p.drawString(width/2 - 50, height-70, bill.shop.address or '')
    
    # Bill info
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, height-120, f"Bill #{bill.bill_number}")
    p.setFont("Helvetica", 10)
    p.drawString(50, height-140, f"Date: {bill.date.strftime('%d %b %Y, %H:%M')}")
    p.drawString(50, height-155, f"Payment: {bill.get_payment_type_display()}")
    
    if bill.customer_name:
        p.drawString(300, height-140, f"Customer: {bill.customer_name}")
    if bill.customer_phone:
        p.drawString(300, height-155, f"Phone: {bill.customer_phone}")
    
    # Items table
    y = height - 200
    p.setFont("Helvetica-Bold", 10)
    p.drawString(50, y, "Item")
    p.drawString(300, y, "Qty")
    p.drawString(350, y, "Price")
    p.drawString(450, y, "Total")
    
    y -= 20
    p.setFont("Helvetica", 9)
    
    for item in bill.items.all():
        p.drawString(50, y, item.product.name[:30])
        p.drawString(300, y, str(item.quantity))
        p.drawString(350, y, f"Rs. {item.unit_price}")
        p.drawString(450, y, f"Rs. {item.total_price}")
        y -= 15
    
    # Totals
    y -= 20
    p.setFont("Helvetica-Bold", 10)
    p.drawString(350, y, f"Subtotal: Rs. {bill.subtotal}")
    y -= 15
    if bill.tax > 0:
        p.drawString(350, y, f"Tax: Rs. {bill.tax}")
        y -= 15
    if bill.discount > 0:
        p.drawString(350, y, f"Discount: Rs. {bill.discount}")
        y -= 15
    p.setFont("Helvetica-Bold", 12)
    p.drawString(350, y, f"Total: Rs. {bill.total}")
    
    # Footer
    p.setFont("Helvetica", 8)
    p.drawString(width/2 - 80, 50, "Thank you for your business!")
    p.drawString(width/2 - 60, 35, "Powered by ShopCloud")
    
    p.showPage()
    p.save()
    
    return response

@login_required
def bill_history(request):
    search = request.GET.get('search', '')
    bills = Bill.objects.filter(shop=request.user.shop)
    
    if search:
        bills = bills.filter(
            Q(bill_number__icontains=search) |
            Q(customer_name__icontains=search) |
            Q(customer_phone__icontains=search)
        )
    
    bills = bills.order_by('-date')[:50]
    return render(request, 'billing/bill_history.html', {'bills': bills, 'search': search})

@login_required
def search_customers(request):
    query = request.GET.get('q', '')
    if len(query) < 2:
        return JsonResponse({'customers': []})
    
    customers = Customer.objects.filter(
        Q(name__icontains=query) | Q(phone__icontains=query),
        shop=request.user.shop
    )[:10]
    
    customer_list = []
    for customer in customers:
        customer_list.append({
            'id': customer.id,
            'name': customer.name,
            'phone': customer.phone,
            'email': customer.email or ''
        })
    
    return JsonResponse({'customers': customer_list})