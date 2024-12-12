from django.urls import path
from . import views
from django.contrib.auth.decorators import login_required
from .views import CustomLoginView
from .views import CustomPasswordResetView, CustomPasswordResetDoneView, CustomPasswordResetConfirmView, CustomPasswordResetCompleteView
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.index, name='index'),
    path('forum/', views.forum_home, name='forum_home'),
    path('forum/<int:post_id>', views.post_detail, name='forum_detail'),
    path('forum/get_posts', views.get_posts, name='get_posts'),
    path ('forum/chargerplus/<int:last_id>/<str:categorie>', views.chargerplus, name='chargerplus'),


    path('profil/', views.profil, name='profil'),
    path('profil/<int:user_id>', views.profil, name='profil'),
    path('ajouter_post/', views.ajouter_post, name='ajouter_post'),
    path('inscription/', views.inscription, name='inscription'),
    path('activate/<uidb64>/<token>/', views.activate, name='activate'),
    path('accounts/login/', CustomLoginView.as_view(), name='login'),
    path('logout/', views.custom_logout, name='logout'),

    path('othello/', views.othello, name='othello'),
    path('othello/regles/', views.reglesOthello, name='regles_othello'),

    path('messagerie/', views.messagerie, name='messagerie'),
    path('messagerie/envoyer/', views.envoyer_message, name='envoyer_message'),
    path('messagerie/restaurer/<int:message_id>/', views.restaurer_message, name='restaurer_message'),
    path('messagerie/supprimer/<int:message_id>/', views.supprimer_message, name='supprimer_message'),
    path('messagerie/supprimer_definitivement/<int:message_id>/', views.supprimer_definitivement_message, name='supprimer_definitivement_message'),
    path('messagerie/ajouter/', views.messagerie_ajouter, name='messagerie_ajouter'),
    path('messagerie/signaler/<int:message_id>/', views.signaler_message, name='signaler_message'),

    path('profil/modifier/<int:user_id>/', views.modifier_profil, name='modifier_profil'),
    path('recherche/', views.recherche, name='recherche'),

    path('add_friend/<int:user_id>/', views.add_friend, name='add_friend'),
    path('remove_friend/<int:user_id>/', views.remove_friend, name='remove_friend'),
    path('send_friend_request/<int:user_id>/', views.send_friend_request, name='send_friend_request'),

    # Demandes d'amitié
    path('accept_friend_request/<int:request_id>/', views.accept_friend_request, name='accept_friend_request'),
    path('decline_friend_request/<int:request_id>/', views.decline_friend_request, name='decline_friend_request'),
    path('friend_request/cancel/<int:user_id>/', views.cancel_friend_request, name='cancel_friend_request'),

    path('reset_password/', CustomPasswordResetView.as_view(), name='password_reset'),
    path('reset_password_sent/', CustomPasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset_password_complete/', CustomPasswordResetCompleteView.as_view(), name='password_reset_complete'),   

    path('email/change/', views.email_change_request, name='email_change_request'),
    path('email/change/confirm/<uidb64>/<token>/<new_email>/', views.email_change_confirm, name='email_change_confirm'),
    path('email/change/<uidb64>/<token>/<new_email>/', views.email_change_confirm, name='email_change_confirm'),

    path('trouble/', views.trouble, name='trouble'),
    path('panneau-controle/', views.control_panel, name='control_panel'),
    path('panneau-controle/user-action/<int:user_id>/', views.user_action, name='user_action'),
]