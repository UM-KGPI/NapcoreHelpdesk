from django.urls import path

from .views import (
    DevTokenView,
    EditorialQueueMetricsView,
    EditorialQueueView,
    EditorialQueueTransitionView,
    HealthLiveView,
    HealthReadyView,
    IndexRepositoryView,
    PromotionCandidatesView,
    QuestionAnswerView,
)

urlpatterns = [
    path("health/live", HealthLiveView.as_view(), name="health-live"),
    path("health/ready", HealthReadyView.as_view(), name="health-ready"),
    path("auth/dev-token", DevTokenView.as_view(), name="auth-dev-token"),
    path("questions/answer", QuestionAnswerView.as_view(), name="answer-question"),
    path("faqs/promotion-candidates", PromotionCandidatesView.as_view(), name="promotion-candidates"),
    path("editorial/queue", EditorialQueueView.as_view(), name="editorial-queue"),
    path("editorial/queue/metrics", EditorialQueueMetricsView.as_view(), name="editorial-queue-metrics"),
    path("editorial/queue/transition", EditorialQueueTransitionView.as_view(), name="editorial-queue-transition"),
    path("admin/index", IndexRepositoryView.as_view(), name="admin-index"),
]
