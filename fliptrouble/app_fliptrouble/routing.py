# routing.py

from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/notifications/(?P<username>[^/]+)/$', consumers.NotificationConsumer.as_asgi()),
    re_path(r'ws/othello/(?P<room_name>\w+)/$', consumers.OthelloConsumers.as_asgi()),
    re_path(r'ws/trouble/(?P<room_name>\w+)/$', consumers.TroubleConsumer.as_asgi()),
]
