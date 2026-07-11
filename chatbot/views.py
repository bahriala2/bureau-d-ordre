from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .models import ChatMessage
from .services import LLMError, ask_llm, get_llm_config


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

    config = get_llm_config()
    return render(
        request,
        "chatbot/chat.html",
        {
            "historique": historique,
            "llm_model": config["model"],
            "llm_base_url": config["base_url"],
            "cle_detectee": bool(config["api_key"]),
            "mode_local": "openrouter" not in config["base_url"],
        },
    )
