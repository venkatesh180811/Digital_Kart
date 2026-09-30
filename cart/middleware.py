class CartMiddleware:
    """Ensures every authenticated request has request.cart available."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            from .models import Cart
            cart, _ = Cart.objects.get_or_create(user=request.user)
            request.cart = cart
        else:
            request.cart = None
        return self.get_response(request)
