from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.models import Role

from .forms import ApprobationForm, DemandeAchatForm
from .models import Approbation, DemandeAchat, StatutDemande

# action -> (target status, roles allowed, message)
ACTIONS = {
    "soumettre": (StatutDemande.SOUMISE, {Role.AGENT_BUREAU_ORDRE, Role.CHEF_SERVICE, Role.ADMINISTRATEUR}, "Demande soumise."),
    "valider_chef_service": (StatutDemande.VALIDEE_CHEF_SERVICE, {Role.CHEF_SERVICE, Role.ADMINISTRATEUR}, "Demande validée par le chef de service."),
    "soumettre_directeur": (StatutDemande.SOUMISE_DIRECTEUR, {Role.CHEF_SERVICE, Role.ADMINISTRATEUR}, "Demande soumise au directeur."),
    "signer_directeur": (StatutDemande.SIGNEE_DIRECTEUR, {Role.DIRECTEUR, Role.ADMINISTRATEUR}, "Demande signée par le directeur."),
    "recevoir_bureau_ordre": (StatutDemande.RECUE_BUREAU_ORDRE, {Role.AGENT_BUREAU_ORDRE, Role.ADMINISTRATEUR}, "Demande reçue par le bureau d'ordre."),
    "transmettre_service_achat": (StatutDemande.TRANSMISE_SERVICE_ACHAT, {Role.AGENT_BUREAU_ORDRE, Role.ADMINISTRATEUR}, "Demande transmise au service achat."),
    "traiter": (StatutDemande.EN_COURS_TRAITEMENT, {Role.SERVICE_ACHAT, Role.ADMINISTRATEUR}, "Demande en cours de traitement."),
    "preparer_bon_commande": (StatutDemande.BON_COMMANDE_PREPARE, {Role.SERVICE_ACHAT, Role.ADMINISTRATEUR}, "Bon de commande préparé."),
    "lancer_marche": (StatutDemande.MARCHE_LANCE, {Role.SERVICE_ACHAT, Role.ADMINISTRATEUR}, "Marché lancé."),
    "cloturer": (StatutDemande.CLOTUREE, {Role.SERVICE_ACHAT, Role.AGENT_BUREAU_ORDRE, Role.ADMINISTRATEUR}, "Demande clôturée."),
    "rejeter": (StatutDemande.REJETEE, {Role.CHEF_SERVICE, Role.DIRECTEUR, Role.ADMINISTRATEUR}, "Demande rejetée."),
}

# statut courant -> liste des actions possibles pour l'écran de détail
NEXT_ACTIONS = {
    StatutDemande.BROUILLON: ["soumettre"],
    StatutDemande.SOUMISE: ["valider_chef_service", "rejeter"],
    StatutDemande.VALIDEE_CHEF_SERVICE: ["soumettre_directeur", "rejeter"],
    StatutDemande.SOUMISE_DIRECTEUR: ["signer_directeur", "rejeter"],
    StatutDemande.SIGNEE_DIRECTEUR: ["recevoir_bureau_ordre"],
    StatutDemande.RECUE_BUREAU_ORDRE: ["enregistrer_bureau_ordre"],
    StatutDemande.ENREGISTREE: ["transmettre_service_achat"],
    StatutDemande.TRANSMISE_SERVICE_ACHAT: ["traiter"],
    StatutDemande.EN_COURS_TRAITEMENT: ["preparer_bon_commande", "lancer_marche"],
    StatutDemande.BON_COMMANDE_PREPARE: ["cloturer"],
    StatutDemande.MARCHE_LANCE: ["cloturer"],
}

ACTION_LABELS = {
    "soumettre": "Soumettre",
    "valider_chef_service": "Valider (chef de service)",
    "soumettre_directeur": "Soumettre au directeur",
    "signer_directeur": "Signer (directeur)",
    "recevoir_bureau_ordre": "Marquer reçue au bureau d'ordre",
    "enregistrer_bureau_ordre": "Enregistrer au bureau d'ordre",
    "transmettre_service_achat": "Transmettre au service achat",
    "traiter": "Marquer en cours de traitement",
    "preparer_bon_commande": "Bon de commande préparé",
    "lancer_marche": "Marché lancé",
    "cloturer": "Clôturer",
    "rejeter": "Rejeter",
}


@login_required
def demande_list(request):
    demandes = DemandeAchat.objects.select_related("service_demandeur").all()
    statut = request.GET.get("statut")
    if statut:
        demandes = demandes.filter(statut=statut)
    return render(request, "achats/demande_list.html", {"demandes": demandes, "statuts": StatutDemande.choices, "statut_actif": statut})


@login_required
def demandes_signees_bo(request):
    """Espace bureau d'ordre : demandes signées par le directeur, en attente d'enregistrement/transmission."""
    demandes = DemandeAchat.objects.filter(statut=StatutDemande.SIGNEE_DIRECTEUR).select_related("service_demandeur")
    return render(request, "achats/demandes_signees_bo.html", {"demandes": demandes})


@login_required
def demande_create(request):
    if request.method == "POST":
        form = DemandeAchatForm(request.POST)
        if form.is_valid():
            demande = form.save(commit=False)
            demande.created_by = request.user
            demande.save()
            messages.success(request, f"Demande {demande.reference} créée.")
            return redirect("achats:detail", pk=demande.pk)
    else:
        form = DemandeAchatForm()
    return render(request, "achats/demande_form.html", {"form": form})


@login_required
def demande_detail(request, pk):
    demande = get_object_or_404(DemandeAchat.objects.select_related("service_demandeur"), pk=pk)
    approbation_form = ApprobationForm()

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "approbation":
            approbation_form = ApprobationForm(request.POST)
            if approbation_form.is_valid():
                approbation = approbation_form.save(commit=False)
                approbation.demande = demande
                approbation.valideur = request.user
                approbation.save()
                messages.success(request, "Approbation enregistrée.")
                return redirect("achats:detail", pk=demande.pk)

        elif action == "enregistrer_bureau_ordre":
            if request.user.role in {Role.AGENT_BUREAU_ORDRE, Role.ADMINISTRATEUR}:
                demande.enregistrer_au_bureau_ordre()
                messages.success(request, f"Demande enregistrée au bureau d'ordre sous le n° {demande.numero_ordre_bo}.")
            else:
                messages.error(request, "Vous n'avez pas les droits pour effectuer cette action.")
            return redirect("achats:detail", pk=demande.pk)

        elif action in ACTIONS:
            target_status, roles, msg = ACTIONS[action]
            if request.user.role not in roles:
                messages.error(request, "Vous n'avez pas les droits pour effectuer cette action.")
            else:
                demande.statut = target_status
                if action == "signer_directeur":
                    demande.date_signature_directeur = timezone.localdate()
                    demande.decision_directeur = request.POST.get("decision_directeur", demande.decision_directeur)
                demande.save()
                messages.success(request, msg)
            return redirect("achats:detail", pk=demande.pk)

    next_actions = [
        (code, ACTION_LABELS[code]) for code in NEXT_ACTIONS.get(demande.statut, [])
    ]

    return render(
        request,
        "achats/demande_detail.html",
        {
            "demande": demande,
            "approbation_form": approbation_form,
            "approbations": demande.approbations.select_related("valideur"),
            "documents": demande.documents.all(),
            "next_actions": next_actions,
        },
    )
