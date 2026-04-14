from rest_framework import serializers


STANDARDS_SCOPE_CHOICES = ["Transmodel", "NeTEx", "SIRI", "OJP", "OpRa", "DATEX II"]


class AnswerOptionsSerializer(serializers.Serializer):
    """Optional tuning knobs for FAQ/RAG orchestration behavior."""

    # Upper bound for returned citation objects in the response payload.
    maxCitations = serializers.IntegerField(required=False, min_value=1, max_value=20, default=5)

    # If true, the service may abstain instead of returning weak/unsafe answers.
    allowAbstain = serializers.BooleanField(required=False, default=True)

    # Minimum FAQ match confidence required to accept FAQ-first path.
    faqMinConfidence = serializers.FloatField(required=False, min_value=0.0, max_value=1.0, default=0.85)

    # Retrieval candidate limits for RAG fallback.
    retrievalTopK = serializers.IntegerField(required=False, min_value=1, max_value=20, default=6)
    retrievalMinScore = serializers.FloatField(required=False, min_value=0.0, max_value=1.0, default=0.62)


class AnswerRequestSerializer(serializers.Serializer):
    """Primary request payload for the answer orchestration endpoint."""

    question = serializers.CharField()
    sessionId = serializers.CharField(required=False, allow_blank=True)
    userId = serializers.CharField(required=False, allow_blank=True)
    # Scope filter aligns request processing with known standards families.
    standardsScope = serializers.ListField(
        child=serializers.ChoiceField(choices=STANDARDS_SCOPE_CHOICES),
        required=False,
        allow_empty=True,
    )
    language = serializers.CharField(required=False, default="en")
    generationProfile = serializers.ChoiceField(
        choices=["deterministic-grounded", "llm-ready"],
        required=False,
        default="llm-ready",
    )
    options = AnswerOptionsSerializer(required=False)


class PromotionCandidatesQuerySerializer(serializers.Serializer):
    """Query params for generating FAQ promotion candidates from telemetry."""

    windowDays = serializers.IntegerField(required=False, min_value=1, default=14)
    minCount = serializers.IntegerField(required=False, min_value=1, default=5)
    onlyUnresolved = serializers.BooleanField(required=False, default=False)


class EditorialQueueRequestSerializer(serializers.Serializer):
    """Payload for routing question outcomes into editorial queue."""

    questionEventId = serializers.CharField()
    reason = serializers.ChoiceField(
        choices=["LOW_CONFIDENCE", "CITATION_GAP", "POLICY_REVIEW", "USER_ESCALATION"]
    )
    priority = serializers.ChoiceField(
        choices=["low", "normal", "high"], required=False, default="normal"
    )


class EditorialQueueListQuerySerializer(serializers.Serializer):
    """Query params for listing editorial queue board items with paging and filters."""

    status = serializers.ChoiceField(
        choices=["draft", "review", "approved", "rejected", "published"],
        required=False,
    )
    reason = serializers.ChoiceField(
        choices=["LOW_CONFIDENCE", "CITATION_GAP", "POLICY_REVIEW", "USER_ESCALATION"],
        required=False,
    )
    priority = serializers.ChoiceField(
        choices=["low", "normal", "high"],
        required=False,
    )
    search = serializers.CharField(required=False, allow_blank=True, default="")
    page = serializers.IntegerField(required=False, min_value=1, default=1)
    pageSize = serializers.IntegerField(required=False, min_value=1, max_value=100, default=20)


class EditorialQueueMetricsQuerySerializer(serializers.Serializer):
    """Query params for computing editorial board KPI aggregates."""

    windowDays = serializers.IntegerField(required=False, min_value=1, default=30)
    slaHours = serializers.IntegerField(required=False, min_value=1, default=72)


class EditorialQueueTransitionRequestSerializer(serializers.Serializer):
    """Payload for transitioning editorial queue item state with workflow actions."""

    queueItemId = serializers.UUIDField()
    action = serializers.ChoiceField(
        choices=[
            "submit_for_review",
            "request_changes",
            "approve",
            "reject",
            "publish",
            "reopen",
        ]
    )
    comment = serializers.CharField(required=False, allow_blank=True, default="")


class IndexRepositoryRequestSerializer(serializers.Serializer):
    """Payload for triggering a source repository ingestion run."""

    repoUrl = serializers.CharField()
    repoPath = serializers.CharField()
    profile = serializers.CharField(required=False, default="default")
    incremental = serializers.BooleanField(required=False, default=True)
    prune = serializers.BooleanField(required=False, default=False)
    autoAllowRepository = serializers.BooleanField(required=False, default=True)
    includeIssues = serializers.BooleanField(required=False, default=False)


class ErrorResponseSerializer(serializers.Serializer):
    """Reusable error structure mirroring OpenAPI error envelope fields."""

    code = serializers.CharField()
    message = serializers.CharField()
    details = serializers.DictField(required=False)
