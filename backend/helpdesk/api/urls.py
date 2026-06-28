"""
URL routing for all helpdesk REST API endpoints.

Registered under the single application prefix defined in the project root
URL conf. Ordering matters where paths share a prefix: the more specific
editorial/queue/metrics and editorial/queue/transition patterns must be listed
before editorial/queue to prevent the shorter path shadowing them.

Requirements & design: Andrej Tibaut, Sara Guerra de Oliveira (UM KGPI)
Crafted by: AI coding agents
Created: 2026-03-28  |  Modified: 2026-06-28
"""

from django.urls import path

from .views import (
    DevTokenView,
    EditorialQueueMetricsView,
    EditorialSemanticClustersView,
    EditorialQueueView,
    EditorialQueueTransitionView,
    HealthLiveView,
    HealthReadyView,
    IndexRepositoryView,
    PromotionCandidatesView,
    QuestionAnswerStreamView,
    QuestionAnswerView,
    QuestionEventDetailView,
    QuestionEventsView,
    QuestionFeedbackView,
)

urlpatterns = [
    path("health/live", HealthLiveView.as_view(), name="health-live"),
    path("health/ready", HealthReadyView.as_view(), name="health-ready"),
    path("auth/dev-token", DevTokenView.as_view(), name="auth-dev-token"),
    path("questions/answer", QuestionAnswerView.as_view(), name="answer-question"),
    path("questions/answer/stream", QuestionAnswerStreamView.as_view(), name="answer-question-stream"),
    path("questions/events", QuestionEventsView.as_view(), name="questions-events"),
    path("questions/events/<str:question_event_id>", QuestionEventDetailView.as_view(), name="question-event-detail"),
    path("questions/feedback", QuestionFeedbackView.as_view(), name="answer-feedback"),
    path("faqs/promotion-candidates", PromotionCandidatesView.as_view(), name="promotion-candidates"),
    path("editorial/queue", EditorialQueueView.as_view(), name="editorial-queue"),
    path("editorial/semantic-clusters", EditorialSemanticClustersView.as_view(), name="editorial-semantic-clusters"),
    path("editorial/queue/metrics", EditorialQueueMetricsView.as_view(), name="editorial-queue-metrics"),
    path("editorial/queue/transition", EditorialQueueTransitionView.as_view(), name="editorial-queue-transition"),
    path("admin/index", IndexRepositoryView.as_view(), name="admin-index"),
]
