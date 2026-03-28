from django.contrib import admin
from .models import EditorialQueueItem, IndexedSourceFile, IndexRunMetric, QuestionEvent, SourceChunk


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


@admin.register(EditorialQueueItem)
class EditorialQueueItemAdmin(admin.ModelAdmin):
	list_display = ("queue_item_id", "question_event", "reason", "priority", "status", "created_at")
	search_fields = ("queue_item_id", "question_event__request_id", "question_event__question")
	list_filter = ("reason", "priority", "status")


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
