from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("verify-email/<uuid:token>/", views.verify_email_view, name="verify_email"),

    path("otp/request/", views.request_otp_view, name="request_otp"),
    path("otp/verify/", views.verify_otp_view, name="verify_otp"),

    path("password-reset/", views.password_reset_request_view, name="password_reset"),
    path("reset-password/<uidb64>/<token>/", views.password_reset_confirm_view, name="password_reset_confirm"),

    path("profile/", views.profile_view, name="profile"),
    path("profile/change-password/", views.change_password_view, name="change_password"),

    path("addresses/", views.address_list_view, name="address_list"),
    path("addresses/add/", views.address_add_view, name="address_add"),
    path("addresses/<int:pk>/edit/", views.address_edit_view, name="address_edit"),
    path("addresses/<int:pk>/delete/", views.address_delete_view, name="address_delete"),

    path("saved-cards/", views.saved_cards_view, name="saved_cards"),
    path("saved-cards/add/", views.saved_card_add, name="saved_card_add"),
    path("saved-cards/<int:card_id>/remove/", views.saved_card_remove, name="saved_card_remove"),
    path("saved-cards/<int:card_id>/set-default/", views.saved_card_set_default, name="saved_card_set_default"),

    path("sessions/", views.sessions_view, name="sessions"),
    path("sessions/<str:session_key>/logout/", views.logout_session, name="logout_session"),
    path("sessions/logout-all/", views.logout_all_sessions, name="logout_all_sessions"),
]
