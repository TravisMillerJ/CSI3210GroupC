/* ShopUX — replaces app.py. Events now fire from the browser via posthog-js. */

// ── PostHog loader (official snippet) ─────────────────────────
!function(t,e){var o,n,p,r;e.__SV||(window.posthog=e,e._i=[],e.init=function(i,s,a){function g(t,e){var o=e.split(".");2==o.length&&(t=t[o[0]],e=o[1]),t[e]=function(){t.push([e].concat(Array.prototype.slice.call(arguments,0)))}}(p=t.createElement("script")).type="text/javascript",p.crossOrigin="anonymous",p.async=!0,p.src=s.api_host.replace(".i.posthog.com","-assets.i.posthog.com")+"/static/array.js",(r=t.getElementsByTagName("script")[0]).parentNode.insertBefore(p,r);var u=e;for(void 0!==a?u=e[a]=[]:a="posthog",u.people=u.people||[],u.toString=function(t){var e="posthog";return"posthog"!==a&&(e+="."+a),t||(e+=" (stub)"),e},u.people.toString=function(){return u.toString(1)+".people (stub)"},o="init capture register register_once register_for_session unregister unregister_for_session getFeatureFlag getFeatureFlagPayload isFeatureEnabled reloadFeatureFlags on onFeatureFlags onSessionId identify setPersonProperties group resetGroups reset get_distinct_id get_session_id alias set_config opt_in_capturing opt_out_capturing debug".split(" "),n=0;n<o.length;n++)g(u,o[n]);e._i.push([i,s,a])},e.__SV=1)}(document,window.posthog||[]);

const CFG = window.SHOPUX_CONFIG;
posthog.init(CFG.POSTHOG_API_KEY, {
  api_host: CFG.POSTHOG_HOST,
  capture_pageview: false,      // we send our own named events
  autocapture: false,
  persistence: 'sessionStorage' // like Flask's session: "Reset" = new user
});

// ── Data ──────────────────────────────────────────────────────
const PRODUCTS = [
  { id: 'p1', title: "Don't Make Me Think",           author: 'Steve Krug',       price: 29.99 },
  { id: 'p2', title: 'The Design of Everyday Things', author: 'Don Norman',       price: 24.99 },
  { id: 'p3', title: 'Lean UX',                       author: 'Gothelf & Seiden', price: 34.99 }
];

const money = n => '$' + n.toFixed(2);
const uid   = () => posthog.get_distinct_id();
const cartItem = () => JSON.parse(sessionStorage.getItem('cart_item') || 'null') || PRODUCTS[0];
const $ = sel => document.querySelector(sel);

// ── Shared page chrome (header, step bar, footer) ─────────────
const STEPS = ['Home', 'Browse', 'Cart', 'Checkout', 'Confirmed'];
const PAGES = { home: 0, products: 1, cart: 2, checkout: 3, confirmation: 4 };
const CIRCLED = ['①','②','③','④','⑤'];

function renderChrome(page) {
  document.body.insertAdjacentHTML('afterbegin', `
    <header>
      <a href="index.html" style="color:#f8fafc; font-weight:700; font-size:1.1rem;">📚 ShopUX</a>
      <nav>
        <a href="index.html">Home</a>
        <a href="products.html">Books</a>
        <a href="#" id="reset-link">↺ Reset session</a>
      </nav>
    </header>`);
  document.body.insertAdjacentHTML('beforeend',
    `<footer>CSI 3210 — PostHog Lab · User ID: <span id="uid"></span></footer>`);
  $('#uid').textContent = uid();

  const bar = $('#step-bar');
  if (bar) {
    const cur = PAGES[page];
    bar.className = 'step-bar';
    bar.innerHTML = STEPS.map((s, i) => {
      const cls = page === 'confirmation' || i < cur ? 'done' : i === cur ? 'active' : '';
      return `<span class="${cls}">${CIRCLED[i]} ${s}</span>`;
    }).join('');
  }
  document.querySelectorAll('#reset-link, [data-reset]').forEach(a =>
    a.addEventListener('click', e => { e.preventDefault(); resetSession(); }));
}

// Replaces Flask's /reset route
function resetSession() {
  sessionStorage.clear();
  posthog.reset();                // new anonymous distinct_id
  location.href = 'index.html';
}

// ── Page logic (replaces each Flask route) ────────────────────
const pageHandlers = {
  home() {
    posthog.capture('page_view', { page: 'home', title: 'ShopUX — UX Design Books' });
  },

  products() {
    posthog.capture('page_view', { page: 'products' });
    posthog.capture('viewed_product_list', { category: 'UX Books', count: PRODUCTS.length });
    $('#product-count').textContent = PRODUCTS.length;
    $('#product-list').innerHTML = PRODUCTS.map(p => `
      <div class="card" style="display:flex; justify-content:space-between; align-items:center; gap:1rem;">
        <div>
          <p style="font-weight:700; font-size:1.05rem;">${p.title}</p>
          <p style="color:#64748b; font-size:0.88rem;">${p.author}</p>
        </div>
        <div style="text-align:right; flex-shrink:0;">
          <p style="font-weight:700; font-size:1.1rem; margin-bottom:0.5rem;">${money(p.price)}</p>
          <a href="cart.html?id=${p.id}" class="btn btn-primary">Add to Cart</a>
        </div>
      </div>`).join('');
  },

  cart() {
    const id = new URLSearchParams(location.search).get('id') || 'p1';
    const product = PRODUCTS.find(p => p.id === id) || PRODUCTS[0];
    sessionStorage.setItem('cart_item', JSON.stringify(product));
    posthog.capture('added_to_cart', {
      product_id: product.id, product_name: product.title, price: product.price
    });
    $('#badge').textContent = `added_to_cart {product: '${product.title}', price: ${product.price}}`;
    $('#title').textContent  = product.title;
    $('#author').textContent = product.author;
    $('#price').textContent  = money(product.price);
    $('#total').textContent  = money(product.price);
  },

  checkout() {
    const product = cartItem();
    posthog.capture('page_view', { page: 'checkout' });
    $('#name').value  = CFG.STUDENT_NAME;
    $('#email').value = CFG.STUDENT_EMAIL;
    $('#summary').textContent = `${product.title} — ${money(product.price)}`;

    $('#checkout-form').addEventListener('submit', e => {
      e.preventDefault();
      const name  = $('#name').value  || CFG.STUDENT_NAME;
      const email = $('#email').value || CFG.STUDENT_EMAIL;
      // posthog.identify() is the browser equivalent of the $identify event
      posthog.identify(uid(), { name, email, course: 'CSI3210' });
      posthog.capture('started_checkout', { cart_value: product.price, student: name });
      // flush before navigating away
      setTimeout(() => { location.href = 'confirmation.html'; }, 250);
    });
  },

  confirmation() {
    const product  = cartItem();
    const orderId  = 'ORD-' + uid().slice(0, 8).toUpperCase();
    posthog.capture('completed_purchase', {
      order_id: orderId, product_id: product.id, revenue: product.price
    });
    $('#order-id').textContent      = orderId;
    $('#product-title').textContent = product.title;
    $('#event-props').textContent   = `{order_id: '${orderId}', revenue: ${product.price}}`;
  }
};

document.addEventListener('DOMContentLoaded', () => {
  const page = document.body.dataset.page;
  renderChrome(page);
  pageHandlers[page]();
});
