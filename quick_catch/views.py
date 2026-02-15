from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .forms import BrainDumpForm
from .models import BrainDump, Profile, TriageRun, TriageTask


def _get_profile(user):
    """Get or create Quick Catch profile for user."""
    profile, _ = Profile.objects.get_or_create(
        user=user,
        defaults={
            "default_energy_level": "medium",
            "timezone": "America/New_York",
            "email_opt_in": True,
            "neurodivergent_focus": "unspecified",
        },
    )
    return profile


@login_required
def dump_view(request):
    """Brain dump entry: large textarea + energy level + Process Dump button."""
    profile = _get_profile(request.user)
    if request.method == "POST":
        form = BrainDumpForm(request.POST)
        if form.is_valid():
            dump = form.save(commit=False)
            dump.user = request.user
            dump.source = "web"
            dump.save()
            _create_placeholder_triage_run(dump)
            return redirect("quick_catch:result", dump_id=str(dump.id))
    else:
        form = BrainDumpForm(initial={"energy_level": profile.default_energy_level})
    return render(
        request,
        "quick_catch/dump.html",
        {"form": form, "profile": profile},
    )


def _create_placeholder_triage_run(dump):
    """Create a TriageRun with placeholder content until the AI pipeline runs."""
    TriageRun.objects.get_or_create(
        dump=dump,
        prompt_version="v1",
        defaults={
            "user": dump.user,
            "model_name": "placeholder",
            "action_plan_md": (
                "Your 10-Minute Action Plan will appear here after processing. "
                "The AI pipeline can be wired to replace this placeholder."
            ),
            "top_3_task_ids": [],
            "blockers": [],
        },
    )


@login_required
def result_view(request, dump_id):
    """Show action plan and top 3 for a brain dump (user must own the dump)."""
    dump = get_object_or_404(BrainDump, id=dump_id, user=request.user)
    triage_run = (
        dump.triage_runs.order_by("-created_at").first()
        if hasattr(dump, "triage_runs") else None
    )
    top_3_tasks = []
    if triage_run and triage_run.top_3_task_ids:
        task_ids = triage_run.top_3_task_ids
        tasks_by_id = {
            str(t.id): t
            for t in TriageTask.objects.filter(
                id__in=task_ids,
                user=request.user,
            )
        }
        top_3_tasks = [tasks_by_id[tid] for tid in task_ids if tid in tasks_by_id]
    return render(
        request,
        "quick_catch/result.html",
        {
            "dump": dump,
            "triage_run": triage_run,
            "top_3_tasks": top_3_tasks,
        },
    )


@login_required
def dump_list_view(request):
    """List current user's brain dumps, most recent first."""
    dumps = BrainDump.objects.filter(user=request.user).order_by("-created_at")[:50]
    return render(request, "quick_catch/dump_list.html", {"dumps": dumps})


@login_required
def profile_view(request):
    """Quick Catch profile/settings (default energy, timezone, email opt-in, neurodivergent focus)."""
    profile = _get_profile(request.user)
    return render(request, "quick_catch/profile.html", {"profile": profile})
