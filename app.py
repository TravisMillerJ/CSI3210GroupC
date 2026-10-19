"""
GamersGear — CSI 3210 Group C Final Project
Oakland University · Fall 2026

Built on the HW01 ShopUX starter. A mock PC parts & peripherals store
for student gamers. Every page fires a PostHog event via the Python SDK.
Prices are mock values for demo purposes.

Run:
    conda activate csi3210
    cd app
    pip install flask>=3.0 posthog>=3.0
    python app.py
Then open http://127.0.0.1:5000
"""

import uuid
from posthog import Posthog
from flask import Flask, render_template, session, redirect, url_for, request
from config import POSTHOG_API_KEY, POSTHOG_HOST, STUDENT_NAME, STUDENT_EMAIL

# ── PostHog setup ─────────────────────────────────────────────
ph = Posthog(project_api_key=POSTHOG_API_KEY, host=POSTHOG_HOST, sync_mode=True)

# ── Flask setup ───────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = 'csi3210-posthog-lab'

# Bias fields used by templates/products.html:
#   sold  -> social proof badge ("Bestseller · N OU students bought this")
#   was   -> anchoring (crossed-out original price)
#   stock -> scarcity ("Only N left in stock")
PRODUCTS = [
    {'id': 'p1', 'title': 'G305 Wireless Gaming Mouse',   'brand': 'Logitech G', 'category': 'Peripheral', 'icon': '🖱️',
     'price': 39.99,  'was': None,   'stock': 24, 'sold': 48},
    {'id': 'p2', 'title': 'Ryzen 5 7600 Processor',       'brand': 'AMD',        'category': 'Component',  'icon': '🧠',
     'price': 189.99, 'was': 229.99, 'stock': 15, 'sold': 0},
    {'id': 'p3', 'title': '32GB DDR5-6000 RAM Kit',       'brand': 'Crucial',    'category': 'Component',  'icon': '💾',
     'price': 89.99,  'was': None,   'stock': 3,  'sold': 0},
    {'id': 'p4', 'title': 'K552 Mechanical Keyboard',     'brand': 'Redragon',   'category': 'Peripheral', 'icon': '⌨️',
     'price': 34.99,  'was': None,   'stock': 30, 'sold': 0},
    {'id': 'p5', 'title': '990 EVO 1TB NVMe SSD',         'brand': 'Samsung',    'category': 'Component',  'icon': '⚡',
     'price': 79.99,  'was': 99.99,  'stock': 12, 'sold': 0},
    {'id': 'p6', 'title': 'Cloud III Gaming Headset',     'brand': 'HyperX',     'category': 'Peripheral', 'icon': '🎧',
     'price': 69.99,  'was': None,   'stock': 2,  'sold': 31},
    {'id': 'p7', 'title': 'GeForce RTX 4060 8GB GPU',     'brand': 'NVIDIA',     'category': 'Component',  'icon': '🎮',
     'price': 299.99, 'was': 329.99, 'stock': 4,  'sold': 57},
    {'id': 'p8', 'title': 'B650 Gaming WiFi Motherboard', 'brand': 'MSI',        'category': 'Component',  'icon': '🔌',
     'price': 159.99, 'was': None,   'stock': 18, 'sold': 0},
    {'id': 'p9', 'title': 'RM750e 750W Power Supply',     'brand': 'Corsair',    'category': 'Component',  'icon': '🔋',
     'price': 99.99,  'was': None,   'stock': 20, 'sold': 0},
    {'id': 'p10', 'title': '4000D Airflow Mid-Tower Case', 'brand': 'Corsair',   'category': 'Component',  'icon': '🖥️',
     'price': 94.99,  'was': 104.99, 'stock': 9,  'sold': 0},
]

def get_uid():
    """Return a stable anonymous ID for this browser session."""
    if 'uid' not in session:
        session['uid'] = str(uuid.uuid4())
    return session['uid']


# ── Routes ────────────────────────────────────────────────────

@app.route('/')
def home():
    uid = get_uid()
    ph.capture(distinct_id=uid, event='page_view', properties={
        'page':  'home',
        'title': 'GamersGear — PC Parts & Peripherals',
    })
    return render_template('home.html', uid=uid)


@app.route('/products')
def products():
    uid = get_uid()
    ph.capture(distinct_id=uid, event='page_view', properties={'page': 'products'})
    ph.capture(distinct_id=uid, event='viewed_product_list', properties={
        'category': 'PC Parts',
        'count':    len(PRODUCTS),
    })
    return render_template('products.html', uid=uid, products=PRODUCTS)


@app.route('/cart')
def cart():
    uid     = get_uid()
    pid     = request.args.get('id', 'p1')
    product = next((p for p in PRODUCTS if p['id'] == pid), PRODUCTS[0])
    session['cart_item'] = product
    ph.capture(distinct_id=uid, event='added_to_cart', properties={
        'product_id':   product['id'],
        'product_name': product['title'],
        'price':        product['price'],
    })
    return render_template('cart.html', uid=uid, product=product)


@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    uid     = get_uid()
    product = session.get('cart_item', PRODUCTS[0])

    if request.method == 'POST':
        name  = request.form.get('name',  STUDENT_NAME)
        email = request.form.get('email', STUDENT_EMAIL)
        ph.capture(distinct_id=uid, event='$identify', properties={
            '$set': {
                'name':   name,
                'email':  email,
                'course': 'CSI3210',
            }
        })
        ph.capture(distinct_id=uid, event='started_checkout', properties={
            'cart_value': product['price'],
            'student':    name,
        })
        return redirect(url_for('confirmation'))

    ph.capture(distinct_id=uid, event='page_view', properties={'page': 'checkout'})
    return render_template('checkout.html', uid=uid, product=product,
                           default_name=STUDENT_NAME, default_email=STUDENT_EMAIL)


@app.route('/confirmation')
def confirmation():
    uid      = get_uid()
    product  = session.get('cart_item', PRODUCTS[0])
    order_id = f'ORD-{uid[:8].upper()}'
    ph.capture(distinct_id=uid, event='completed_purchase', properties={
        'order_id':   order_id,
        'product_id': product['id'],
        'revenue':    product['price'],
    })
    return render_template('confirmation.html', uid=uid,
                           product=product, order_id=order_id)


@app.route('/reset')
def reset():
    """Clear the session so students can run through the funnel again as a new user."""
    session.clear()
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)