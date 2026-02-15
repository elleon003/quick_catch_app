from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import BrainDump, Email, Profile, TriageRun, TriageTask


@admin.register(Profile)
class ProfileAdmin(ModelAdmin):
    list_display = ("user", "default_energy_level", "timezone", "email_opt_in", "neurodivergent_focus", "updated_at")
    list_filter = ("default_energy_level", "email_opt_in", "neurodivergent_focus")
    search_fields = ("user__email", "user__first_name", "user__last_name")
    readonly_fields = ("created_at", "updated_at")
    autocomplete_fields = ("user",)


@admin.register(BrainDump)
class BrainDumpAdmin(ModelAdmin):
    list_display = ("id", "user", "energy_level", "source", "word_count", "created_at")
    list_filter = ("energy_level", "source", "created_at")
    search_fields = ("user__email", "input_text")
    readonly_fields = ("id", "word_count", "created_at")
    autocomplete_fields = ("user",)
    date_hierarchy = "created_at"


class TriageTaskInline(admin.TabularInline):
    model = TriageTask
    extra = 0
    readonly_fields = ("id", "created_at")
    fields = ("title", "rank_order", "is_top3", "best_energy", "estimated_minutes", "category")
    show_change_link = True


class EmailInline(admin.TabularInline):
    model = Email
    extra = 0
    readonly_fields = ("id", "created_at", "send_after")
    fields = ("to_email", "subject", "status", "send_after", "provider_message_id", "error_message")
    show_change_link = True


@admin.register(TriageRun)
class TriageRunAdmin(ModelAdmin):
    list_display = ("id", "dump", "user", "model_name", "prompt_version", "detected_crisis", "created_at")
    list_filter = ("prompt_version", "detected_crisis", "created_at")
    search_fields = ("user__email", "summary_one_liner", "action_plan_md")
    readonly_fields = ("id", "created_at", "latency_ms", "token_in", "token_out")
    autocomplete_fields = ("dump", "user")
    date_hierarchy = "created_at"
    inlines = (TriageTaskInline, EmailInline)


@admin.register(TriageTask)
class TriageTaskAdmin(ModelAdmin):
    list_display = ("title", "triage_run", "user", "rank_order", "is_top3", "best_energy", "category", "created_at")
    list_filter = ("is_top3", "best_energy", "category", "created_at")
    search_fields = ("title", "user__email")
    readonly_fields = ("id", "created_at")
    autocomplete_fields = ("triage_run", "user")
    date_hierarchy = "created_at"


@admin.register(Email)
class EmailAdmin(ModelAdmin):
    list_display = ("id", "user", "triage_run", "to_email", "subject", "status", "send_after", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("user__email", "to_email", "subject")
    readonly_fields = ("id", "created_at")
    autocomplete_fields = ("user", "triage_run")
    date_hierarchy = "created_at"
