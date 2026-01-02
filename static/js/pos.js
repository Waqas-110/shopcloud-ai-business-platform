let cart = {};

document.addEventListener('DOMContentLoaded', function() {
    loadCart();
    setupEventListeners();
});

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function setupEventListeners() {
    document.getElementById('productSearch').addEventListener('input', searchProducts);
    
    document.querySelectorAll('.category-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            document.querySelectorAll('.category-btn').forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            filterByCategory(this.dataset.category);
        });
    });
    
    document.querySelectorAll('.add-to-cart').forEach(btn => {
        btn.addEventListener('click', function() {
            addToCart(this.dataset.id);
        });
    });
    
    document.getElementById('clearCart').addEventListener('click', clearCart);
    document.getElementById('generateBill').addEventListener('click', generateBill);
}

function searchProducts() {
    const query = document.getElementById('productSearch').value;
    if (query.length < 2) return;
    
    fetch(`/billing/search-products/?q=${query}`)
        .then(response => response.json())
        .then(data => {
            updateProductsGrid(data.products);
        });
}

function filterByCategory(categoryId) {
    const products = document.querySelectorAll('.product-card');
    products.forEach(product => {
        if (categoryId === 'all' || product.dataset.category === categoryId) {
            product.style.display = 'block';
        } else {
            product.style.display = 'none';
        }
    });
}

function addToCart(productId) {
    fetch('/billing/add-to-cart/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({product_id: productId, quantity: 1})
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            cart = data.cart;
            updateCartDisplay();
        } else {
            alert(data.error);
        }
    });
}

function updateCartDisplay() {
    const cartItems = document.getElementById('cartItems');
    cartItems.innerHTML = '';
    
    let subtotal = 0;
    
    for (const [id, item] of Object.entries(cart)) {
        subtotal += item.price * item.quantity;
        cartItems.innerHTML += `
            <div class="cart-item">
                <div class="item-name">${item.name}</div>
                <div class="quantity-controls">
                    <button class="qty-btn" onclick="updateQuantity('${id}', ${item.quantity - 1})">-</button>
                    <span>${item.quantity}</span>
                    <button class="qty-btn" onclick="updateQuantity('${id}', ${item.quantity + 1})">+</button>
                </div>
                <div>Rs. ${item.price}</div>
                <div>Rs. ${(item.price * item.quantity).toFixed(2)}</div>
                <button class="remove-item" onclick="removeFromCart('${id}')">×</button>
            </div>
        `;
    }
    
    document.getElementById('subtotal').textContent = `Rs. ${subtotal.toFixed(2)}`;
    document.getElementById('total').textContent = `Rs. ${subtotal.toFixed(2)}`;
}

function updateQuantity(productId, newQuantity) {
    if (newQuantity <= 0) {
        removeFromCart(productId);
        return;
    }
    
    fetch('/billing/update-cart/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({product_id: productId, quantity: newQuantity})
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            cart = data.cart;
            updateCartDisplay();
        }
    });
}

function removeFromCart(productId) {
    fetch('/billing/remove-from-cart/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({product_id: productId})
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            cart = data.cart;
            updateCartDisplay();
        }
    });
}

function clearCart() {
    fetch('/billing/clear-cart/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            cart = {};
            updateCartDisplay();
        }
    });
}

function generateBill() {
    if (Object.keys(cart).length === 0) {
        alert('Please add items to cart first!');
        return;
    }
    
    const subtotal = Object.values(cart).reduce((sum, item) => sum + (item.price * item.quantity), 0);
    
    const billData = {
        customer_name: document.getElementById('customerName').value,
        customer_phone: document.getElementById('customerPhone').value,
        payment_type: document.getElementById('paymentMethod').value,
        subtotal: subtotal,
        tax: 0,
        discount: 0,
        total: subtotal
    };
    
    fetch('/billing/create-bill/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify(billData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            window.location.href = `/billing/bill/${data.bill_id}/`;
        } else {
            alert('Error: ' + data.error);
        }
    });
}

function loadCart() {
    updateCartDisplay();
}