from django.urls import path

from utils.simulator.dj.views.world import CreateWorldView

app_name = 'world'
urlpatterns = [
    path('create/', CreateWorldView.as_view()),

]
