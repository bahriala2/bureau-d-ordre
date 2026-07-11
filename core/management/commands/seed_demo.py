from django.core.management.base import BaseCommand

from accounts.models import Role, User
from achats.models import DemandeAchat, StatutDemande, TypeAchat
from core.models import Correspondant, Service
from courrier.models import Courrier, StatutCourrier, TypeCourrier
from marches.models import Marche, StatutMarche, TypeProcedure


class Command(BaseCommand):
    help = "Crée des services, utilisateurs et données de démonstration pour chaque rôle et module."

    def handle(self, *args, **options):
        services = {}
        for nom, code in [
            ("Direction Générale", "DG"),
            ("Service Achat", "ACHAT"),
            ("Service Financier", "FIN"),
            ("Service Informatique", "INFO"),
        ]:
            service, _ = Service.objects.get_or_create(code=code, defaults={"nom": nom})
            services[code] = service

        users = [
            ("admin", Role.ADMINISTRATEUR, "DG", True),
            ("agent.bo", Role.AGENT_BUREAU_ORDRE, "DG", False),
            ("chef.info", Role.CHEF_SERVICE, "INFO", False),
            ("directeur", Role.DIRECTEUR, "DG", False),
            ("service.achat", Role.SERVICE_ACHAT, "ACHAT", False),
            ("service.financier", Role.SERVICE_FINANCIER, "FIN", False),
            ("audit", Role.AUDIT, "DG", False),
        ]
        created_users = {}
        for username, role, service_code, is_superuser in users:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "role": role,
                    "service": services[service_code],
                    "is_staff": True,
                    "is_superuser": is_superuser,
                },
            )
            if created:
                user.set_password("Demo1234!")
                user.save()
                self.stdout.write(f"Utilisateur créé : {username} / Demo1234! (rôle : {role})")
            created_users[username] = user

        for nom in [
            "Direction Générale",
            "Gouvernorat",
            "Municipalité",
            "Ministère de l'Équipement",
            "Société ABC",
        ]:
            Correspondant.objects.get_or_create(nom=nom)

        agent_bo = created_users["agent.bo"]

        courrier, created = Courrier.objects.get_or_create(
            objet="Demande de renseignements - marché de fournitures",
            defaults=dict(
                type_courrier=TypeCourrier.ENTRANT,
                emetteur="Société ABC",
                recepteur="Direction Générale",
                service=services["DG"],
                statut=StatutCourrier.ENREGISTRE,
                created_by=agent_bo,
            ),
        )
        if created:
            courrier.log_action(agent_bo, "Enregistrement", "Créé via seed de démonstration")

        demande, created = DemandeAchat.objects.get_or_create(
            objet="Acquisition de matériel informatique",
            defaults=dict(
                service_demandeur=services["INFO"],
                description="Renouvellement de 10 postes de travail",
                montant_estimatif=15000,
                type_achat=TypeAchat.MATERIEL_INFORMATIQUE,
                statut=StatutDemande.SIGNEE_DIRECTEUR,
                created_by=created_users["chef.info"],
            ),
        )

        Marche.objects.get_or_create(
            objet="Marché de fourniture de matériel informatique",
            defaults=dict(
                type_procedure=TypeProcedure.CONSULTATION,
                service_demandeur=services["INFO"],
                demande_achat=demande,
                statut=StatutMarche.PREPARATION,
                created_by=created_users["service.achat"],
            ),
        )

        self.stdout.write(self.style.SUCCESS("Données de démonstration créées avec succès."))
