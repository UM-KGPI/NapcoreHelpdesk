from __future__ import annotations

from unittest.mock import patch

from django.test import SimpleTestCase

import helpdesk.services.semantic_graph as semantic_graph
from helpdesk.services import property_terms
from helpdesk.services.property_terms import PropertyIndex, name_words, text_words, word_pairs

# Shaped like the generated NeTEx ontology (property, class that is its rdfs:domain).
PROPERTIES = [
    ("netex:seatAllocationMethod_PassengerSpotAllocation", "netex:PassengerSpotAllocation"),
    ("netex:seatAllocationMethod_VehicleJourneySpotAllocation", "netex:VehicleJourneySpotAllocation"),
    ("netex:seatAllocationMethod_Reserving", "netex:Reserving"),
    ("netex:seats_WaitingEquipment", "netex:WaitingEquipment"),
    ("tnits:roadFeatureType_RoadFeature", "tnits:RoadFeature"),
] + [(f"netex:startTime_Filler{i}", f"netex:Filler{i}") for i in range(20)]

LABELS = {
    "netex:PassengerSpotAllocation": {"passenger spot allocation"},
    "netex:Vehicle": {"vehicle", "public transport vehicle"},
}


class WordTests(SimpleTestCase):
    def test_text_words_drop_function_words_and_standard_names(self):
        self.assertEqual(text_words("What is NeTEx telling us about seat allocation?"), ["seat", "allocation"])

    def test_text_words_singularise(self):
        self.assertEqual(text_words("seats categories boxes classes"), ["seat", "category", "box", "class"])

    def test_name_words_split_camel_case_and_drop_the_domain_suffix(self):
        self.assertEqual(name_words("netex:seatAllocationMethod_PassengerSpotAllocation"), ["seat", "allocation", "method"])

    def test_word_pairs_are_adjacent_words(self):
        self.assertEqual(word_pairs(["seat", "allocation", "method"]), [("seat", "allocation"), ("allocation", "method")])


class PropertyIndexTests(SimpleTestCase):
    def setUp(self):
        self.index = PropertyIndex.build(PROPERTIES)

    def test_a_property_name_leads_to_the_classes_named_like_it(self):
        self.assertEqual(
            set(self.index.concepts_for([("seat", "allocation")])),
            {"netex:PassengerSpotAllocation", "netex:VehicleJourneySpotAllocation"},
        )

    def test_a_single_word_finds_nothing(self):
        self.assertEqual(self.index.concepts_for([]), [])

    def test_a_pair_owned_by_many_classes_names_no_topic(self):
        self.assertEqual(self.index.concepts_for([("start", "time")]), [])

    def test_owners_without_a_pair_word_in_their_name_are_left_out(self):
        index = PropertyIndex.build([("netex:realTimeOccupancy_Parking", "netex:Parking")])
        self.assertEqual(index.concepts_for([("real", "time")]), [])

    def test_opt_in_sources_only_when_scoped(self):
        self.assertEqual(self.index.concepts_for([("road", "feature")]), [])
        self.assertEqual(self.index.concepts_for([("road", "feature")], scope=["TN-ITS"]), ["tnits:RoadFeature"])

    def test_empty_index_finds_nothing(self):
        self.assertEqual(PropertyIndex().concepts_for([("seat", "allocation")]), [])


class QuestionPropertyConceptsTests(SimpleTestCase):
    def setUp(self):
        index = patch.object(property_terms, "property_index", return_value=PropertyIndex.build(PROPERTIES))
        aliases = patch.object(semantic_graph, "GRAPH_CONCEPT_ALIASES", LABELS)
        index.start()
        aliases.start()
        self.addCleanup(index.stop)
        self.addCleanup(aliases.stop)

    def test_question_653(self):
        concepts = property_terms.question_property_concepts(
            "What is NeTEx telling us about seat allocation in public transport vehicle ?", {"netex:Vehicle"}
        )
        self.assertEqual(concepts, {"netex:PassengerSpotAllocation", "netex:VehicleJourneySpotAllocation"})

    def test_words_of_matched_labels_are_context_not_topic(self):
        self.assertEqual(
            property_terms.question_property_concepts(
                "How is a passenger spot allocation described?", {"netex:PassengerSpotAllocation"}
            ),
            set(),
        )

    def test_words_apart_in_the_question_form_no_pair(self):
        # Function words are dropped before pairing ("number of seats" -> numberOfSeats); a content word is not.
        self.assertEqual(property_terms.question_property_concepts("Which seat gets a manual allocation?", set()), set())


class IndexLoadingTests(SimpleTestCase):
    def test_load_failure_leaves_an_empty_index(self):
        with patch.object(property_terms, "_index", None), patch.object(
            property_terms, "_load_properties", side_effect=OSError("GraphDB down")
        ):
            self.assertEqual(property_terms.property_index().concepts_for([("seat", "allocation")]), [])
