from django.db import models


class Service(models.Model):
    """Service / direction administrative (ex: Service Achat, Direction Générale...)."""

    nom = models.CharField(max_length=150, unique=True)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    actif = models.BooleanField(default=True)

    class Meta:
        ordering = ["nom"]
        verbose_name = "Service"
        verbose_name_plural = "Services"

    def __str__(self):
        return self.nom


class TimeStampedModel(models.Model):
    """Abstract base with creation/update timestamps and author tracking."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
