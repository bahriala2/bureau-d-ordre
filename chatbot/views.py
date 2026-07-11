from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .models import ChatMessage
from .services import LLM_BASE_URL, LLM_MODEL, LLMError, ask_llm


@login_required
def chat(request):
    historique = list(ChatMessage.objects.filter(utilisateur=request.user))

    if request.method == "POST":
        if "effacer" in request.POST:
            ChatMessage.objects.filter(utilisateur=request.user).delete()
            return redirect("chatbot:chat")

        question = request.POST.get("question", "").strip()
        if question:
            ChatMessage.objects.create(utilisateur=request.user, role="user", contenu=question)
            try:
                reponse = ask_llm(question, historique=historique)
                ChatMessage.objects.create(utilisateur=request.user, role="assistant", contenu=reponse)
            except LLMError as exc:
                messages.error(request, str(exc))
            return redirect("chatbot:chat")

    return render(
        request,
        "chatbot/chat.html",
        {
            "historique": historique,
            "llm_model": LLM_MODEL,
            "llm_base_url": LLM_BASE_URL,
        },
    )
