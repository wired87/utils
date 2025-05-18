from django.urls import path

from utils.simulator.dj.views.create_world import CreateWorldView
from utils.simulator.dj.views.runner import WorldRunnerTestView, SimulationWebsocket

app_name = 'world'
urlpatterns = [
    path('create/', CreateWorldView.as_view()),
    path('test/', WorldRunnerTestView.as_view()),
    path('run/', SimulationWebsocket.as_view()),
]
