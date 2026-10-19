"""
CA — PostHog UX Analytics Lab
CSI 3210 · Oakland University

Scenario: ShopUX — a three-step UX-book e-commerce checkout funnel.
Students navigate through the app while PostHog records every event,
then explore the data in the PostHog dashboard.

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

PRODUCTS = [
    {'id': 'p1', 'title': "Don't Make Me Think",           'author': 'Steve Krug',      'price': 29.99},
    {'id': 'p2', 'title': 'The Design of Everyday Things', 'author': 'Don Norman',      'price': 24.99},
    {'id': 'p3', 'title': 'Lean UX',                       'author': 'Gothelf & Seiden','price': 34.99},
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
        'title': 'ShopUX — UX Design Books',
    })
    return render_template('home.html', uid=uid)


@app.route('/products')
def products():
    uid = get_uid()
    ph.capture(distinct_id=uid, event='page_view', properties={'page': 'products'})
    ph.capture(distinct_id=uid, event='viewed_product_list', properties={
        'category': 'UX Books',
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
