import tempfile

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404, redirect, render

from documents.models import Document, TypeDocument
from documents.services.ocr import analyze_document

from .forms import CourrierForm, CourrierSearchForm, ScanUploadForm, StatutChangeForm
from .models import Courrier


@login_required
def courrier_list(request):
    form = CourrierSearchForm(request.GET or None)
    courriers = Courrier.objects.select_related("service").all()

    if form.is_valid():
        q = form.cleaned_data.get("q")
        if q:
            from django.db.models import Q

            courriers = courriers.filter(
                Q(numero_ordre__icontains=q)
                | Q(objet__icontains=q)
                | Q(emetteur__icontains=q)
                | Q(recepteur__icontains=q)
                | Q(reference_externe__icontains=q)
            )
        if form.cleaned_data.get("type_courrier"):
            courriers = courriers.filter(type_courrier=form.cleaned_data["type_courrier"])
        if form.cleaned_data.get("statut"):
            courriers = courriers.filter(statut=form.cleaned_data["statut"])
        if form.cleaned_data.get("service"):
            courriers = courriers.filter(service=form.cleaned_data["service"])

    return render(request, "courrier/courrier_list.html", {"courriers": courriers, "form": form})


@login_required
def courrier_create(request):
    extraction = None
    initial = {}
    scan_form = ScanUploadForm(request.POST or None, request.FILES or None)

    if request.method == "POST" and "analyser" in request.POST:
        if scan_form.is_valid() and scan_form.cleaned_data.get("fichier"):
            uploaded = scan_form.cleaned_data["fichier"]
            with tempfile.NamedTemporaryFile(suffix="_" + uploaded.name, delete=False) as tmp:
                for chunk in uploaded.chunks():
                    tmp.write(chunk)
                tmp_path = tmp.name
            extraction = analyze_document(tmp_path)
            initial = {
                "objet": extraction.objet,
                "emetteur": extraction.emetteur,
                "recepteur": extraction.recepteur,
                "reference_externe": extraction.reference,
                "resume": extraction.resume,
                "urgence": "URGENT" if extraction.urgence == "Urgent" else "NORMAL",
            }
            if not extraction.ocr_disponible:
                messages.warning(
                    request,
                    "OCR indisponible sur ce serveur (dépendances optionnelles non installées). "
                    "Veuillez saisir les informations manuellement.",
                )
            else:
                messages.info(request, "Document analysé. Vérifiez les informations proposées avant l'enregistrement.")
        form = CourrierForm(initial=initial)

    elif request.method == "POST" and "enregistrer" in request.POST:
        form = CourrierForm(request.POST)
        if form.is_valid():
            courrier = form.save(commit=False)
            courrier.created_by = request.user
            courrier.statut = "ENREGISTRE"
            courrier.save()
            courrier.log_action(request.user, "Enregistrement", "Courrier enregistré au bureau d'ordre")

            uploaded = request.FILES.get("fichier")
            if uploaded:
                Document.objects.create(
                    fichier=uploaded,
                    nom=uploaded.name,
                    type_document=TypeDocument.IMAGE if not uploaded.name.lower().endswith(".pdf") else TypeDocument.PDF,
                    content_type=ContentType.objects.get_for_model(Courrier),
                    object_id=courrier.id,
                    uploaded_by=request.user,
                )
            messages.success(request, f"Courrier {courrier.numero_ordre} enregistré avec succès.")
            return redirect("courrier:detail", pk=courrier.pk)
    else:
        form = CourrierForm()

    return render(
        request,
        "courrier/courrier_form.html",
        {"form": form, "scan_form": scan_form, "extraction": extraction},
    )


@login_required
def courrier_detail(request, pk):
    courrier = get_object_or_404(Courrier.objects.select_related("service"), pk=pk)
    statut_form = StatutChangeForm(initial={"statut": courrier.statut})

    if request.method == "POST":
        statut_form = StatutChangeForm(request.POST)
        if statut_form.is_valid():
            ancien_statut = courrier.get_statut_display()
            courrier.statut = statut_form.cleaned_data["statut"]
            courrier.save()
            courrier.log_action(
                request.user,
                f"Changement de statut : {ancien_statut} → {courrier.get_statut_display()}",
                statut_form.cleaned_data.get("commentaire", ""),
            )
            messages.success(request, "Statut mis à jour.")
            return redirect("courrier:detail", pk=courrier.pk)

    return render(
        request,
        "courrier/courrier_detail.html",
        {
            "courrier": courrier,
            "statut_form": statut_form,
            "historique": courrier.historique.select_related("user"),
            "documents": courrier.documents.all(),
        },
    )
