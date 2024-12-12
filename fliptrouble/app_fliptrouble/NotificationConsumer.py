# consumers.py

import json
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync

class NotificationConsumer(WebsocketConsumer):

    def connect(self):
        self.username = self.scope['url_route']['kwargs']['username']
        self.group_name = f"notifications_{self.username}"

        # Ajouter l'utilisateur au groupe de notifications
        async_to_sync(self.channel_layer.group_add)(
            self.group_name,
            self.channel_name
        )

        # Accepter la connexion WebSocket
        self.accept()

    def disconnect(self, close_code):
        # Retirer l'utilisateur du groupe de notifications lors de la déconnexion
        async_to_sync(self.channel_layer.group_discard)(
            self.group_name,
            self.channel_name
        )

    def receive(self, text_data):
        # Ne gère pas la réception de messages du client pour le moment
        pass

    def send_notification(self, event):
        # Envoyer une notification au client
        notification = event['notification']
        self.send(text_data=json.dumps({
            'type': 'notification',
            'notification': notification
        }))
