from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .ai import run_triage
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


def _save_triage_result(dump, result):
    """Create TriageRun and TriageTasks from AI TriageResult."""
    run = TriageRun.objects.create(
        dump=dump,
        user=dump.user,
        prompt_version="v1",
        model_name=result.model_name,
        temperature=0.2,
        action_plan_md=result.action_plan,
        blockers=result.blockers,
        top_3_task_ids=[],  # set after tasks exist
        latency_ms=result.latency_ms,
    )
    tasks_by_index = {}
    for i, item in enumerate(result.extracted_tasks):
        if not isinstance(item, dict):
            continue
        title = (item.get("title") or "").strip() or f"Task {i + 1}"
        micro_steps = item.get("micro_steps")
        if not isinstance(micro_steps, list):
            micro_steps = []
        micro_steps = [str(s) for s in micro_steps][:20]
        is_top3 = i in result.top_3_indices
        rank_order = (result.top_3_indices.index(i) + 1) if is_top3 else None
        task = TriageTask.objects.create(
            triage_run=run,
            user=dump.user,
            title=title,
            micro_steps=micro_steps,
            is_top3=is_top3,
            rank_order=rank_order,
        )
        tasks_by_index[i] = task
    top_3_ids = [
        str(tasks_by_index[i].id)
        for i in result.top_3_indices
        if i in tasks_by_index
    ]
    run.top_3_task_ids = top_3_ids
    run.save(update_fields=["top_3_task_ids"])
    return run


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
            result = run_triage(dump.input_text, dump.energy_level)
            _save_triage_result(dump, result)
            return redirect("quick_catch:result", dump_id=str(dump.id))
    else:
        form = BrainDumpForm(initial={"energy_level": profile.default_energy_level})
    return render(
        request,
        "quick_catch/dump.html",
        {"form": form, "profile": profile},
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
