from __future__ import annotations

from unittest.mock import patch

from django.test import SimpleTestCase, TestCase

from helpdesk.services import concept_presence as presence
from helpdesk.services import concept_vectors as vectors


class TextTests(SimpleTestCase):
    def test_question_subject_drops_the_frame(self):
        self.assertEqual(vectors.question_subject("How can fare distribution be defined in NeTEx?"), "fare distribution")
        self.assertEqual(vectors.question_subject("Is there an element for a ticket machine in NeTEx?"), "ticket machine")

    def test_concept_text_and_readable_names(self):
        self.assertEqual(vectors.concept_text("DISTRIBUTION CHANNEL", ["outlet"], "A type of outlet."), "DISTRIBUTION CHANNEL; outlet. A type of outlet.")
        self.assertEqual(vectors._readable("DISTRIBUTION_CHANNEL"), "distribution channel")
        self.assertEqual(vectors._readable("DistributionChannel"), "distribution channel")


class BuildTests(TestCase):
    CLASSES = [
        {"concept_id": "transmodel:DRIVER", "standard": "transmodel", "label": "DRIVER", "alt_labels": [], "definition": "An EMPLOYEE.", "implemented_by": []},
        {"concept_id": "netex:DriverTrip", "standard": "netex", "label": "driver trip", "alt_labels": [], "definition": "A movement.", "implemented_by": ["netex:DriverTrip"]},
    ]

    def test_only_new_and_changed_classes_are_embedded(self):
        with patch.object(vectors, "ontology_classes", return_value=[dict(c) for c in self.CLASSES]), patch.object(
            vectors, "_embed", side_effect=lambda texts, kind: [[0.1] * vectors.DIMENSION for _ in texts]
        ) as embed:
            self.assertEqual(vectors.build_concept_vectors()["embedded"], 2)
            self.assertEqual(vectors.build_concept_vectors()["embedded"], 0)
            changed = [dict(c) for c in self.CLASSES]
            changed[0]["definition"] = "An EMPLOYEE whose usual work is to drive."
            with patch.object(vectors, "ontology_classes", return_value=changed):
                result = vectors.build_concept_vectors()
        self.assertEqual(result["embedded"], 1)
        self.assertEqual(embed.call_count, 2)

    def test_gone_classes_are_removed(self):
        from helpdesk.models import ConceptVector

        with patch.object(vectors, "ontology_classes", return_value=[dict(c) for c in self.CLASSES]), patch.object(
            vectors, "_embed", side_effect=lambda texts, kind: [[0.1] * vectors.DIMENSION for _ in texts]
        ):
            vectors.build_concept_vectors()
            with patch.object(vectors, "ontology_classes", return_value=[dict(self.CLASSES[0])]):
                self.assertEqual(vectors.build_concept_vectors()["removed"], 1)
        self.assertEqual(list(ConceptVector.objects.values_list("concept_id", flat=True)), ["transmodel:DRIVER"])


class OrderTests(SimpleTestCase):
    def _nearest(self, ids):
        return [{"concept_id": c, "label": c, "similarity": 0.9, "implemented_by": []} for c in ids]

    def test_labels_count_when_the_meaning_agrees_and_existence_puts_the_literal_first(self):
        with patch.object(presence, "_labelled_concepts", return_value=["transmodel:DRIVER"]), patch.object(
            presence, "head_word_concepts", return_value=[]
        ), patch("helpdesk.services.concept_vectors.semantic_concepts", return_value=self._nearest(["transmodel:DUTY", "transmodel:DRIVER_TRIP"])):
            # "How is the work shift of a driver modelled?": DRIVER is named but not near in meaning.
            self.assertEqual(presence.presence_concepts("q", kind="how")[:2], ["transmodel:DUTY", "transmodel:DRIVER_TRIP"])
            # "Does a bus have drivers name described?": an existence question names the thing itself.
            self.assertEqual(presence.presence_concepts("q", kind="whether")[0], "transmodel:DRIVER")

    def test_head_word_concepts_count_when_near_in_meaning(self):
        nearest = self._nearest(["transmodel:FARE_INTERVAL", "transmodel:DISTRIBUTION_CHANNEL"])
        with patch.object(presence, "_labelled_concepts", return_value=[]), patch.object(
            presence, "head_word_concepts", return_value=["transmodel:DISTRIBUTION_ASSIGNMENT", "transmodel:DISTRIBUTION_CHANNEL"]
        ), patch("helpdesk.services.concept_vectors.semantic_concepts", return_value=nearest):
            self.assertEqual(presence.presence_concepts("q", kind="how")[0], "transmodel:DISTRIBUTION_CHANNEL")

    def test_without_the_index_labels_and_head_words_as_before(self):
        with patch.object(presence, "_labelled_concepts", return_value=["transmodel:PARKING"]), patch(
            "helpdesk.services.concept_vectors.semantic_concepts", return_value=[]
        ):
            self.assertEqual(presence.presence_concepts("q"), ["transmodel:PARKING"])


class BatchTests(TestCase):
    def test_batches_are_saved_as_they_are_embedded(self):
        from helpdesk.models import ConceptVector

        classes = [
            {"concept_id": f"transmodel:C{i}", "standard": "transmodel", "label": f"C{i}", "alt_labels": [], "definition": "d", "implemented_by": []}
            for i in range(vectors.EMBED_BATCH + 3)
        ]
        calls = {"n": 0}

        def embed(texts, kind):
            calls["n"] += 1
            if calls["n"] == 2:
                raise OSError("embedder out of memory")
            return [[0.1] * vectors.DIMENSION for _ in texts]

        with patch.object(vectors, "ontology_classes", return_value=[dict(c) for c in classes]), patch.object(vectors, "_embed", side_effect=embed):
            with self.assertRaises(OSError):
                vectors.build_concept_vectors()
            # The first batch was kept; the next run embeds only the rest.
            self.assertEqual(ConceptVector.objects.count(), vectors.EMBED_BATCH)
            self.assertEqual(vectors.build_concept_vectors()["embedded"], 3)
        self.assertEqual(vectors.index_status(), {"conceptVectors": vectors.EMBED_BATCH + 3})
