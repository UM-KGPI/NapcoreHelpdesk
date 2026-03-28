from django.urls import path

from .views import (
    EditorialQueueMetricsView,
    EditorialQueueView,
    EditorialQueueTransitionView,
    PromotionCandidatesView,
    QuestionAnswerView,
)

urlpatterns = [
    path("questions/answer", QuestionAnswerView.as_view(), name="answer-question"),
    path("faqs/promotion-candidates", PromotionCandidatesView.as_view(), name="promotion-candidates"),
    path("editorial/queue", EditorialQueueView.as_view(), name="editorial-queue"),
    path("editorial/queue/metrics", EditorialQueueMetricsView.as_view(), name="editorial-queue-metrics"),
    path("editorial/queue/transition", EditorialQueueTransitionView.as_view(), name="editorial-queue-transition"),
]
