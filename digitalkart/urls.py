from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from products import views as product_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", product_views.home, name="home"),
    path("accounts/", include("accounts.urls")),
    path("products/", include("products.urls")),
    path("category/", include("categories.urls")),
    path("cart/", include("cart.urls")),
    path("wishlist/", include("wishlist.urls")),
    path("orders/", include("orders.urls")),
    path("payments/", include("payments.urls")),
    path("reviews/", include("reviews.urls")),
    path("coupons/", include("coupons.urls")),
    path("dashboard/", include("dashboard.urls")),
    path("search/", include("search.urls")),
    path("notifications/", include("notifications.urls")),
    path("chatbot/", include("chatbot.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

handler404 = "digitalkart.views.error_404"
handler500 = "digitalkart.views.error_500"
