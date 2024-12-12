import json
from app_fliptrouble.models import FriendRequest
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
from channels.generic.websocket import AsyncWebsocketConsumer


# Dictionnaire pour maintenir le comptage des utilisateurs
room_user_counts = {}

class OthelloConsumers(WebsocketConsumer):
    users_in_room = {}  # Dictionnaire pour stocker les utilisateurs et leurs couleurs

    def connect(self):
        # Récupérer le nom de la salle depuis l'URL
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f"othello_{self.room_name}"

        # Ajouter l'utilisateur au groupe
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )

        # Incrémenter le comptage des utilisateurs pour cette salle
        room_user_counts[self.room_group_name] = room_user_counts.get(self.room_group_name, 0) + 1

        # Attribuer une couleur (rouge ou bleu) en fonction de l'ordre d'arrivée
        users_connected = room_user_counts.get(self.room_group_name, 0)
        if users_connected == 1:
            self.color = 'red'  # Premier utilisateur, couleur rouge
        elif users_connected == 2:
            self.color = 'blue'  # Deuxième utilisateur, couleur bleue
        else:
            self.color = None  # Plus de 2 utilisateurs ne sont pas autorisés dans cette version de la partie

        # Sauvegarder l'utilisateur et sa couleur
        self.username = f"Player {users_connected}"
        OthelloConsumers.users_in_room[self.channel_name] = self.color

        # Accepter la connexion WebSocket
        self.accept()

        # Envoyer la couleur de l'utilisateur au frontend
        self.send(text_data=json.dumps({
            'type': 'assign_color',
            'color': self.color,
        }))

        # Gérer le comptage des utilisateurs dans la salle
        self.update_user_count()

    def disconnect(self, close_code):
        """
        Cette méthode est appelée lors de la déconnexion d'un client du WebSocket.
        Elle retire l'utilisateur du groupe et met à jour le comptage des utilisateurs.
        """
        # Retirer l'utilisateur du groupe lors de la déconnexion
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )

        # Décrémenter le comptage des utilisateurs pour cette salle
        if self.room_group_name in room_user_counts:
            room_user_counts[self.room_group_name] -= 1
            if room_user_counts[self.room_group_name] == 0:
                del room_user_counts[self.room_group_name]

        # Supprimer l'utilisateur du dictionnaire
        if self.channel_name in OthelloConsumers.users_in_room:
            del OthelloConsumers.users_in_room[self.channel_name]

        # Mettre à jour le comptage des utilisateurs lors de la déconnexion
        self.update_user_count()

    def update_user_count(self):
        """
        Cette méthode met à jour le nombre d'utilisateurs connectés à la salle.
        Si deux utilisateurs sont présents, la partie démarre automatiquement.
        """
        users_connected = room_user_counts.get(self.room_group_name, 0)

        if users_connected == 2:
            # Si deux utilisateurs sont connectés, démarrer la partie
            self.initiate_game()

    def initiate_game(self):
        """
        Cette méthode envoie un message à tous les clients pour démarrer la partie.
        """
        # Envoyer un message aux utilisateurs pour démarrer la partie
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,  # Groupe spécifique à la salle
            {
                'type': 'start_game',  # Appelle la méthode `start_game`
            }
        )

    def receive(self, text_data):
        """
        Cette méthode est appelée lorsqu'un message est reçu du client.
        Elle transmet le message à tous les membres du groupe.
        """
        text_data_json = json.loads(text_data)
        
        message = text_data_json.get('message', '')
        username = text_data_json.get('username', '')
        message_type = text_data_json.get('type', '')

        if message:  # Si le message est présent
            # Envoyer le message à tous les membres du groupe
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,  # Groupe spécifique à la salle
                {
                    'type': 'chat_message',  # Appelle la méthode `chat_message`
                    'message': message,
                    'username': username  # Ajoute le nom d'utilisateur au message
                }
            )

        if message_type == 'move':  # Si c'est un mouvement de jeu
            row = text_data_json.get('row', -1)
            col = text_data_json.get('col', -1)
            color = text_data_json.get('color', '')

            # Envoi du mouvement à tous les clients connectés
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,
                {
                    'type': 'game_move',
                    'row': row,
                    'col': col,
                    'color': color
                }
            )
        
        if message_type == 'pass_turn':  # Si c'est un signal pour passer le tour
            username = text_data_json.get('username', '')
            
            # Passer le tour et envoyer à l'autre joueur
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,
                {
                    'type': 'change_turn',
                    'username': username,
                }
            )

        if message_type == 'abandon':
            username = text_data_json.get('username', '')
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,
                {
                    'type': 'abandon',
                    'username': username,
                }
            )
    def chat_message(self, event):
        """
        Cette méthode reçoit et envoie le message à tous les clients connectés au groupe.
        """
        message = event['message']
        username = event['username']  # Récupère le nom de l'utilisateur

        self.send(text_data=json.dumps({
            'type': 'chat',
            'message': message,
            'username': username  # Inclut le nom d'utilisateur dans la réponse
        }))

    def start_game(self, event):
        """
        Cette méthode est appelée pour démarrer la partie sur le frontend.
        Elle envoie un message pour signaler au client que la partie doit commencer.
        """
        self.send(text_data=json.dumps({
            'type': 'start_game',  # Type de message pour démarrer le jeu
        }))

    def game_move(self, event):
        """
        Cette méthode envoie un message de mouvement de jeu à tous les clients.
        """
        row = event['row']
        col = event['col']
        color = event['color']

        self.send(text_data=json.dumps({
            'type': 'move',
            'row': row,
            'col': col,
            'color': color
        }))

    def change_turn(self, event):
        """
        Cette méthode est appelée pour signaler à tous les joueurs de changer de tour.
        """
        username = event['username']
        
        if self.color == 'red':
            self.color = 'blue'
        else:
            self.color = 'red'

        self.send(text_data=json.dumps({
            'type': 'change_turn',
            'username': username,
            'color': self.color,
        }))

    def abandon(self, event):
        username = event['username']
        self.send(text_data=json.dumps({
            'type': 'abandon',
            'username': username,
        }))

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.username = self.scope['url_route']['kwargs']['username']
        self.group_name = f'notifications_{self.username}'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def send_notification(self, event):
        notification = event['notification']
        request_id = event.get('request_id')
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'notification': notification,
            'request_id': request_id
        }))

    # accept_request and reject_request logic...

    async def accept_request(self, event):
        request_id = event['request_id']

        # Logic to accept the friend request
        friend_request = await database_sync_to_async(FriendRequest.objects.get)(id=request_id)
        from_user = friend_request.from_user
        to_user = friend_request.to_user

        await database_sync_to_async(from_user.friends.add)(to_user)
        await database_sync_to_async(to_user.friends.add)(from_user)

        await database_sync_to_async(friend_request.delete)()

        # Send a notification to the sender of the request
        await self.channel_layer.group_send(
            f'notifications_{from_user.username}',
            {
                'type': 'send_notification',
                'notification': f'{to_user.username} a accepté votre demande d\'amitié.',
                'request_id': friend_request.id
            }
        )

    async def reject_request(self, event):
        request_id = event['request_id']

        # Logic to reject the friend request
        friend_request = await database_sync_to_async(FriendRequest.objects.get)(id=request_id)
        await database_sync_to_async(friend_request.delete)()



import json
import random


GAME_STATE = {
    'board': [None]*28,
    'players': {
        'blue': {'pions':[{'pos':'home'},{'pos':'home'},{'pos':'home'},{'pos':'home'}]},
        'red': {'pions':[{'pos':'home'},{'pos':'home'},{'pos':'home'},{'pos':'home'}]},
        'green': {'pions':[{'pos':'home'},{'pos':'home'},{'pos':'home'},{'pos':'home'}]},
        'yellow': {'pions':[{'pos':'home'},{'pos':'home'},{'pos':'home'},{'pos':'home'}]}
    },
    'order': ['blue','red','green','yellow'],
    'currentTurnIndex': 0,
    'lastDice': None,
    'started': False,
    'waitingPlayers': []  # liste des couleurs des joueurs réels connectés
}

class TroubleConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f"trouble_{self.room_name}"
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

        # On veut 2 joueurs humains max: bleu, rouge
        # Les bots: green, yellow sont automatiquement ajoutés quand on a 2 joueurs
        if len(GAME_STATE['waitingPlayers']) < 2:
            # Assigner une des deux couleurs humaines
            if 'blue' not in GAME_STATE['waitingPlayers']:
                GAME_STATE['waitingPlayers'].append('blue')
                await self.send(json.dumps({'type':'assign_color','color':'blue'}))
            else:
                GAME_STATE['waitingPlayers'].append('red')
                await self.send(json.dumps({'type':'assign_color','color':'red'}))

        if len(GAME_STATE['waitingPlayers']) == 2 and not GAME_STATE['started']:
            # Ajouter les bots
            # Les bots 'green' et 'yellow' sont ajoutés sans WebSocket
            GAME_STATE['waitingPlayers'].append('green')
            GAME_STATE['waitingPlayers'].append('yellow')
            GAME_STATE['started'] = True
            await self.update_state("Partie démarrée. C'est au tour de blue.")
            # Si c'est un bot, jouer direct, sinon attendre le joueur
            await self.try_bot_play()

    async def receive(self, text_data):
        data = json.loads(text_data)
        msg_type = data.get('type')

        # Vérifier si la partie est commencée
        if not GAME_STATE['started']:
            return

        if msg_type == 'roll_dice':
            color = self.current_turn_color()
            # Vérifier si c'est un humain autorisé
            if color in ['blue','red'] and color in GAME_STATE['waitingPlayers']:
                await self.handle_roll_dice()
                # Après le lancer de dé, attendre le move_pion
            else:
                # Pas le tour d'un humain
                return

        if msg_type == 'move_pion':
            color = data['color']
            if color != self.current_turn_color():
                return
            pionIndex = data['pionIndex']
            steps = data['steps']
            await self.handle_move_pion(color, pionIndex, steps)
            # Après le move_pion, si fin, update. Sinon, si steps!=6, next turn.
            # Si bot ensuite, play bot
            await self.try_bot_play()

    def current_turn_color(self):
        return GAME_STATE['order'][GAME_STATE['currentTurnIndex']]

    async def handle_roll_dice(self):
        value = random.randint(1,6)
        GAME_STATE['lastDice'] = value
        await self.channel_layer.group_send(
            self.room_group_name,
            {'type': 'send_dice_result','value':value}
        )

    async def handle_move_pion(self, color, pionIndex, steps):
        pion = GAME_STATE['players'][color]['pions'][pionIndex]
        oldPos = pion['pos']
        if oldPos == 'home':
            if steps == 6:
                if GAME_STATE['board'][0] is not None:
                    await self.return_home(GAME_STATE['board'][0])
                GAME_STATE['board'][0] = {'color':color,'pionIndex':pionIndex}
                pion['pos'] = 0
            else:
                await self.update_state("Pas de 6, pas de sortie.")
                return
        else:
            # Sur board ou finish
            if oldPos == 'finish':
                # Déjà en finish ? Plus de move.
                await self.update_state("Ce pion est déjà dans la zone d'arrivée.")
                return
            newPos = oldPos + steps
            if newPos > 28:
                # on doit atterrir pile sur 28 (si 28 est finish)
                # On considèrera que finish c'est juste 'finish' si newPos == 28 exactement
                if newPos == 28:
                    # Finish
                    GAME_STATE['board'][oldPos] = None
                    pion['pos'] = 'finish'
                else:
                    await self.update_state("Mouvement impossible (doit être exact).")
                    return
            elif newPos == 28:
                # pile finish
                GAME_STATE['board'][oldPos] = None
                pion['pos'] = 'finish'
            else:
                # Nouveau pos sur board
                GAME_STATE['board'][oldPos] = None
                if GAME_STATE['board'][newPos] is not None:
                    await self.return_home(GAME_STATE['board'][newPos])
                GAME_STATE['board'][newPos] = {'color':color,'pionIndex':pionIndex}
                pion['pos'] = newPos

        # Check win
        if self.check_winner(color):
            await self.update_state(f"{color} a gagné !")
            return

        # Fin du coup
        if steps != 6:
            GAME_STATE['lastDice'] = None
            self.next_turn()
            await self.update_state(f"C'est au tour de {self.current_turn_color()}.")
        else:
            # a un 6, rejoue le même joueur
            GAME_STATE['lastDice'] = None
            await self.update_state(f"{color} a obtenu un 6, rejouez.")

    async def return_home(self, occupant):
        occColor = occupant['color']
        occPionIndex = occupant['pionIndex']
        GAME_STATE['players'][occColor]['pions'][occPionIndex]['pos'] = 'home'

    def next_turn(self):
        GAME_STATE['currentTurnIndex'] = (GAME_STATE['currentTurnIndex'] + 1) % len(GAME_STATE['order'])

    def check_winner(self, color):
        pions = GAME_STATE['players'][color]['pions']
        return all(p['pos'] == 'finish' for p in pions)

    async def update_state(self, message=""):
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'send_update',
                'board': GAME_STATE['board'],
                'players': GAME_STATE['players'],
                'currentTurn': self.current_turn_color(),
                'lastDice': GAME_STATE['lastDice'],
                'message': message
            }
        )


    def update_state(message=""):
        pusher_client.trigger('my-channel', 'my-event', {
        'board': GAME_STATE['board'],
        'players': GAME_STATE['players'],
        'currentTurn': current_turn_color(),
        'lastDice': GAME_STATE['lastDice'],
        'message': message
    })


    async def send_dice_result(self, event):
        await self.send(text_data=json.dumps({
            'type':'dice_result',
            'value': event['value']
        }))

    async def send_update(self, event):
        await self.send(text_data=json.dumps({
            'type':'update_state',
            'board': event['board'],
            'players': event['players'],
            'currentTurn': event['currentTurn'],
            'lastDice': event['lastDice'],
            'message': event['message']
        }))

    async def try_bot_play(self):
        # Si c'est un bot, jouer automatiquement
        color = self.current_turn_color()
        if color in ['green','yellow']:
            # Bot
            await self.bot_turn(color)

    async def bot_turn(self, color):
        # Le bot lance le dé
        await self.handle_roll_dice()
        value = GAME_STATE['lastDice']

        # Tenter de jouer un pion
        # Stratégie simple : s'il peut sortir un pion de home avec 6, le faire
        # sinon, bouger un pion sur le board
        played = await self.bot_play_pion(color, value)
        if not played:
            # Aucune action possible, passer tour
            if value != 6:
                self.next_turn()
                await self.update_state(f"{self.current_turn_color()} au tour.")
            else:
                # a obtenu 6 mais aucune action possible, on retente ?
                # Pour éviter boucle infinie, on passe le tour
                self.next_turn()
                await self.update_state(f"{self.current_turn_color()} au tour.")

        else:
            # S'il a joué un pion
            # handle_move_pion gère déjà le passage de tour si steps !=6
            # Si steps=6, c'est encore lui, rejouer
            # On vérifie si encore lui et si c'est un bot, on rejoue
            await self.try_bot_play()

    async def bot_play_pion(self, color, steps):
        # Si steps == 6, vérifier si on peut sortir un pion de la home
        if steps == 6:
            # Y a-t-il un pion en home ?
            for i, p in enumerate(GAME_STATE['players'][color]['pions']):
                if p['pos'] == 'home':
                    # Essayer de sortir ce pion
                    # On envoie direct handle_move_pion
                    await self.handle_move_pion(color, i, steps)
                    return True
        # Sinon bouger un pion sur le board
        # Trouver un pion déplaçable
        for i, p in enumerate(GAME_STATE['players'][color]['pions']):
            if p['pos'] not in ['home','finish']:
                # pion sur board
                oldPos = p['pos']
                newPos = oldPos+steps
                # Vérifier si on peut finir ou avancer
                if newPos == 28 or (newPos < 28 and newPos >=0 and newPos< len(GAME_STATE['board'])):
                    # On tente ce move
                    await self.handle_move_pion(color, i, steps)
                    return True
                # Sinon si on dépasse 28 sans être exact, pas possible
        # Aucun move possible
        return False
