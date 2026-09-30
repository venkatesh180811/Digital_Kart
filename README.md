# DigitalKart

An original, Flipkart-**inspired** e-commerce learning project built with Django 5, MySQL, and vanilla JS.
No Flipkart code, images, logos, or trademarks are used anywhere — the design, copy, and codebase are original.

## Status: Part 1 of a multi-part build

This is a large project (12 Django apps, 17+ database tables, 3 payment paths, seller + admin panels).
It's being generated in phases so each app is real, working code — not filler. **Implemented so far:**

| App | Status |
|---|---|
| `accounts` | ✅ Full — register, email verification, login, OTP login, password reset, profile, addresses |
| `categories` | ✅ Full — categories, subcategories, brands, nav menu |
| `products` | ✅ Core — model, home page, listing with filters/sort/pagination, detail page, seller product list |
| `cart` | ✅ Full — add/update/remove, save for later, GST + shipping calculation |
| `wishlist` | ✅ Full — add/remove/move to cart |
| `orders` | ✅ Full — checkout, order history, tracking, cancel, return requests |
| `payments` | ✅ Sandboxed — COD live; Razorpay/Stripe wired with a simulated callback (real key integration is a follow-up) |
| `reviews` | ✅ Core — star ratings, verified purchase flag |
| `coupons` | ✅ Core — percent/flat coupons, session-based apply |
| `dashboard` | ✅ Core — seller registration + seller sales dashboard |
| `search` | ✅ Core — live search, autocomplete endpoint |
| `notifications` | ✅ Core — in-app notification list |
| **Still to come** | Product image zoom/gallery JS, admin analytics dashboards (revenue/inventory charts), invoice PDF generation, frequently-bought-together logic, dark mode, sample data fixtures, and automated tests |

Ask for the next app or feature by name (e.g. "build the invoice PDF" or "add dark mode") and it'll be generated the same way — fully, in its own pass.

## Tech Stack
- **Backend:** Python 3.12, Django 5
- **Database:** MySQL 8
- **Frontend:** HTML5, CSS3 (custom design system, no Bootstrap dependency), vanilla JS
- **Auth:** Django auth with custom email-based `User` model, email verification, OTP login
- **Payments:** Cash on Delivery (live), Razorpay + Stripe (sandboxed simulation — swap in real API calls when you have gateway keys)

## Project Structure
```
digitalkart/
├── manage.py
├── digitalkart/          # settings, root urls, wsgi/asgi
├── accounts/              # auth, profile, addresses
├── products/               # catalog, home page
├── categories/              # categories, subcategories, brands
├── cart/                     # shopping cart
├── wishlist/                  # wishlist
├── orders/                     # checkout, order history, returns
├── payments/                    # payment gateway integration
├── reviews/                      # ratings & reviews
├── coupons/                       # discount coupons
├── dashboard/                      # seller registration & seller dashboard
├── search/                          # search + autocomplete
├── notifications/                    # in-app notifications
├── templates/                         # base.html, error pages
├── static/                             # css/js/images
└── media/                                # uploaded images
```

## Setup Instructions

1. **Create a virtual environment and install dependencies**
   ```bash
   python -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Create your `.env` file**
   ```bash
   cp .env.example .env
   # then edit .env with your real MySQL credentials and secret key
   ```

3. **Create the MySQL database**
   ```sql
   CREATE DATABASE digitalkart_db CHARACTER SET utf8mb4;
   ```

4. **Run migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

5. **Create an admin superuser**
   ```bash
   python manage.py createsuperuser
   ```

6. **Run the development server**
   ```bash
   python manage.py runserver
   ```
   Visit `http://127.0.0.1:8000/` for the storefront and `http://127.0.0.1:8000/admin/` for the admin panel.

## Testing
- Run `python manage.py test` once test modules are added (see roadmap above).
- In the meantime, exercise the flows manually: register → verify email (check console output for the link, since `EMAIL_BACKEND` defaults to console) → log in → browse a category → add to cart → checkout with a saved address → simulate payment → view order.
- To try selling: log in, visit **Become a Seller**, register a business, then add products via `/admin/` (a dedicated "add product" seller UI is on the roadmap) — set `is_active=True` and add at least one `ProductImage` so it appears on the storefront.

## Deployment Notes (production checklist)
- Set `DJANGO_DEBUG=False` and a strong `DJANGO_SECRET_KEY`.
- Point `EMAIL_BACKEND` to a real SMTP backend and set real credentials.
- Add real `RAZORPAY_KEY_ID` / `STRIPE_SECRET_KEY` values, and replace the simulated callback in `payments/views.py` with real gateway verification (webhook signature checks) before going live.
- Run `python manage.py collectstatic` and serve `staticfiles/` via whitenoise or a CDN.
- Put MySQL, static, and media storage behind proper backups.
- Run behind Gunicorn + Nginx (or your platform's equivalent) with HTTPS enforced.

## Security Notes
- CSRF protection is on by default (Django middleware); all forms include `{% csrf_token %}`.
- Passwords are hashed via Django's PBKDF2 hasher — never stored in plaintext.
- Card details are never stored — `accounts.SavedCard` stores only a gateway token + last 4 digits.
- `AUTH_PASSWORD_VALIDATORS` enforces minimum length and blocks common/numeric-only passwords.
- Role-based access: `is_seller` and Django's `is_staff`/`is_superuser` gate seller and admin features.
