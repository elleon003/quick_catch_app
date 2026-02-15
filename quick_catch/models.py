import uuid

from django.conf import settings
from django.db import models


# Choice constants (match SQL check constraints)
ENERGY_LEVELS = ("low", "medium", "high")
SOURCE_CHOICES = ("web", "mobile", "api")
EMAIL_STATUS_CHOICES = ("queued", "sent", "failed", "canceled")
NEURODIVERGENT_FOCUS_CHOICES = ("adhd", "autistic", "audhd", "unspecified")


class Profile(models.Model):
    """User profile (1:1 with auth user). Preferences and optional segmentation."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name="quick_catch_profile",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    default_energy_level = models.CharField(
        max_length=10,
        choices=[(x, x) for x in ENERGY_LEVELS],
        default="medium",
    )
    timezone = models.CharField(max_length=63, default="America/New_York")
    email_opt_in = models.BooleanField(default=True)  # type: ignore[assignment]  # type: ignore[assignment]

    neurodivergent_focus = models.CharField(
        max_length=20,
        choices=[(x, x) for x in NEURODIVERGENT_FOCUS_CHOICES],
        default="unspecified",
    )

    class Meta:
        db_table = "profiles"
        indexes = [
            models.Index(fields=["email_opt_in"]),
        ]

    def __str__(self):
        return f"Profile({self.user_id})"


class BrainDump(models.Model):
    """Raw brain dump input from the user."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="brain_dumps",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    energy_level = models.CharField(
        max_length=10,
        choices=[(x, x) for x in ENERGY_LEVELS],
    )
    input_text = models.TextField()

    source = models.CharField(
        max_length=10,
        choices=[(x, x) for x in SOURCE_CHOICES],
        default="web",
    )
    word_count = models.PositiveIntegerField(
        editable=False,
        null=True,
        blank=True,
        help_text="Set from input_text on save; optional DB-generated column in Postgres.",
    )

    class Meta:
        db_table = "brain_dumps"
        indexes = [
            models.Index(fields=["user", "-created_at"], name="brain_dumps_user_created_idx"),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return str(self.id)

    def save(self, *args, **kwargs):
        if self.input_text is not None:
            self.word_count = len(self.input_text.split()) if self.input_text.strip() else 0
        super().save(*args, **kwargs)


class TriageRun(models.Model):
    """AI processing result for a brain dump. Supports re-runs with different prompts/models."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    dump = models.ForeignKey(
        BrainDump,
        on_delete=models.CASCADE,
        related_name="triage_runs",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="triage_runs",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    model_name = models.CharField(max_length=128)
    prompt_version = models.CharField(max_length=32, default="v1")
    temperature = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0.2,
        null=True,
        blank=True,
    )

    top_3_task_ids = models.JSONField(
        default=list,
        help_text="List of triage_tasks.id (UUIDs as strings).",
    )
    blockers = models.JSONField(default=list)
    action_plan_md = models.TextField()
    summary_one_liner = models.CharField(max_length=512, null=True, blank=True)

    detected_crisis = models.BooleanField(default=False)  # type: ignore[assignment]
    latency_ms = models.PositiveIntegerField(null=True, blank=True)
    token_in = models.PositiveIntegerField(null=True, blank=True)
    token_out = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        db_table = "triage_runs"
        constraints = [
            models.UniqueConstraint(
                fields=["dump", "prompt_version"],
                name="triage_runs_dump_prompt_version_uniq",
            ),
        ]
        indexes = [
            models.Index(
                fields=["dump", "-created_at"],
                name="triage_runs_dump_created_idx",
            ),
            models.Index(
                fields=["user", "-created_at"],
                name="triage_runs_user_created_idx",
            ),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return str(self.id)


class TriageTask(models.Model):
    """Extracted task from a triage run (1 run : many tasks)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    triage_run = models.ForeignKey(
        TriageRun,
        on_delete=models.CASCADE,
        related_name="triage_tasks",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="triage_tasks",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    title = models.CharField(max_length=512)
    micro_steps = models.JSONField(default=list)
    estimated_minutes = models.PositiveIntegerField(null=True, blank=True)

    rank_score = models.DecimalField(
        max_digits=6,
        decimal_places=3,
        null=True,
        blank=True,
    )
    rank_order = models.PositiveIntegerField(null=True, blank=True)
    is_top3 = models.BooleanField(default=False)  # type: ignore[assignment]  

    best_energy = models.CharField(
        max_length=10,
        choices=[(x, x) for x in ENERGY_LEVELS],
        null=True,
        blank=True,
    )
    friction_score = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="0..10, higher = more aversive.",
    )
    category = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        help_text="e.g. admin, sales, dev, personal (AI inferred).",
    )
    evidence_spans = models.JSONField(
        default=list,
        help_text='e.g. [{"start": 120, "end": 180, "text": "..."}]',
    )

    class Meta:
        db_table = "triage_tasks"
        indexes = [
            models.Index(
                fields=["triage_run", "rank_order"],
                name="triage_tasks_run_rank_idx",
            ),
            models.Index(
                fields=["user", "-created_at"],
                name="triage_tasks_user_created_idx",
            ),
            models.Index(
                fields=["user", "is_top3", "-created_at"],
                name="triage_tasks_is_top3_idx",
            ),
        ]
        ordering = ["triage_run", "rank_order"]

    def __str__(self):
        return str(self.title)[:50] if self.title else str(self.id)


class Email(models.Model):
    """Email delivery log (e.g. 'Email me this' queue)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="quick_catch_emails",
    )
    triage_run = models.ForeignKey(
        TriageRun,
        on_delete=models.CASCADE,
        related_name="emails",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    send_after = models.DateTimeField(auto_now_add=True)

    to_email = models.EmailField()
    subject = models.CharField(max_length=512)
    body_md = models.TextField()

    status = models.CharField(
        max_length=16,
        choices=[(x, x) for x in EMAIL_STATUS_CHOICES],
        default="queued",
    )
    provider_message_id = models.CharField(max_length=256, null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "emails"
        indexes = [
            models.Index(
                fields=["status", "send_after"],
                name="emails_status_send_after_idx",
            ),
            models.Index(
                fields=["user", "-created_at"],
                name="emails_user_created_idx",
            ),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{str(self.subject)[:30]} ({self.status})" if self.subject else str(self.id)  # type: ignore[union-attr]
