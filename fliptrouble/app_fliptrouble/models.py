from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from django.db import models
from datetime import timedelta
from django.utils.timezone import now

tableau = [
    (0, 'Jeux'),
    (1, 'Général'),
    (2, 'Humour'),
]

JEUX_CHOICES = [
    ('othello', 'Othello'),
    ('trouble', 'Trouble'),
]

class User(AbstractUser):
    courriel = models.EmailField(unique=True)
    adresse = models.CharField(max_length=255, blank=True, null=True)
    sexe = models.CharField(max_length=10, blank=True, null=True)
    date_de_naissance = models.DateField(null=True, blank=True)
    telephone = models.CharField(max_length=15, blank=True, null=True)
    est_moderateur = models.BooleanField(default=False)
    est_bannie = models.BooleanField(default=False)
    jeux_prefere = models.CharField(max_length=50, choices=[('Othello', 'Othello'), ('Trouble', 'Trouble')], blank=True, null=True)
    friends = models.ManyToManyField('self', symmetrical=False, blank=True)
    suspendu_jusqua = models.DateTimeField(null=True, blank=True)

    EMAIL_FIELD = 'courriel'
    def __str__(self):
        return self.username
    
    def suspendre_pour_24h(self):
        self.suspendu_jusqua = now() + timedelta(hours=24)
        self.save()

    def desuspendre(self):
        self.suspendu_jusqua = None
        self.save()
        
    def est_suspendu(self):
        return self.suspendu_jusqua and self.suspendu_jusqua > now()
        
        
class Publication(models.Model):
    titre = models.CharField(max_length=255 , blank=False)
    contenu = models.TextField(blank=False)
    cree_a = models.DateTimeField(auto_now_add=True)
    categorie = models.IntegerField(choices=tableau, default=0)
    id_utilisateur = models.ForeignKey(User, on_delete=models.CASCADE)
    est_signale = models.BooleanField(default=False) 

    def __str__(self):
        return self.titre


class Commentaire(models.Model):
    id_publication = models.ForeignKey(Publication, on_delete=models.CASCADE)
    contenu = models.TextField()
    cree_a = models.DateTimeField(auto_now_add=True)
    est_signale = models.BooleanField(default=False) 
    id_utilisateur = models.ForeignKey(User, on_delete=models.CASCADE)
    est_archive = models.BooleanField(default=False)
    parent = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='reponses'
    )
    

    def __str__(self):
        return self.contenu

    def is_reponse(self):
        return self.parent is not None
    
class Message(models.Model):
    id_utilisateur = models.ForeignKey(User, related_name='sent_messages', on_delete=models.CASCADE)  
    destinataire = models.ForeignKey(User, related_name='received_messages', on_delete=models.CASCADE) 
    objet = models.CharField(max_length=255, blank=False)  
    contenu = models.TextField(blank=False)  
    date_envoye = models.DateTimeField(auto_now_add=True)  
    est_lu = models.BooleanField(default=False)  

    est_supprime_par_envoyeur = models.BooleanField(default=False)  
    est_supprime_par_destinataire = models.BooleanField(default=False)  

    est_archive_par_envoyeur = models.BooleanField(default=False)  
    est_archive_par_destinataire = models.BooleanField(default=False)  

    est_signale = models.BooleanField(default=False)  

    def __str__(self):
        return f'Message de {self.id_utilisateur.username} à {self.destinataire.username} - {self.objet}'
    

class FriendRequest(models.Model):
    from_user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='sent_friend_requests', on_delete=models.CASCADE)
    to_user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='received_friend_requests', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('from_user', 'to_user')

    def __str__(self):
        return f"{self.from_user.username} -> {self.to_user.username}"
    

class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('FRIEND_REQUEST', 'Friend Request'),
        ('FRIEND_ACCEPTED', 'Friend Accepted'),
        ('FRIEND_REJECTED', 'Friend Rejected'),
    )

    to_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='notifications',
        on_delete=models.CASCADE
    )
    from_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='sent_notifications',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    friend_request = models.ForeignKey(FriendRequest, null=True, blank=True, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.notification_type} from {self.from_user} to {self.to_user}"