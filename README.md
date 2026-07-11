# DTPCSSO — Gestion du bureau d'ordre, des demandes d'achat et des marchés

Application web (Django) pour la digitalisation du bureau d'ordre, le suivi
des courriers, des demandes d'achat signées par le directeur, des
approbations et des marchés publics d'une administration territoriale.

## Modules

- **Bureau d'ordre** (`courrier`) : listes séparées des courriers entrants et
  sortants avec recherche par colonne et lignes cliquables, numéro d'ordre
  automatique, statuts, historique des actions, correspondances liées
  (liaison manuelle + suggestions automatiques par thème, référence ou
  interlocuteur), scan intelligent (OCR + extraction heuristique) avec
  pré-remplissage vérifié par l'agent.
- **Demandes d'achat** (`achats`) : deux circuits de validation — « avec
  accords » (la demande passe par la DCP et les autres directions avant la
  signature du directeur) et « locale » (signature du directeur uniquement) —
  avec approbations, suivi des demandes signées par le directeur
  (`/achats/signees-bureau-ordre/`) et attribution d'un numéro d'ordre au
  bureau d'ordre.
- **Marchés** (`marches`) : suivi des consultations, attributions,
  notifications et clôtures, avec lien optionnel vers la demande d'achat
  d'origine.
- **Gestion documentaire** (`documents`) : pièces jointes génériques
  réutilisables par les courriers, demandes d'achat et marchés.
- **Tableau de bord** (`dashboard`) : indicateurs clés et alertes de retard.
- **Utilisateurs et rôles** (`accounts`) : administrateur, agent bureau
  d'ordre, chef de service, directeur, service achat, service financier,
  audit.

## Démarrage rapide (développement)

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

python3 manage.py migrate
python3 manage.py seed_demo   # crée des services, des comptes de démo et des exemples
python3 manage.py runserver
```

Comptes créés par `seed_demo` (mot de passe `Demo1234!`) : `admin`,
`agent.bo`, `chef.info`, `directeur`, `service.achat`, `service.financier`,
`audit`.

Pour créer votre propre administrateur : `python3 manage.py createsuperuser`.

## Configuration (variables d'environnement)

| Variable | Rôle | Défaut |
|---|---|---|
| `DJANGO_SECRET_KEY` | Clé secrète Django | valeur de développement |
| `DJANGO_DEBUG` | Mode debug | `True` |
| `DJANGO_ALLOWED_HOSTS` | Hôtes autorisés (séparés par des virgules) | `*` |
| `DATABASE_ENGINE` | `postgresql` pour utiliser PostgreSQL (recommandé en production) | SQLite |
| `DATABASE_NAME`, `DATABASE_USER`, `DATABASE_PASSWORD`, `DATABASE_HOST`, `DATABASE_PORT` | Connexion PostgreSQL | — |

## OCR / extraction intelligente des documents

Le module `documents/services/ocr.py` exécute le pipeline
« scan → OCR → extraction → résumé → pré-remplissage ». Le pré-remplissage
n'est jamais enregistré automatiquement : l'agent doit toujours vérifier et
valider la fiche avant l'enregistrement (voir le formulaire de création de
courrier).

L'OCR réel nécessite le binaire Tesseract sur le serveur
(`apt install tesseract-ocr poppler-utils`) ainsi que les dépendances Python
optionnelles `pytesseract` et `pdf2image` (incluses dans `requirements.txt`).
En leur absence, l'application continue de fonctionner normalement : la
saisie reste manuelle et un message prévient l'agent.

## Statuts et workflows

Les statuts des courriers, des demandes d'achat et des marchés reprennent
exactement les valeurs définies dans la spécification fonctionnelle du
projet. Le circuit d'approbation des demandes d'achat est piloté par les
actions disponibles sur la page de détail de chaque demande, filtrées selon
le rôle de l'utilisateur connecté.

## Hébergement / déploiement

**Note : Netlify ne peut pas héberger cette application.** Netlify est réservé
aux sites statiques et fonctions serverless JavaScript ; une application
Django avec base de données nécessite un hébergeur Python. L'équivalent
gratuit le plus proche est **Render**.

### Déploiement sur Render (gratuit, recommandé)

Le dépôt contient un blueprint `render.yaml` (service web + base PostgreSQL) :

1. Créez un compte sur https://render.com (connexion GitHub possible).
2. Cliquez sur **New → Blueprint** et sélectionnez ce dépôt GitHub.
3. Render lit `render.yaml`, crée la base PostgreSQL et le service web,
   exécute `build.sh` (dépendances, collectstatic, migrations, comptes de
   démonstration) puis démarre `gunicorn`.
4. L'application est disponible sur `https://dtpcsso.onrender.com`
   (connexion : `admin` / `Demo1234!` — à changer immédiatement).

Fonctionne aussi sur Railway, Fly.io ou PythonAnywhere : le `Procfile` et
les variables d'environnement documentées ci-dessus suffisent.

## Périmètre non couvert dans cette version

Cette première version pose les fondations fonctionnelles (modèles,
workflows, interface, administration). Restent à approfondir selon les
besoins : intégration d'un moteur IA de résumé plus avancé (LLM), export
PDF/Excel, notifications de relance automatiques, et permissions fines par
document.
