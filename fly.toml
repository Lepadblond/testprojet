# Utiliser une image de base Python
FROM python:3.9-slim

# Définir le répertoire de travail
WORKDIR /app

# Copier les fichiers requirements.txt et installer les dépendances
COPY requirements.txt /app/
RUN pip install -r requirements.txt

# Copier l'intégralité du projet dans le conteneur
COPY . /app/

# Exposer le port 8000
EXPOSE 8000

# Commande pour démarrer l'application Django
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
