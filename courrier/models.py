from django.conf import settings
from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.utils import timezone

from core.models import Service
from documents.models import Document


class TypeCourrier(models.TextChoices):
    ENTRANT = "ENTRANT", "Courrier entrant"
    SORTANT = "SORTANT", "Courrier sortant"


class StatutCourrier(models.TextChoices):
    RECU = "RECU", "Reçu"
    ENREGISTRE = "ENREGISTRE", "Enregistré"
    TRANSMIS = "TRANSMIS", "Transmis"
    EN_TRAITEMENT = "EN_TRAITEMENT", "En traitement"
    EN_ATTENTE = "EN_ATTENTE", "En attente"
    CLOTURE = "CLOTURE", "Clôturé"
    ARCHIVE = "ARCHIVE", "Archivé"


class Urgence(models.TextChoices):
    NORMAL = "NORMAL", "Normal"
    URGENT = "URGENT", "Urgent"


class Courrier(models.Model):
    numero_ordre = models.CharField(max_length=30, unique=True, editable=False)
    type_courrier = models.CharField(max_length=10, choices=TypeCourrier.choices)
    date_courrier = models.DateField(default=timezone.localdate, help_text="Date d'arrivée ou de départ")
    emetteur = models.CharField(max_length=255)
    recepteur = models.CharField(max_length=255)
    objet = models.CharField(max_length=255)
    reference_externe = models.CharField(max_length=100, blank=True)
    service = models.ForeignKey(Service, on_delete=models.PROTECT, related_name="courriers")
    statut = models.CharField(max_length=20, choices=StatutCourrier.choices, default=StatutCourrier.RECU)
    urgence = models.CharField(max_length=10, choices=Urgence.choices, default=Urgence.NORMAL)
    resume = models.TextField(blank=True)

    documents = GenericRelation(Document, related_query_name="courrier")

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="courriers_crees"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Courrier"
        verbose_name_plural = "Courriers"

    def __str__(self):
        return f"{self.numero_ordre} - {self.objet}"

    def save(self, *args, **kwargs):
        if not self.numero_ordre:
            self.numero_ordre = self._generate_numero_ordre()
        super().save(*args, **kwargs)

    def _generate_numero_ordre(self):
        year = timezone.localdate().year
        prefix = "E" if self.type_courrier == TypeCourrier.ENTRANT else "S"
        count = Courrier.objects.filter(
            type_courrier=self.type_courrier, date_courrier__year=year
        ).count()
        return f"BO-{prefix}-{year}-{count + 1:05d}"

    def log_action(self, user, action, commentaire=""):
        return HistoriqueAction.objects.create(courrier=self, user=user, action=action, commentaire=commentaire)


class HistoriqueAction(models.Model):
    courrier = models.ForeignKey(Courrier, on_delete=models.CASCADE, related_name="historique")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=255)
    commentaire = models.TextField(blank=True)
    date_action = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date_action"]
        verbose_name = "Historique d'action"
        verbose_name_plural = "Historique des actions"

    def __str__(self):
        return f"{self.courrier.numero_ordre} - {self.action}"
