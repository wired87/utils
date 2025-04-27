from django.conf import settings
from django.conf.urls.static import static
from django.urls import path

from Dashboard.bot.Apify.webhooks.views import DataCollecting

app_name = 'bot-webhooks'

urlpatterns = [
    path('status/', DataCollecting.as_view()),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
