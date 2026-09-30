from .models import Category


def categories_menu(request):
    """Exposes the active category list to every template (navbar dropdown)."""
    return {"nav_categories": Category.objects.filter(is_active=True).order_by("name")}
