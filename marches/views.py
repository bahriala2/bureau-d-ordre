from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import MarcheForm
from .models import Marche, StatutMarche


@login_required
def marche_list(request):
    marches = Marche.objects.select_related("service_demandeur").all()
    statut = request.GET.get("statut")
    if statut:
        marches = marches.filter(statut=statut)
    return render(request, "marches/marche_list.html", {"marches": marches, "statuts": StatutMarche.choices, "statut_actif": statut})


@login_required
def marche_create(request):
    if request.method == "POST":
        form = MarcheForm(request.POST)
        if form.is_valid():
            marche = form.save(commit=False)
            marche.created_by = request.user
            marche.save()
            messages.success(request, f"Marché {marche.reference} créé.")
            return redirect("marches:detail", pk=marche.pk)
    else:
        form = MarcheForm()
    return render(request, "marches/marche_form.html", {"form": form})


@login_required
def marche_detail(request, pk):
    marche = get_object_or_404(Marche.objects.select_related("service_demandeur", "demande_achat"), pk=pk)
    return render(request, "marches/marche_detail.html", {"marche": marche, "documents": marche.documents.all()})
