def wishlist_summary(request):
    if request.user.is_authenticated:
        return {"wishlist_count": request.user.wishlist_items.count()}
    return {"wishlist_count": 0}
