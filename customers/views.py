from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count
from django.contrib import messages
from billing.models import Customer, Bill
from shopcloud.language_utils import get_user_language, get_template_name

@login_required
def customers_list(request):
    shop = request.user.shop
    customers = Customer.objects.filter(shop=shop).order_by('-created_at')
    
    # Add bill stats manually
    for customer in customers:
        customer_bills = Bill.objects.filter(
            shop=shop,
            customer_phone=customer.phone
        )
        customer.total_bills = customer_bills.count()
        customer.total_spent = customer_bills.aggregate(Sum('total'))['total__sum'] or 0
    
    language = get_user_language(request)
    template_name = get_template_name('customers/list.html', language)
    
    context = {
        'customers': customers,
    }
    return render(request, template_name, context)

@login_required
def customer_detail(request, customer_id):
    shop = request.user.shop
    customer = get_object_or_404(Customer, id=customer_id, shop=shop)
    
    bills = Bill.objects.filter(
        shop=shop,
        customer_phone=customer.phone
    ).order_by('-date')
    
    stats = {
        'total_bills': bills.count(),
        'total_spent': bills.aggregate(Sum('total'))['total__sum'] or 0,
        'avg_bill': bills.aggregate(Sum('total'))['total__sum'] / bills.count() if bills.count() > 0 else 0
    }
    
    context = {
        'customer': customer,
        'bills': bills,
        'stats': stats,
    }
    return render(request, 'customers/detail.html', context)

@login_required
def add_customer(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        phone = request.POST.get('phone')
        email = request.POST.get('email')
        address = request.POST.get('address')
        
        if name and phone:
            # Check if customer already exists
            existing = Customer.objects.filter(
                shop=request.user.shop,
                phone=phone
            ).first()
            
            if not existing:
                customer = Customer.objects.create(
                    name=name,
                    phone=phone,
                    email=email or '',
                    address=address or '',
                    shop=request.user.shop
                )
                
                # Return JSON for AJAX requests
                if request.headers.get('Content-Type') == 'application/x-www-form-urlencoded':
                    from django.http import JsonResponse
                    return JsonResponse({
                        'success': True,
                        'customer': {
                            'id': customer.id,
                            'name': customer.name,
                            'phone': customer.phone,
                            'email': customer.email
                        }
                    })
            
            messages.success(request, 'Customer added successfully!')
            return redirect('customers:list')
        else:
            messages.error(request, 'Name and phone are required!')
    
    language = get_user_language(request)
    template_name = get_template_name('customers/add.html', language)
    
    return render(request, template_name)

@login_required
def customers_list_ur(request):
    shop = request.user.shop
    customers = Customer.objects.filter(shop=shop).order_by('-created_at')
    
    # Add bill stats manually
    for customer in customers:
        customer_bills = Bill.objects.filter(
            shop=shop,
            customer_phone=customer.phone
        )
        customer.total_bills = customer_bills.count()
        customer.total_spent = customer_bills.aggregate(Sum('total'))['total__sum'] or 0
    
    context = {
        'customers': customers,
    }
    return render(request, 'customers/list_ur.html', context)

@login_required
def add_customer_ur(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        phone = request.POST.get('phone')
        email = request.POST.get('email')
        address = request.POST.get('address')
        
        if name:
            Customer.objects.create(
                name=name,
                phone=phone,
                email=email,
                address=address,
                shop=request.user.shop
            )
            messages.success(request, 'کسٹمر کامیابی سے شامل ہو گیا!')
            return redirect('customers:list_ur')
        else:
            messages.error(request, 'نام ضروری ہے!')
    
    return render(request, 'customers/add_ur.html')