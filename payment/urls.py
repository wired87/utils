from django.urls import path

from Dashboard.payment.views import Checkout, Unsubscribe
from Dashboard.payment.webhooks import PaymentMessage
app_name = 'payments'
urlpatterns = [
    path('checkout/', Checkout.as_view()),
    path('unsub/', Unsubscribe.as_view()),
    path('stripe-webhook/', PaymentMessage.as_view())
]
