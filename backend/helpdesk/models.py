from django.db import models
import uuid

from helpdesk.db_fields import PortableVectorField


class TimestampedModel(models.Model):
    """Shared timestamp fields for future domain models."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class SourceChunk(TimestampedModel):
    """Persisted retrieval index chunks from approved repositories."""

    # Source provenance fields used for policy checks and citation rendering.
    repository_url = models.URLField()
    commit_sha = models.CharField(max_length=64)
    source_path = models.CharField(max_length=512)
    chunk_id = models.CharField(max_length=128, unique=True)
    label = models.CharField(max_length=255, blank=True)

    # Indexed content and retrieval metadata.
    text = models.TextField()
    standards_scope = models.JSONField(default=list, blank=True)
    quality_score = models.FloatField(default=0.5)
    # Structure-aware chunking metadata.
    chunk_type = models.CharField(max_length=32, default="prose", blank=True)
    doc_type = models.CharField(max_length=32, default="guide", blank=True)
    heading = models.CharField(max_length=512, blank=True)
    structured_metadata = models.JSONField(default=dict, blank=True)
    # PostgreSQL uses pgvector; SQLite falls back to JSON via PortableVectorField.
    embedding_vector = PortableVectorField(dimensions=1536, default=list, blank=True)

    class Meta:
        ordering = ["-quality_score", "source_path", "chunk_id"]
        indexes = [
            models.Index(fields=["repository_url"]),
            models.Index(fields=["source_path"]),
            models.Index(fields=["quality_score"]),
        ]

    def __str__(self):
        return f"SourceChunk(chunk_id={self.chunk_id}, source_path={self.source_path})"


class IndexedSourceFile(TimestampedModel):
    """Tracks per-file hash and commit for incremental index runs."""

    # Uniqueness is enforced on (repository_url, source_path) to represent one tracked file.
    repository_url = models.URLField()
    source_path = models.CharField(max_length=512)
    commit_sha = models.CharField(max_length=64)
    content_hash = models.CharField(max_length=64)

    class Meta:
        ordering = ["repository_url", "source_path"]
        constraints = [
            models.UniqueConstraint(
                fields=["repository_url", "source_path"],
                name="uniq_indexed_source_file_repo_path",
            )
        ]

    def __str__(self):
        return f"IndexedSourceFile(repo={self.repository_url}, path={self.source_path})"


class IndexRunMetric(TimestampedModel):
    """Telemetry for index build executions."""

    STATUS_SUCCESS = "success"
    STATUS_FAILED = "failed"
    STATUS_CHOICES = [
        (STATUS_SUCCESS, "Success"),
        (STATUS_FAILED, "Failed"),
    ]

    MODE_FULL = "full"
    MODE_INCREMENTAL = "incremental"
    MODE_CHOICES = [
        (MODE_FULL, "Full"),
        (MODE_INCREMENTAL, "Incremental"),
    ]

    # Run context.
    repository_url = models.URLField()
    repository_path = models.CharField(max_length=1024)
    profile = models.CharField(max_length=64, default="default")
    mode = models.CharField(max_length=32, choices=MODE_CHOICES)
    status = models.CharField(max_length=32, choices=STATUS_CHOICES)

    # Aggregated counters for this run.
    scanned_files = models.IntegerField(default=0)
    skipped_files = models.IntegerField(default=0)
    created_chunks = models.IntegerField(default=0)
    updated_chunks = models.IntegerField(default=0)
    deleted_chunks = models.IntegerField(default=0)

    # Operational diagnostics.
    duration_ms = models.IntegerField(default=0)
    error_message = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"IndexRunMetric(repo={self.repository_url}, mode={self.mode}, status={self.status})"


class QuestionEvent(TimestampedModel):
    """Stores a full answer orchestration outcome for analytics and traceability."""

    MODE_FAQ = "faq"
    MODE_RAG = "rag"
    MODE_ABSTAIN = "abstain"
    MODE_CHOICES = [
        (MODE_FAQ, "FAQ"),
        (MODE_RAG, "RAG"),
        (MODE_ABSTAIN, "Abstain"),
    ]

    REASON_INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    REASON_POLICY_BLOCK = "POLICY_BLOCK"
    REASON_RETRIEVAL_LOW_QUALITY = "RETRIEVAL_LOW_QUALITY"
    REASON_UNKNOWN = "UNKNOWN"
    ABSTENTION_REASON_CHOICES = [
        (REASON_INSUFFICIENT_EVIDENCE, "Insufficient evidence"),
        (REASON_POLICY_BLOCK, "Policy block"),
        (REASON_RETRIEVAL_LOW_QUALITY, "Retrieval low quality"),
        (REASON_UNKNOWN, "Unknown"),
    ]

    # Request identity and caller context.
    request_id = models.CharField(max_length=128, db_index=True)
    question = models.TextField()
    session_id = models.CharField(max_length=128, blank=True)
    user_id = models.CharField(max_length=128, blank=True)
    standards_scope = models.JSONField(default=list, blank=True)
    language = models.CharField(max_length=16, default="en")

    # Final answer result selected by orchestration.
    mode = models.CharField(max_length=16, choices=MODE_CHOICES)
    confidence = models.FloatField(default=0.0)
    answer = models.TextField(blank=True)
    abstained = models.BooleanField(default=False)
    abstention_reason = models.CharField(
        max_length=64,
        choices=ABSTENTION_REASON_CHOICES,
        null=True,
        blank=True,
    )
    review_required = models.BooleanField(default=False)

    # Trace links used by downstream debugging and editorial workflows.
    matched_faq_entry_id = models.CharField(max_length=128, null=True, blank=True)
    retrieval_event_ids = models.JSONField(default=list, blank=True)
    evidence_link_ids = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"QuestionEvent(id={self.id}, mode={self.mode}, request_id={self.request_id})"


class FAQEntry(TimestampedModel):
    """Canonical FAQ intent entity used by the FAQ-first orchestration path."""

    faq_entry_id = models.CharField(max_length=128, unique=True)
    normalized_intent = models.CharField(max_length=512)
    standards_scope = models.JSONField(default=list, blank=True)
    keyword_tokens = models.JSONField(default=list, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["faq_entry_id"]
        indexes = [
            models.Index(fields=["faq_entry_id"], name="faqentry_id_idx"),
            models.Index(fields=["is_active"], name="faqentry_active_idx"),
        ]

    def __str__(self):
        return f"FAQEntry(faq_entry_id={self.faq_entry_id})"


class FAQVersion(TimestampedModel):
    """Versioned FAQ answer record to preserve history of canonical responses."""

    faq_entry = models.ForeignKey(
        FAQEntry,
        on_delete=models.CASCADE,
        related_name="versions",
    )
    version = models.IntegerField(default=1)
    answer = models.TextField()
    citations = models.JSONField(default=list, blank=True)
    confidence = models.FloatField(default=0.85)
    review_required = models.BooleanField(default=False)
    is_published = models.BooleanField(default=True)

    class Meta:
        ordering = ["faq_entry", "-version"]
        constraints = [
            models.UniqueConstraint(
                fields=["faq_entry", "version"],
                name="uniq_faq_version_per_entry",
            )
        ]
        indexes = [
            models.Index(fields=["is_published"], name="faqversion_pub_idx"),
        ]

    def __str__(self):
        return f"FAQVersion(entry={self.faq_entry.faq_entry_id}, version={self.version})"


class RetrievalEvent(TimestampedModel):
    """Per-chunk retrieval telemetry emitted by the RAG fallback flow."""

    retrieval_event_id = models.CharField(max_length=128, unique=True)
    question_event = models.ForeignKey(
        QuestionEvent,
        on_delete=models.CASCADE,
        related_name="retrieval_events",
    )
    repository_url = models.URLField()
    commit_sha = models.CharField(max_length=64)
    source_path = models.CharField(max_length=512)
    chunk_id = models.CharField(max_length=128)
    score = models.FloatField(default=0.0)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["retrieval_event_id"], name="ret_event_id_idx"),
            models.Index(fields=["repository_url"], name="ret_repo_idx"),
            models.Index(fields=["source_path"], name="ret_source_idx"),
        ]

    def __str__(self):
        return (
            f"RetrievalEvent(retrieval_event_id={self.retrieval_event_id}, "
            f"chunk_id={self.chunk_id})"
        )


class AnswerEvidenceLink(TimestampedModel):
    """Persisted claim/evidence links to support answer auditability."""

    evidence_link_id = models.CharField(max_length=128, unique=True)
    question_event = models.ForeignKey(
        QuestionEvent,
        on_delete=models.CASCADE,
        related_name="answer_evidence_links",
    )
    answer_id = models.CharField(max_length=128)
    repository_url = models.URLField()
    commit_sha = models.CharField(max_length=64)
    source_path = models.CharField(max_length=512)
    chunk_id = models.CharField(max_length=128)
    label = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["evidence_link_id"], name="evlink_id_idx"),
            models.Index(fields=["answer_id"], name="evlink_answer_idx"),
            models.Index(fields=["source_path"], name="evlink_source_idx"),
        ]

    def __str__(self):
        return (
            f"AnswerEvidenceLink(evidence_link_id={self.evidence_link_id}, "
            f"answer_id={self.answer_id})"
        )


class OntologyAssetVersion(TimestampedModel):
    """Tracks versioned ontology assets loaded into the semantic layer."""

    ontology_key = models.CharField(max_length=64, unique=True)
    file_path = models.CharField(max_length=512)
    graph_uri = models.CharField(max_length=255)
    version = models.CharField(max_length=64)
    content_hash = models.CharField(max_length=64)
    graphdb_repository = models.CharField(max_length=255, blank=True)
    last_loaded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["ontology_key"]
        indexes = [
            models.Index(fields=["version"], name="ontology_version_idx"),
            models.Index(fields=["content_hash"], name="ontology_hash_idx"),
        ]

    def __str__(self):
        return f"OntologyAssetVersion(key={self.ontology_key}, version={self.version})"


class EvidenceProvenance(TimestampedModel):
    """Persisted provenance payload for answer evidence and rule derivations."""

    provenance_id = models.CharField(max_length=128, unique=True)
    question_event = models.ForeignKey(
        QuestionEvent,
        on_delete=models.CASCADE,
        related_name="evidence_provenance_records",
    )
    evidence_link = models.ForeignKey(
        AnswerEvidenceLink,
        on_delete=models.CASCADE,
        related_name="provenance_records",
    )
    core_concepts = models.JSONField(default=list, blank=True)
    ontology_versions = models.JSONField(default=list, blank=True)
    rule_conclusions = models.JSONField(default=list, blank=True)
    provenance_payload = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["provenance_id"], name="prov_id_idx"),
            models.Index(fields=["question_event"], name="prov_qevent_idx"),
        ]

    def __str__(self):
        return f"EvidenceProvenance(provenance_id={self.provenance_id})"


class EditorialQueueItem(TimestampedModel):
    """Represents a review unit routed to the editorial workflow."""

    REASON_LOW_CONFIDENCE = "LOW_CONFIDENCE"
    REASON_CITATION_GAP = "CITATION_GAP"
    REASON_POLICY_REVIEW = "POLICY_REVIEW"
    REASON_USER_ESCALATION = "USER_ESCALATION"
    REASON_CHOICES = [
        (REASON_LOW_CONFIDENCE, "Low confidence"),
        (REASON_CITATION_GAP, "Citation gap"),
        (REASON_POLICY_REVIEW, "Policy review"),
        (REASON_USER_ESCALATION, "User escalation"),
    ]

    PRIORITY_LOW = "low"
    PRIORITY_NORMAL = "normal"
    PRIORITY_HIGH = "high"
    PRIORITY_CHOICES = [
        (PRIORITY_LOW, "Low"),
        (PRIORITY_NORMAL, "Normal"),
        (PRIORITY_HIGH, "High"),
    ]

    STATUS_DRAFT = "draft"
    STATUS_REVIEW = "review"
    STATUS_APPROVED = "approved"
    STATUS_REJECTED = "rejected"
    STATUS_PUBLISHED = "published"
    STATUS_CHOICES = [
        (STATUS_DRAFT, "Draft"),
        (STATUS_REVIEW, "Review"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_REJECTED, "Rejected"),
        (STATUS_PUBLISHED, "Published"),
    ]

    # External/public identifier for queue integrations.
    queue_item_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    # Link back to the originating answer outcome.
    question_event = models.ForeignKey(
        QuestionEvent,
        on_delete=models.CASCADE,
        related_name="editorial_queue_items",
    )

    # Editorial routing metadata.
    reason = models.CharField(max_length=32, choices=REASON_CHOICES)
    priority = models.CharField(max_length=8, choices=PRIORITY_CHOICES, default=PRIORITY_NORMAL)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_DRAFT)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"EditorialQueueItem(queue_item_id={self.queue_item_id}, status={self.status})"


class EditorialQueueTransition(TimestampedModel):
    """Audit record for state transitions performed on editorial queue items."""

    ACTION_SUBMIT_FOR_REVIEW = "submit_for_review"
    ACTION_REQUEST_CHANGES = "request_changes"
    ACTION_APPROVE = "approve"
    ACTION_REJECT = "reject"
    ACTION_PUBLISH = "publish"
    ACTION_REOPEN = "reopen"
    ACTION_CHOICES = [
        (ACTION_SUBMIT_FOR_REVIEW, "Submit for review"),
        (ACTION_REQUEST_CHANGES, "Request changes"),
        (ACTION_APPROVE, "Approve"),
        (ACTION_REJECT, "Reject"),
        (ACTION_PUBLISH, "Publish"),
        (ACTION_REOPEN, "Reopen"),
    ]

    queue_item = models.ForeignKey(
        EditorialQueueItem,
        on_delete=models.CASCADE,
        related_name="transitions",
    )
    action = models.CharField(max_length=32, choices=ACTION_CHOICES)
    from_status = models.CharField(max_length=16, choices=EditorialQueueItem.STATUS_CHOICES)
    to_status = models.CharField(max_length=16, choices=EditorialQueueItem.STATUS_CHOICES)
    actor_id = models.CharField(max_length=128, blank=True)
    actor_roles = models.JSONField(default=list, blank=True)
    comment = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return (
            f"EditorialQueueTransition(queue_item_id={self.queue_item.queue_item_id}, "
            f"action={self.action}, from={self.from_status}, to={self.to_status})"
        )
