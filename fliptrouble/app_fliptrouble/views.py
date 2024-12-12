import urllib.request
from datetime import date
import json
from django.shortcuts import render, redirect, get_object_or_404, HttpResponse, HttpResponseRedirect
from django.http import Http404, JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse
from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.contrib.auth import login
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, logout
from django.core.mail import send_mail
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.tokens import default_token_generator
from .models import Publication, Commentaire, User, Message
from .forms import postform, CustomUserCreationForm
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.utils.text import slugify
from django.contrib.auth.views import LoginView
from django.contrib import messages
from .forms import CustomUserCreationForm
from django.db.models import Q
from .models import FriendRequest
from channels.layers import get_channel_layer
from django.contrib.auth.views import PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
from django.urls import reverse_lazy
from .forms import ResetPasswordForm  # Import your custom form
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.conf import settings
from .forms import EmailChangeForm
from django.contrib import messages
from django.contrib.auth import get_user_model
from datetime import date
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

import pusher
from django.conf import settings

# Modèles et formulaires
from .models import Publication, Commentaire, User, Message, FriendRequest, Notification
from .forms import postform, commentaireform, CustomUserCreationForm
from django.contrib.auth.views import LoginView
from .forms import CustomAuthenticationForm
from django.views.decorators.http import require_POST


pusher_client = pusher.Pusher(
  app_id=settings.PUSHER_APP_ID,
  key=settings.PUSHER_KEY,
  secret=settings.PUSHER_SECRET,
  cluster=settings.PUSHER_CLUSTER,
  ssl=True
)

################################################
############## SECTION PROFIL ###################
################################################

def index(request):
    """
    Page d'accueil du site
    """
    if not request.user.is_authenticated:
        return redirect('login')

    return render(request, 'fliptrouble/index.html')


def calculer_age(date_naissance):
    today = date.today()
    return today.year - date_naissance.year - ((today.month, today.day) < (date_naissance.month, date_naissance.day))


def profil(request, user_id):
    """
    Page de profil de l'utilisateur
    """
    user_courant = get_object_or_404(User, id=user_id)
    
    age = None
    if user_courant.date_de_naissance:
        age = calculer_age(user_courant.date_de_naissance)
    
    is_friend = user_courant in request.user.friends.all() if request.user.is_authenticated else False

    is_request_sent = False
    is_request_received = False
    friend_request = None

    friends = None  # Initialise la variable friends

    if request.user.is_authenticated:
        if request.user != user_courant:
            # Vérifier si une demande a été envoyée
            is_request_sent = FriendRequest.objects.filter(from_user=request.user, to_user=user_courant).exists()
            
            # Vérifier si une demande a été reçue
            friend_request = FriendRequest.objects.filter(from_user=user_courant, to_user=request.user).first()
            if friend_request:
                is_request_received = True
        else:
            # L'utilisateur consulte son propre profil, récupérer sa liste d'amis
            friends = request.user.friends.all()

    return render(request, 'fliptrouble/profil.html', {
        'user_courant': user_courant,
        'age': age,
        'is_friend': is_friend,
        'is_request_sent': is_request_sent,
        'is_request_received': is_request_received,
        'friend_request': friend_request,
        'friends': friends,  # Passer la liste des amis au template
    })

def trouble(request):
    # Juste une vue pour afficher le template
    return render(request, 'fliptrouble/trouble.html', {})

@login_required
def add_friend(request, user_id):
    user_courant = request.user
    friend_to_add = get_object_or_404(User, id=user_id)
    
    if friend_to_add == user_courant:
        messages.error(request, "Vous ne pouvez pas vous ajouter vous-même comme ami.")
        return redirect('profil', user_id=user_id)

    user_courant.friends.add(friend_to_add)
    messages.success(request, f"{friend_to_add.username} a été ajouté à votre liste d'amis.")
    return redirect('profil', user_id=user_id)

@login_required
def send_friend_request(request, user_id):
    to_user = get_object_or_404(User, id=user_id)
    from_user = request.user

    if to_user == from_user:
        messages.error(request, "Vous ne pouvez pas vous ajouter vous-même comme ami.")
        return redirect('profil', user_id=user_id)

    existing_request = FriendRequest.objects.filter(from_user=from_user, to_user=to_user).first()
    if existing_request:
        messages.info(request, "Vous avez déjà envoyé une demande d'amitié à cet utilisateur.")
        return redirect('profil', user_id=user_id)

    if to_user in from_user.friends.all():
        messages.info(request, "Cet utilisateur est déjà dans votre liste d'amis.")
        return redirect('profil', user_id=user_id)

    # Créer la demande d'ami
    friend_request = FriendRequest.objects.create(from_user=from_user, to_user=to_user)

    # Créer une notification en base
    notification = Notification.objects.create(
        to_user=to_user,
        from_user=from_user,
        notification_type='FRIEND_REQUEST',
        message=f'Vous avez une nouvelle demande d\'amitié de {from_user.username}.',
        friend_request=friend_request
    )

    # Envoyer une notification via WebSocket
    pusher_client.trigger(
    f'notifications_{to_user.username}', 
    'new-notification', 
    {
        'notification': f'Vous avez une nouvelle demande d\'amitié de {from_user.username}.',
        'request_id': friend_request.id
    }
)
    messages.success(request, f"Demande d'amitié envoyée à {to_user.username}.")
    return redirect('profil', user_id=user_id)

@login_required
def accept_friend_request(request, request_id):
    if request.method == "POST":
        friend_request = get_object_or_404(FriendRequest, id=request_id, to_user=request.user)
        from_user = friend_request.from_user
        to_user = friend_request.to_user

        from_user.friends.add(to_user)
        to_user.friends.add(from_user)
        friend_request.delete()

        # Supprimer la notification associée à cette demande
        Notification.objects.filter(friend_request_id=request_id).delete()

        return JsonResponse({'status': 'ok', 'message': f"Vous êtes maintenant amis avec {from_user.username}."})
    else:
        return JsonResponse({'status': 'error', 'message': "Méthode non autorisée."}, status=405)
    
@login_required
def decline_friend_request(request, request_id):
    if request.method == "POST":
        friend_request = get_object_or_404(FriendRequest, id=request_id, to_user=request.user)
        friend_request.delete()

        # Supprimer la notification associée à cette demande
        Notification.objects.filter(friend_request_id=request_id).delete()

        return JsonResponse({'status': 'ok', 'message': "La demande d'amitié a été refusée."})
    else:
        return JsonResponse({'status': 'error', 'message': "Méthode non autorisée."}, status=405)
    
@login_required
def remove_friend(request, user_id):
    """
    Supprime un utilisateur de la liste d'amis.
    """
    friend = get_object_or_404(User, id=user_id)
    request.user.friends.remove(friend)
    friend.friends.remove(request.user)
    messages.success(request, f"{friend.username} a été supprimé de votre liste d'amis.")
    return redirect('profil', user_id=user_id)

@login_required
def cancel_friend_request(request, user_id):
    """
    Annule une demande d'amitié envoyée.
    """
    friend_request = FriendRequest.objects.filter(from_user=request.user, to_user_id=user_id).first()
    if friend_request:
        friend_request.delete()
        messages.success(request, "La demande d'amitié a été annulée.")
    else:
        messages.error(request, "Aucune demande d'amitié trouvée.")
    return redirect('profil', user_id=user_id)

class CustomPasswordResetView(PasswordResetView):
    template_name = 'registration/password_reset_form.html'
    success_url = reverse_lazy('password_reset_done')
    email_template_name = 'registration/password_reset_email.html'
    subject_template_name = 'registration/password_reset_subject.txt'

class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'registration/password_reset_done.html'

class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'registration/password_reset_confirm.html'
    success_url = reverse_lazy('password_reset_complete')

class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'registration/password_reset_complete.html'


def email_change_request(request):
    if request.method == 'POST':
        # Supposons que form est déjà vérifié et valide
        new_email = form.cleaned_data['new_email']
        user = request.user

        # Générer le token de confirmation et le lien
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(str(user.pk).encode())

        # Créer l'URL complète
        confirm_link = request.build_absolute_uri(
            reverse('email_change_confirm', args=[uid, token])
        )

        # Envoyer l'email avec le lien
        send_mail(
            'Confirmation de changement d\'email',
            f"Bonjour {user.username},\n\nVous avez demandé à changer votre adresse e-mail.\nVeuillez cliquer sur le lien ci-dessous pour confirmer ce changement :\n\n{confirm_link}\n\nSi vous n'êtes pas à l'origine de cette demande, veuillez nous contacter immédiatement.\n\nCordialement,\nL'équipe de FlipTrouble",
            settings.DEFAULT_FROM_EMAIL,
            [new_email],
            fail_silently=False,
        )

        # Rediriger ou renvoyer un message
        return redirect('some_redirect')
    
@login_required
def email_change_request(request):
    if request.method == 'POST':
        form = EmailChangeForm(request.POST, user=request.user)
        if form.is_valid():
            new_email = form.cleaned_data['new_email']

            # Générer un jeton de confirmation
            token = default_token_generator.make_token(request.user)
            uid = urlsafe_base64_encode(force_bytes(request.user.pk))
            new_email_encoded = urlsafe_base64_encode(force_bytes(new_email))

            # Construire l'URL de confirmation
            current_site = get_current_site(request)
            confirm_url = reverse('email_change_confirm', kwargs={
                'uidb64': uid,
                'token': token,
                'new_email': new_email_encoded,
            })

            # Debug : Imprimer le lien de confirmation pour s'assurer qu'il est généré
            print("Lien de confirmation : ", confirm_url)  # Vérifiez si cela affiche un lien valide
            confirm_link = f'http://{current_site.domain}{confirm_url}'

            # Envoyer l'e-mail de confirmation
            subject = 'Confirmez le changement de votre adresse e-mail'
            message = render_to_string('email_change_request_email.html', {
                'user': request.user,
                'confirm_link': confirm_link,
            })
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [request.user.courriel])

            messages.success(request, 'Un e-mail de confirmation a été envoyé à votre adresse e-mail actuelle.')
            return redirect('profil', user_id=request.user.id)
        else:
            return render(request, 'email_change_form.html', {'form': form})
    else:
        form = EmailChangeForm(user=request.user)
        return render(request, 'email_change_form.html', {'form': form})
    

from django.utils.encoding import force_str
@login_required
def email_change_confirm(request, uidb64, token, new_email):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = get_user_model().objects.get(pk=uid)

        if default_token_generator.check_token(user, token):
            new_email_decoded = force_str(urlsafe_base64_decode(new_email))
            old_email = user.courriel  # Assurez-vous d'utiliser le bon champ
            user.courriel = new_email_decoded
            user.save()

            messages.success(request, "Votre adresse e-mail a été mise à jour avec succès.")

            # Envoyer une notification à la nouvelle adresse e-mail
            subject = 'Votre adresse e-mail a été modifiée'
            message = render_to_string('email_change_notification.html', {
                'user': user,
                'old_email': old_email,
                'new_email': new_email_decoded,
            })
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [new_email_decoded])

            return redirect('profil', user_id=user.id)
        else:
            messages.error(request, "Le lien de confirmation est invalide ou a expiré.")
            return redirect('profil', user_id=request.user.id)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        messages.error(request, "Le lien de confirmation est invalide.")
        return redirect('profil', user_id=request.user.id)
        
################################################
############## SECTION FORUM ###################
################################################


CATEGORY_MAP = {
    'jeux': 0,
    'general': 1,
    'humour': 2,
    # Ajoutez d'autres catégories si nécessaire
}
def forum_home(request):
    """page d'accueil du forum"""
    general_posts = Publication.objects.filter(categorie=1).order_by('-cree_a')[:5]
    humour_posts = Publication.objects.filter(categorie=2).order_by('-cree_a')[:5]
    jeux_posts =  Publication.objects.filter(categorie=0).order_by('-cree_a')[:5]
   
    form = postform()

    context = {
        'general_posts': general_posts,
        'humour_posts': humour_posts,
        'jeux_posts': jeux_posts,
        'form': form,
     
    }

    return render(request, 'forum/forum_home.html', context)


def chargerplus(request, last_id, categorie):
    # Convertir last_id en entier
    print("Received last_id:", last_id)
    print("Received category:", categorie)
    category_id = CATEGORY_MAP.get(categorie)
    print (category_id)

    
    

    # Récupérer les posts de la catégorie spécifiée avec l'offset et last_id
    posts = Publication.objects.filter(categorie=category_id, id__lt=last_id).order_by('-cree_a')[:10]
    posts_data = []

    for post in posts:
        post_data = {
            'id': post.id,
            'titre': post.titre,
            'contenu': post.contenu,
            'cree_a': post.cree_a,
            'id_utilisateur': post.id_utilisateur.username,  # Inclure le nom d'utilisateur
            'categorie': post.categorie
        }
        posts_data.append(post_data)

    return JsonResponse({'posts': posts_data})

  
    

    return JsonResponse({'posts': posts_data})




def get_posts(request):
    # Récupérer l'ID du dernier post depuis les paramètres de l'URL (lastPostId)
    last_post_id = request.GET.get('lastPostId')

    if last_post_id:
        try:
            # Convertir last_post_id en entier pour filtrer correctement
            last_post_id = int(last_post_id)
        except ValueError:
            return JsonResponse({'error': 'Invalid lastPostId'}, status=400)

    # Récupérer les posts de la catégorie spécifiée avec l'offset et last_id
    posts = Publication.objects.filter(id__lt=last_post_id).order_by('-cree_a')[:10]
    posts_data = []

    for post in posts:
        post_data = {
            'id': post.id,
            'titre': post.titre,
            'contenu': post.contenu,
            'cree_a': post.cree_a,
            'id_utilisateur': post.id_utilisateur.username,  # Inclure le nom d'utilisateur
            'categorie': post.categorie
        }
        posts_data.append(post_data)

    return JsonResponse({'posts': posts_data})



def post_detail(request, post_id):
    """
    Afficher le détail d'un post
    """
    # Vérifier si l'utilisateur est connecté
    if not request.user.is_authenticated:
        return redirect('login')

    # Vérifier si le post_id existe et est valide
    post = get_object_or_404(Publication, id=post_id)

    # Récupérer les commentaires principaux (ceux sans parent)
    commentaires = Commentaire.objects.filter(
        id_publication=post, parent=None
    ).order_by('-cree_a').prefetch_related('reponses')  # Précharger les réponses

    # Gérer le formulaire
    if request.method == 'POST':
        form = commentaireform(request.POST)
        if form.is_valid():
            parent_id = request.POST.get('parent_id')  # ID du commentaire parent
            parent_comment = None
            if parent_id:
                parent_comment = get_object_or_404(Commentaire, id=parent_id)

            commentaire = form.save(commit=False)
            commentaire.id_publication = post  # Associer le commentaire au post
            commentaire.id_utilisateur = request.user
            commentaire.parent = parent_comment  # Associer un parent si présent
            commentaire.save()
            return redirect('forum_detail', post_id=post.id)  # Rediriger vers le même post

    else:
        form = commentaireform()

    # Afficher le post, les commentaires et le formulaire
    return render(request, 'forum/forum_detail.html', {
        'post': post,
        'commentaires': commentaires,
        'form': form,
    })





def ajouter_post(request):
    """
    Ajouter un post
    """
    if not request.user.is_authenticated:
        return redirect('login')
    
    if request.method == 'POST':
        form = postform(request.POST)
        user = request.user
        if form.is_valid():
            titre = form.cleaned_data['titre']
            contenu = form.cleaned_data['contenu']
            categorie = form.cleaned_data['categorie']
            post = Publication(titre=titre, contenu=contenu, categorie=categorie, id_utilisateur=user)
            print (post)
            post.save()
            return redirect('forum_home')
    else:
        form = postform()

    return render(request, 'forum/ajouter_post.html', {'form': form}) 




















################################################
############## SECTION RECHERCHE ###################
################################################


def calculate_age(born):
    if born is None:
        return ''
    today = date.today()
    return today.year - born.year - ((today.month, today.day) < (born.month, born.day))

@login_required
def modifier_profil(request, user_id):
    user_courant = get_object_or_404(User, id=user_id)
    if request.user != user_courant:
        return redirect('profil', user_id=user_courant.id)

    if request.method == 'POST':
        print("Requête POST reçue")
        print("Données POST :", request.POST)
        sexe = request.POST.get('sexe')
        jeux_prefere = request.POST.get('jeux_prefere')

        if sexe:
            user_courant.sexe = sexe
        if jeux_prefere:
            user_courant.jeux_prefere = jeux_prefere

        user_courant.save()
        print("Profil mis à jour avec succès")
        return redirect('profil', user_id=user_courant.id)
    else:
        age = calculate_age(user_courant.date_de_naissance)
        return render(request, 'fliptrouble/profil.html', {
            'user_courant': user_courant,
            'age': age,
            # Autres variables de contexte
        })
    
def recherche(request):
    profiles = User.objects.all()

    search_query = request.GET.get('query', '')
    gender_filter = request.GET.get('sexe', '')
    favorite_game_filter = request.GET.get('jeux_prefere', '')

    if search_query:
        profiles = profiles.filter(username__icontains=search_query)
    
    if gender_filter:
        profiles = profiles.filter(sexe=gender_filter)
    
    if favorite_game_filter:
        profiles = profiles.filter(jeux_prefere=favorite_game_filter)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        profiles_data = []
        for profile in profiles:
            age = None
            if profile.date_de_naissance:
                age = calculer_age(profile.date_de_naissance)
            profiles_data.append({
                "id": profile.id,
                "username": profile.username,
                "sexe": profile.sexe or "Non spécifié",
                "jeux_prefere": profile.jeux_prefere or "Non spécifié",
                "age": age or "Non spécifié"
            })
        return JsonResponse({'profiles': profiles_data})

    context = {
        'profiles': profiles,
        'search_query': search_query,
        'gender_filter': gender_filter,
        'favorite_game_filter': favorite_game_filter,
    }
    return render(request, 'fliptrouble/recherche.html', context)

    context = {
        'profiles': profiles,
        'search_query': search_query,
        'gender_filter': gender_filter,
        'favorite_game_filter': favorite_game_filter,
    }
    return render(request, 'fliptrouble/recherche.html', context)
  
################################################
################################################
# views.py


# views.py

def inscription(request):
    if request.user.is_authenticated:
        return redirect('index')
    
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = True  # Automatically activate the user
            user.save()
            # Remove or comment out the email verification logic
            # send_confirmation_email(request, user)

            messages.success(request, "Votre compte a été créé avec succès. Vous pouvez maintenant vous connecter.")
            return redirect('login')
        else:
            messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
    else:
        form = CustomUserCreationForm()

    return render(request, 'fliptrouble/inscription.html', {'form': form})


def send_confirmation_email(request, user):
    """
    Envoie un e-mail de confirmation avec un jeton.
    """
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    current_site = get_current_site(request)
    mail_subject = 'Activez votre compte FlipTrouble'
    message = render_to_string('email_verification.html', {
        'user': user,
        'domain': current_site.domain,
        'uidb64': uid,
        'token': token,
    })
    send_mail(mail_subject, message, 'projet.garneau@gmail.com', [user.email])



def activate(request, uidb64, token):
    """
    Active le compte de l'utilisateur après vérification du lien de confirmation.
    """
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        login(request, user)
        return HttpResponse('Votre compte a été activé avec succès !')
    else:
        return render(request, 'registration/login.html')
    
def custom_404(request, exception):
    return render(request, '404.html', {}, status=404)
 
class CustomLoginView(LoginView):
    template_name = 'registration/login.html'
 
    def form_valid(self, form):
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password')
 
        # Essaye de trouver l'utilisateur avec le nom d'utilisateur ou l'e-mail
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            user = User.objects.filter(email=username).first()
 
        if user is not None:
            if not user.is_active:
                messages.error(self.request, "Votre compte n'a pas encore été activé. Veuillez vérifier votre courriel.")
                return self.form_invalid(form)
            else:
                # Si l'utilisateur est actif, continuez avec l'authentification
                user = authenticate(self.request, username=username, password=password)
                if user is None:
                    messages.error(self.request, "Courriel ou mot de passe incorrect.")
                    return self.form_invalid(form)
                else:
                    login(self.request, user)
                    return redirect('forum_home')
        else:
            messages.error(self.request, "Courriel ou mot de passe incorrect.")
            return self.form_invalid(form)
        
def custom_logout(request):
    logout(request)
    return redirect('index')

###############################################
############## SECTION JEUX ###################
###############################################

def othello(request):
    if not request.user.is_authenticated:
        return redirect('login')
    
    return render(request, 'fliptrouble/othello.html', {'username': request.user.username})


def reglesOthello(request):
    if not request.user.is_authenticated:
        return redirect('login')

    return render(request, 'fliptrouble/othelloregle.html')


class CustomLoginView(LoginView):
    template_name = 'registration/login.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('index')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password')

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            user = User.objects.filter(email=username).first()

        if user is not None:
            if not user.is_active:
                messages.error(self.request, "Votre compte n'a pas encore été activé. Veuillez vérifier votre courriel.")
                return self.form_invalid(form)
            else:
                user = authenticate(self.request, username=username, password=password)
                if user is None:
                    messages.error(self.request, "Courriel ou mot de passe incorrect.")
                    return self.form_invalid(form)
                else:
                    login(self.request, user)
                    return redirect('/')
        else:
            messages.error(self.request, "Courriel ou mot de passe incorrect.")
            return self.form_invalid(form)



################################################
############## SECTION MESSAGERIE ##############
################################################

def messagerie(request):
    onglet = request.GET.get('onglet', 'recus')
    user = request.user

    if onglet == 'recus':
        messages = Message.objects.filter(
            destinataire=user,
            est_supprime_par_destinataire=False,
            est_archive_par_destinataire=False
        )
    elif onglet == 'envoyes':
        messages = Message.objects.filter(
            id_utilisateur=user,
            est_supprime_par_envoyeur=False,
            est_archive_par_envoyeur=False
        )
    elif onglet == 'corbeille':
        messages = Message.objects.filter(
            Q(destinataire=user, est_supprime_par_destinataire=True) |
            Q(id_utilisateur=user, est_supprime_par_envoyeur=True)
        )
    else:
        messages = Message.objects.none()

    return render(request, 'fliptrouble/messagerie.html', {
        'onglet': onglet,
        'messages': messages,
    })

def messagerie_ajouter(request, receiver_id=None):
    if not request.user.is_authenticated:
        return redirect('login')

    destinataire = get_object_or_404(User, id=receiver_id) if receiver_id else None
    utilisateurs = User.objects.exclude(id=request.user.id)

    context = {
        'utilisateurs': utilisateurs,
        'destinataire': destinataire,
    }

    return render(request, 'fliptrouble/messagerie_ajouter.html', context)

from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from .models import User, Message

def envoyer_message(request):
    if not request.user.is_authenticated:
        return redirect('login')

    if request.method == 'POST':
        destinataire_id = request.POST.get('receiver')
        objet = request.POST.get('subject')
        contenu = request.POST.get('body')

        if not destinataire_id or not objet or not contenu:
            messages.error(request, "Tous les champs sont obligatoires.")
            return redirect('messagerie_ajouter')

        destinataire = get_object_or_404(User, id=destinataire_id)

        if destinataire not in request.user.friends.all():
            messages.error(request, "Vous ne pouvez envoyer un message qu'à vos amis.")
            return redirect('messagerie_ajouter')

        if destinataire == request.user:
            messages.error(request, "Vous ne pouvez pas vous envoyer un message.")
            return redirect('messagerie_ajouter')

        Message.objects.create(
            id_utilisateur=request.user,
            destinataire=destinataire,
            objet=objet,
            contenu=contenu,
            date_envoye=timezone.now()
        )

        messages.success(request, "Message envoyé avec succès.")
        return redirect('messagerie')

    return redirect('messagerie_ajouter')


def signaler_message(request, message_id):
    message = get_object_or_404(Message, id=message_id)
    message.est_signale = True
    message.save()
    messages.success(request, "Message signalé avec succès.")
    return redirect('messagerie')


def restaurer_message(request, message_id):
    message = get_object_or_404(Message, id=message_id)

    if request.user == message.id_utilisateur:
        message.est_supprime_par_envoyeur = False
    elif request.user == message.destinataire:
        message.est_supprime_par_destinataire = False
    else:
        messages.error(request, "Action non autorisée.")
        return redirect('messagerie')

    message.save()
    messages.success(request, "Message restauré avec succès.")
    return redirect('messagerie')

def supprimer_message(request, message_id):
    message = get_object_or_404(Message, id=message_id)
    role = request.GET.get('role')

    if role == 'envoyeur' and request.user == message.id_utilisateur:
        message.est_supprime_par_envoyeur = True
    elif role == 'destinataire' and request.user == message.destinataire:
        message.est_supprime_par_destinataire = True
    else:
        messages.error(request, "Action non autorisée.")
        return redirect('messagerie')

    message.save()
    messages.success(request, "Message déplacé dans la corbeille.")
    return redirect('messagerie')

def supprimer_definitivement_message(request, message_id):
    message = get_object_or_404(Message, id=message_id)

    if (request.user == message.id_utilisateur and message.est_supprime_par_envoyeur) or \
       (request.user == message.destinataire and message.est_supprime_par_destinataire):
        message.delete()
        messages.success(request, "Message supprimé définitivement.")
    else:
        messages.error(request, "Action non autorisée.")

    return redirect('messagerie')


################################################
############## SECTION ADMIN ###################
################################################

def is_admin_or_moderator(user):
    return user.is_superuser or user.est_moderateur

@login_required
def control_panel(request):
    name = request.GET.get('name', '').strip()
    status = request.GET.get('status', '').strip()
    role = request.GET.get('role', '').strip()

    users = User.objects.all()

    if name:
        users = users.filter(username__icontains=name)

    if status:
        if status == 'actif':
            users = users.filter(est_bannie=False, suspendu_jusqua__isnull=True)
        elif status == 'suspendu':
            users = users.filter(suspendu_jusqua__isnull=False)
        elif status == 'banni':
            users = users.filter(est_bannie=True)

    if role:
        if role == 'administrateur':
            users = users.filter(is_superuser=True)
        elif role == 'moderateur':
            users = users.filter(est_moderateur=True)
        elif role == 'utilisateur':
            users = users.filter(is_superuser=False, est_moderateur=False)

    reported_publications = Publication.objects.filter(est_signale=True)
    reported_comments = Commentaire.objects.filter(est_signale=True)
    reported_messages = Message.objects.filter(est_signale=True)

    context = {
        'users': users,
        'reported_publications': reported_publications,
        'reported_comments': reported_comments,
        'reported_messages': reported_messages,
    }
    return render(request, 'fliptrouble/panneau_controle.html', context)


@login_required
@user_passes_test(is_admin_or_moderator)
def user_action(request, user_id):
    user = get_object_or_404(User, id=user_id)
    action = request.POST.get('action')
    
    if action == "suspend" and (request.user.is_superuser or request.user.est_moderateur):
        user.suspendre_pour_24h()
    elif action == "unsuspend" and (request.user.is_superuser or request.user.est_moderateur):
        user.desuspendre()
    elif action == "ban" and request.user.is_superuser:
        user.est_bannie = True
    elif action == "unban" and request.user.is_superuser:
        user.est_bannie = False
    elif action == "promote" and request.user.is_superuser:
        user.est_moderateur = True
    elif action == "demote" and request.user.is_superuser:
        user.est_moderateur = False
    else:
        messages.error(request, "Action non autorisée.")
        return redirect(f"{request.META.get('HTTP_REFERER', 'control_panel')}")

    user.save()
    messages.success(request, f"L'action '{action}' a été appliquée avec succès.")

    # Preserve filters by redirecting back with query parameters
    query_params = request.GET.urlencode()
    redirect_url = f"{reverse('control_panel')}?{query_params}" if query_params else reverse('control_panel')
    return redirect(redirect_url)

@login_required
@require_POST
@user_passes_test(is_admin_or_moderator)
def content_action(request, content_type, content_id):
    action = request.POST.get('action')
    
    if content_type == 'publication':
        content = get_object_or_404(Publication, id=content_id)
    elif content_type == 'comment':
        content = get_object_or_404(Commentaire, id=content_id)
    elif content_type == 'message':
        content = get_object_or_404(Message, id=content_id)
    else:
        return redirect(f"{request.META.get('HTTP_REFERER', 'control_panel')}")

    if action == 'delete':
        content.delete()
        messages.success(request, f'{content_type.capitalize()} supprimé avec succès.')
    elif action == 'ban':
        user = content.id_utilisateur
        user.est_bannie = True
        user.save()
        messages.success(request, f"Utilisateur {user.username} banni avec succès.")

    query_params = request.GET.urlencode()
    redirect_url = f"{reverse('control_panel')}?{query_params}" if query_params else reverse('control_panel')
    return redirect(redirect_url)

