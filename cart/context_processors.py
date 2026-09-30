def cart_summary(request):
    cart = getattr(request, "cart", None)
    return {"cart_count": cart.total_items if cart else 0}
