from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Publication, Commentaire, User
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth.forms import PasswordResetForm



class postform(forms.ModelForm):
    error_css_class = 'alert alert-danger'

    class Meta:
        model = Publication
        fields = ['titre', 'contenu', 'categorie']
        labels = {
            'titre': 'Titre',
            'contenu': 'Contenu',
            'categorie': 'Categorie',
        }
        widgets = {
            'titre': forms.TextInput(attrs={'class': 'form-control'}),
            'contenu': forms.Textarea(attrs={'class': 'form-control'}),
            'categorie': forms.Select(attrs={'class': 'form-control'}),
        }
         
class commentaireform(forms.ModelForm):
    error_css_class = 'alert alert-danger'

    class Meta:
        model = Commentaire
        fields = ['contenu']
        widgets = {
            'body': forms.Textarea(attrs={
                'class': 'form-control ', 
                'placeholder': 'Entrez votre commentaire ici...'
            }),
        }
        labels = {
            'contenu': '',
        }
   


class CustomUserCreationForm(UserCreationForm):
    courriel = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'id': 'courriel', 'name': 'email'}),
        label="Adresse e-mail"
    )
    adresse = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'name': 'adresse'}),
        label="Adresse"
    )
    sexe = forms.ChoiceField(
        choices=[('', 'Sélectionnez un genre'), ('homme', 'Homme'), ('femme', 'Femme'), ('autre', 'Autre')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'genre', 'name': 'sexe'}),
        label="Genre"
    )
    date_de_naissance = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={'class': 'form-control', 'id': 'date_de_naissance', 'type': 'date', 'name': 'date_de_naissance'}),
        label="Date de naissance"
    )
    telephone = forms.CharField(
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'name': 'telephone'}),
        label="Téléphone"
    )
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'username', 'name': 'username'}),
        label="Nom d'utilisateur"
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'id': 'password', 'name': 'password1'}),
        label="Mot de passe"
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'id': 'confirm_mdp', 'name': 'password2'}),
        label="Confirmer le mot de passe"
    )

    def clean_courriel(self):
        email = self.cleaned_data.get('courriel')
        if User.objects.filter(courriel=email).exists():
            raise ValidationError("Ce courriel est déjà utilisé.")
        return email

    def clean_date_de_naissance(self):
        date_naiss = self.cleaned_data.get('date_de_naissance')
        if date_naiss:
            today = timezone.now().date()
            age = today.year - date_naiss.year - ((today.month, today.day) < (date_naiss.month, date_naiss.day))
            if age < 18:
                raise ValidationError("Vous devez avoir au moins 18 ans pour vous inscrire.")
        else:
            # Si la date de naissance est requise, vous pouvez émettre une erreur si elle est manquante
            # raise ValidationError("La date de naissance est requise.")
            pass
        return date_naiss

    class Meta:
        model = User
        fields = ('username', 'sexe', 'date_de_naissance', 'courriel', 'password1', 'password2')

    def clean_courriel(self):
        courriel = self.cleaned_data.get('courriel')
        if not courriel:
            raise ValidationError("L'adresse e-mail est requise.")
        if User.objects.filter(courriel=courriel).exists():
            raise ValidationError("Ce courriel est déjà utilisé.")
        return courriel

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')

        if not password1:
            raise ValidationError("Le mot de passe est requis.")
        if not password2:
            raise ValidationError("Veuillez confirmer le mot de passe.")
        if password1 != password2:
            raise ValidationError("Les mots de passe ne correspondent pas.")
        return password2

    class Meta:
        model = User
        fields = ('username', 'sexe', 'date_de_naissance', 'courriel', 'password1', 'password2')


class CustomAuthenticationForm(AuthenticationForm):
    def confirm_login_allowed(self, user):
        if not user.is_active:
            raise forms.ValidationError(
                "Votre compte n'a pas encore été activé. Veuillez vérifier votre courriel.",
                code='inactive',
            )
        

def clean_date_of_birth(self):
        date_of_birth = self.cleaned_data.get('date_de_naissance')
        if date_of_birth:
            today = timezone.now().date()
            age = (today - date_of_birth).days // 365
            if age < 18:
                raise ValidationError("Vous devez avoir au moins 18 ans pour vous inscrire.")
        return date_of_birth        


class ResetPasswordForm(PasswordResetForm):
    def get_users(self, email):
        """Override to allow inactive users to receive the password reset email."""
        email_field_name = get_user_model().get_email_field_name()
        active_users = get_user_model()._default_manager.filter(**{
            '%s__iexact' % email_field_name: email,
        })
        return (u for u in active_users if u.has_usable_password())
    
class EmailChangeForm(forms.Form):
    new_email = forms.EmailField(label="Nouvelle adresse e-mail", required=True)

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(EmailChangeForm, self).__init__(*args, **kwargs)

    def clean_new_email(self):
        new_email = self.cleaned_data['new_email']
        if User.objects.filter(courriel=new_email).exists():
            raise forms.ValidationError("Cette adresse e-mail est déjà utilisée.")
        return new_email