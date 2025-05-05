from django.urls import path

from utils.simulator.dj.views.create_world import CreateWorldView
from utils.simulator.dj.views.runner import WorldRunnerView

app_name = 'world'
urlpatterns = [
    path('create/', CreateWorldView.as_view()),
    path('run/', WorldRunnerView.as_view()),
]
