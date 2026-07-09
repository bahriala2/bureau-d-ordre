from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import render
from django.utils import timezone

from achats.models import DemandeAchat, StatutDemande
from core.models import Service
from courrier.models import Courrier, StatutCourrier, TypeCourrier
from marches.models import Marche, StatutMarche

RETARD_JOURS_COURRIER = 7
RETARD_JOURS_DEMANDE = 15

CLOTURE_STATUTS_COURRIER = {StatutCourrier.CLOTURE, StatutCourrier.ARCHIVE}
CLOTURE_STATUTS_DEMANDE = {StatutDemande.CLOTUREE, StatutDemande.REJETEE}
EN_COURS_STATUTS_MARCHE = {
    StatutMarche.CONSULTATION_LANCEE, StatutMarche.OFFRES_RECUES,
    StatutMarche.ANALYSE_OFFRES, StatutMarche.ATTRIBUE,
    StatutMarche.NOTIFIE, StatutMarche.EN_COURS_EXECUTION,
}


@login_required
def dashboard_home(request):
    today = timezone.localdate()
    seuil_courrier = today - timezone.timedelta(days=RETARD_JOURS_COURRIER)
    seuil_demande = today - timezone.timedelta(days=RETARD_JOURS_DEMANDE)

    courriers_entrants = Courrier.objects.filter(type_courrier=TypeCourrier.ENTRANT).count()
    courriers_sortants = Courrier.objects.filter(type_courrier=TypeCourrier.SORTANT).count()
    courriers_en_attente = Courrier.objects.filter(statut=StatutCourrier.EN_ATTENTE).count()

    demandes_signees_non_transmises = DemandeAchat.objects.filter(statut=StatutDemande.SIGNEE_DIRECTEUR).count()
    demandes_en_cours = DemandeAchat.objects.filter(statut=StatutDemande.EN_COURS_TRAITEMENT).count()
    marches_en_cours = Marche.objects.filter(statut__in=EN_COURS_STATUTS_MARCHE).count()

    courriers_retard = Courrier.objects.exclude(statut__in=CLOTURE_STATUTS_COURRIER).filter(
        created_at__date__lt=seuil_courrier
    )
    demandes_retard = DemandeAchat.objects.exclude(statut__in=CLOTURE_STATUTS_DEMANDE).filter(
        created_at__date__lt=seuil_demande
    )
    dossiers_en_retard = courriers_retard.count() + demandes_retard.count()

    repartition_service = (
        Courrier.objects.values("service__nom").annotate(total=Count("id")).order_by("-total")
    )
    repartition_statut = (
        Courrier.objects.values("statut").annotate(total=Count("id")).order_by("-total")
    )

    context = {
        "courriers_entrants": courriers_entrants,
        "courriers_sortants": courriers_sortants,
        "courriers_en_attente": courriers_en_attente,
        "demandes_signees_non_transmises": demandes_signees_non_transmises,
        "demandes_en_cours": demandes_en_cours,
        "marches_en_cours": marches_en_cours,
        "dossiers_en_retard": dossiers_en_retard,
        "courriers_retard": courriers_retard[:10],
        "demandes_retard": demandes_retard[:10],
        "repartition_service": repartition_service,
        "repartition_statut": repartition_statut,
        "total_services": Service.objects.filter(actif=True).count(),
        "total_marches": Marche.objects.count(),
        "total_demandes": DemandeAchat.objects.count(),
    }
    return render(request, "dashboard/home.html", context)
