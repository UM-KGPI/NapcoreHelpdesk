from django.contrib import admin
from .models import (
	AnswerEvidenceLink,
	EditorialQueueItem,
	EditorialQueueTransition,
	FAQEntry,
	FAQVersion,
	IndexedSourceFile,
	IndexRunMetric,
	QuestionEvent,
	RetrievalEvent,
	SourceChunk,
)


@admin.register(QuestionEvent)
class QuestionEventAdmin(admin.ModelAdmin):
	list_display = (
		"id",
		"request_id",
		"mode",
		"confidence",
		"abstained",
		"review_required",
		"created_at",
	)
	search_fields = ("request_id", "question", "session_id", "user_id")
	list_filter = ("mode", "abstained", "review_required", "language")


@admin.register(FAQEntry)
class FAQEntryAdmin(admin.ModelAdmin):
	list_display = ("faq_entry_id", "normalized_intent", "is_active", "updated_at")
	search_fields = ("faq_entry_id", "normalized_intent")
	list_filter = ("is_active",)


@admin.register(FAQVersion)
class FAQVersionAdmin(admin.ModelAdmin):
	list_display = ("faq_entry", "version", "confidence", "review_required", "is_published", "created_at")
	search_fields = ("faq_entry__faq_entry_id", "answer")
	list_filter = ("is_published", "review_required")


@admin.register(EditorialQueueItem)
class EditorialQueueItemAdmin(admin.ModelAdmin):
	list_display = ("queue_item_id", "question_event", "reason", "priority", "status", "created_at")
	search_fields = ("queue_item_id", "question_event__request_id", "question_event__question")
	list_filter = ("reason", "priority", "status")


@admin.register(EditorialQueueTransition)
class EditorialQueueTransitionAdmin(admin.ModelAdmin):
	list_display = (
		"queue_item",
		"action",
		"from_status",
		"to_status",
		"actor_id",
		"created_at",
	)
	search_fields = ("queue_item__queue_item_id", "actor_id", "comment")
	list_filter = ("action", "from_status", "to_status")


@admin.register(RetrievalEvent)
class RetrievalEventAdmin(admin.ModelAdmin):
	list_display = ("retrieval_event_id", "question_event", "repository_url", "source_path", "score", "created_at")
	search_fields = ("retrieval_event_id", "repository_url", "source_path", "chunk_id")
	list_filter = ("repository_url",)


@admin.register(AnswerEvidenceLink)
class AnswerEvidenceLinkAdmin(admin.ModelAdmin):
	list_display = ("evidence_link_id", "answer_id", "question_event", "repository_url", "source_path", "created_at")
	search_fields = ("evidence_link_id", "answer_id", "repository_url", "source_path", "chunk_id")
	list_filter = ("repository_url",)


@admin.register(SourceChunk)
class SourceChunkAdmin(admin.ModelAdmin):
	list_display = ("chunk_id", "repository_url", "source_path", "quality_score", "updated_at")
	search_fields = ("chunk_id", "repository_url", "source_path", "text")
	list_filter = ("repository_url",)


@admin.register(IndexedSourceFile)
class IndexedSourceFileAdmin(admin.ModelAdmin):
	list_display = ("repository_url", "source_path", "commit_sha", "updated_at")
	search_fields = ("repository_url", "source_path", "commit_sha", "content_hash")


@admin.register(IndexRunMetric)
class IndexRunMetricAdmin(admin.ModelAdmin):
	list_display = (
		"repository_url",
		"profile",
		"mode",
		"status",
		"scanned_files",
		"created_chunks",
		"updated_chunks",
		"deleted_chunks",
		"duration_ms",
		"created_at",
	)
	search_fields = ("repository_url", "repository_path", "profile", "error_message")
	list_filter = ("status", "mode", "profile")
