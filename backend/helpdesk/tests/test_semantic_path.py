"""A semantic path as evidence of its own (services/semantic_path.py): the search, the block, where it goes in the
evidence, and that the checks on a cited sentence read it for the right reasons. No database, no network, no model."""

from __future__ import annotations

import io
import json
from unittest import mock

from django.test import SimpleTestCase, override_settings

from helpdesk.api import views
from helpdesk.services import semantic_graph as sg
from helpdesk.services import semantic_path as sp
from helpdesk.services.llm_generator import (
    _build_messages,
    _sentence_grounding_error,
    _sentence_purpose_error,
)

SR, TE, ACC = "x:Situation.SituationRecord", "x:Situation.TrafficElement", "x:Situation.Accident"
LR, LOC, NET = "x:Loc.LocationReference", "x:Loc.Location", "x:Loc.NetworkLocation"
SPD, CAR, LANE = "x:Loc.SupplementaryPositionalDescription", "x:Loc.Carriageway", "x:Loc.Lane"
IMP, VEH, ROAD = "x:Situation.Impact", "x:Common.Vehicle", "x:Common.Road"
DEFS = {
    TE: "An event not planned by the operator.",
    SR: "One record within a situation.",
    LR: "Represents one or more separate locations.",
    LOC: "The specification of a location.",
    NET: "A location on a network.",
    SPD: "More precise positional information.",
    CAR: "Details carriageway and lane locations.",
    ACC: "Collisions between vehicles.",
    LANE: "A specific lane.",
}


def _data(extra_out=(), extra_up=()) -> dict:
    up = [(ACC, TE), (TE, SR), (LOC, LR), (NET, LOC), *extra_up]
    supers, subs = {}, {}
    for sub, sup in up:
        supers.setdefault(sub, []).append(sup)
        subs.setdefault(sup, []).append(sub)
    out = {}
    for domain, target, name in [
        (SR, LR, "LocationReference"), (SR, IMP, "impact"), (NET, SPD, "SupplementaryPositionalDescription"),
        (SPD, CAR, "Carriageway"), (CAR, LANE, "Lane"), (VEH, ROAD, "Road"), *extra_out,
    ]:
        out.setdefault(domain, []).append((target, name))
    return {"supers": supers, "subs": subs, "out": out, "definitions": dict(DEFS)}


def _path_chunk() -> dict:
    found = sp.find_paths([ACC, LANE], _data())
    return sp.build_block(found[0], ["Collisions between vehicles. A specific lane."], _data())


def _passages(n: int = 6) -> list[dict]:
    return [{"chunkId": f"p{i}", "text": f"passage {i}", "sourcePath": f"f{i}", "repositoryUrl": "https://example.org/r/blob/main/f", "commitSha": "c", "docType": "datex"} for i in range(1, n + 1)]


class SearchTests(SimpleTestCase):
    def test_the_chain_goes_up_along_a_relation_and_down(self):
        (found,) = sp.find_paths([ACC, LANE], _data())
        self.assertEqual((found["source"], found["target"], found["steps"]), (ACC, LANE, 8))
        self.assertEqual(
            [(kind, node) for kind, _name, node in found["path"]],
            [("up", TE), ("up", SR), ("has", LR), ("down", LOC), ("down", NET), ("has", SPD), ("has", CAR), ("has", LANE)],
        )

    def test_no_step_goes_against_a_relations_direction(self):
        # Lane has no way back: the relations point at it only.
        self.assertEqual(sp.find_paths([LANE, VEH], _data()), [])
        reached = sp.search_from(LANE, _data())
        self.assertEqual(reached, {})

    def test_the_search_does_not_use_the_undirected_shortcut_through_other_classes(self):
        # Impact has Road and Vehicle; Vehicle has Road. Ignoring direction, Road would link Vehicle to Impact and
        # Accident; here Vehicle is reached only as Impact's range, and Road from Vehicle never leads back.
        data = _data(extra_out=[(IMP, ROAD, "Road"), (IMP, VEH, "Vehicle")])
        path = sp.search_from(ACC, data)[VEH][2]
        self.assertEqual([(kind, node) for kind, _name, node in path], [("up", TE), ("up", SR), ("has", IMP), ("has", VEH)])
        self.assertNotIn(ACC, sp.search_from(VEH, data))
        self.assertNotIn(IMP, sp.search_from(VEH, data))

    def test_no_step_down_after_up_or_up_after_down(self):
        data = _data(extra_up=[("x:Situation.Roadworks", TE)])
        # Accident up to TrafficElement, down to Roadworks would be a sibling.
        self.assertNotIn("x:Situation.Roadworks", sp.search_from(ACC, data))
        # Down to Location, up again would only return.
        self.assertNotIn(LR, sp.search_from(LR, data))

    def test_a_relation_leads_to_subtypes_and_supertypes_continue(self):
        reached = sp.search_from(SR, _data())
        self.assertIn(NET, reached)  # has LocationReference, down, down
        self.assertEqual(reached[NET][0], 3)

    def test_both_orders_of_a_pair_are_tried(self):
        found = sp.find_paths([LANE, ACC], _data())  # given in the other order
        self.assertEqual((found[0]["source"], found[0]["target"]), (ACC, LANE))

    def test_longest_path_is_bounded(self):
        self.assertEqual(sp.find_paths([ACC, LANE], _data()) != [], True)
        with mock.patch.object(sp, "MAX_STEPS", 7):
            self.assertEqual(sp.find_paths([ACC, LANE], _data()), [])

    def test_a_tie_goes_to_the_path_with_fewer_inheritance_steps_then_to_the_smaller_path(self):
        a, b, c, d = "x:N.A", "x:N.B", "x:N.C", "x:N.D"
        # A has B, B has D (2 steps); A has C, C has D (2 steps): the relation names break the tie ("b" before "c").
        data = {"supers": {}, "subs": {}, "definitions": {}, "out": {a: [(b, "viaB"), (c, "viaC")], b: [(d, "x")], c: [(d, "x")]}}
        (found,) = sp.find_paths([a, d], data)
        self.assertEqual([m[2] for m in found["path"]], [b, d])
        # Another route of the same length through one inheritance step loses to the one with relations only.
        data["supers"] = {a: ["x:N.P"]}
        data["out"]["x:N.P"] = [(d, "direct")]
        (found,) = sp.find_paths([a, d], data)
        self.assertEqual(found["steps"], 2)
        self.assertEqual([m[0] for m in found["path"]], ["has", "has"])

    def test_fewer_than_two_countable_classes_give_no_path(self):
        self.assertEqual(sp.find_paths([ACC], _data()), [])
        self.assertEqual(sp.find_paths([ACC, "x:Situation.impact"], _data()), [])  # a property is not a class
        self.assertEqual(sp.find_paths([ACC, "y:Situation.Other"], _data()), [])  # another ontology
        self.assertEqual(sp.find_paths([], _data()), [])

    def test_a_class_inside_the_path_between_two_others_is_covered_by_it(self):
        found = sp.find_paths([ACC, LOC, LANE], _data())
        self.assertEqual([(f["source"], f["target"]) for f in found], [(ACC, LANE)])

    def test_unconnected_pairs_each_get_their_own_path_up_to_the_cap(self):
        data = _data(extra_out=[(IMP, ROAD, "Road")])
        found = sp.find_paths([ACC, LANE, IMP, ROAD, VEH], data)
        self.assertLessEqual(len(found), sp.MAX_PATH_BLOCKS)
        self.assertEqual(found, sorted(found, key=lambda f: (f["steps"], f["source"], f["target"])))

    def test_no_data_no_path(self):
        self.assertEqual(sp.find_paths([ACC, LANE], {"supers": {}, "subs": {}, "out": {}, "definitions": {}}), [])


class BlockTests(SimpleTestCase):
    def test_one_line_per_step_in_plain_sentences_and_a_heading_naming_both_ends(self):
        block = _path_chunk()
        lines = block["text"].split("\n")
        self.assertEqual(lines[0], "Semantic path in the x ontology: Accident to Lane")
        self.assertEqual(
            lines[1:9],
            [
                "Accident is a TrafficElement.", "TrafficElement is a SituationRecord.", "SituationRecord has LocationReference.",
                "LocationReference can be a Location.", "Location can be a NetworkLocation.",
                "NetworkLocation has SupplementaryPositionalDescription.", "SupplementaryPositionalDescription has Carriageway.",
                "Carriageway has Lane.",
            ],
        )

    def test_a_relation_named_otherwise_than_its_range_shows_its_name(self):
        data = _data(extra_out=[(SR, ROAD, "affectedRoad")])
        found = sp.find_paths([ACC, ROAD], data)[0]
        self.assertIn("SituationRecord has Road (relation `affectedRoad`).", sp.build_block(found, [], data)["text"])
        self.assertIn("SituationRecord has LocationReference.", sp.build_block(sp.find_paths([ACC, LANE], data)[0], [], data)["text"])

    def test_a_relation_written_name_first_shows_its_name_not_its_classes(self):
        # The shape of the Transmodel relations: name, then domain, then range when needed ("in.STOP_PLACE.QUAY").
        data = _data(extra_out=[(SR, ROAD, "affected.SituationRecord.Road")])
        found = sp.find_paths([ACC, ROAD], data)[0]
        self.assertIn("SituationRecord has Road (relation `affected`).", sp.build_block(found, [], data)["text"])
        self.assertEqual(sg.local_own_name("in.STOP_PLACE.QUAY"), "in")
        self.assertEqual(sg.local_own_name("hasSITEFRAME.STOP_PLACE"), "hasSITEFRAME")
        self.assertEqual(sg.local_own_name("Situation.Accident.impact"), "impact")
        self.assertEqual(sg.local_own_name("Common.Vehicle"), "Vehicle")
        self.assertEqual(sg.local_own_name("validation"), "validation")

    def test_definitions_only_of_classes_not_already_in_a_served_passage(self):
        block = _path_chunk()  # Accident's and Lane's definitions are in the passage given to build_block
        self.assertIn("Definitions of classes on the path:", block["text"])
        self.assertIn("TrafficElement: An event not planned by the operator.", block["text"])
        self.assertNotIn("Accident: Collisions", block["text"])
        self.assertNotIn("Lane: A specific lane.", block["text"])
        self.assertEqual(sorted(block["semanticPathDefined"]), sorted(["TrafficElement", "SituationRecord", "LocationReference", "Location", "NetworkLocation", "SupplementaryPositionalDescription", "Carriageway"]))

    def test_definitions_are_all_or_none_within_the_cap(self):
        found = sp.find_paths([ACC, LANE], _data())[0]
        with mock.patch.object(sp, "MAX_BLOCK_CHARS", 300):
            block = sp.build_block(found, [], _data())
        self.assertNotIn("Definitions", block["text"])
        self.assertEqual(block["semanticPathDefined"], [])
        self.assertIn("Carriageway has Lane.", block["text"])

    def test_every_line_of_the_steps_is_a_plain_sentence_of_one_of_three_shapes(self):
        for line in _path_chunk()["text"].split("\n")[1:9]:
            self.assertRegex(line, r"^\w+ (is an? |can be an? |has )\w+\.$")

    def test_the_block_is_a_citable_chunk(self):
        block = _path_chunk()
        self.assertEqual(block["docType"], "ontology-path")
        self.assertTrue(block["semanticPath"])
        self.assertEqual(block["sourcePath"], "docs/ontology/standards/x.ttl#path=Situation.Accident=Loc.Lane")
        self.assertTrue(block["repositoryUrl"].endswith("/docs/ontology/standards/x.ttl"))
        self.assertEqual(sp.citation_title(block["sourcePath"]), "x ontology: path Accident to Lane")
        self.assertEqual(views._citation_title(block["sourcePath"]), {"title": "x ontology: path Accident to Lane"})
        self.assertEqual(views._citation_url(block), block["repositoryUrl"])

    def test_two_classes_of_one_name_are_told_apart_by_their_local_names(self):
        data = _data(extra_out=[(ROAD, "x:Other.Vehicle", "Vehicle")])
        data["definitions"] = {}
        found = sp.find_paths([VEH, "x:Other.Vehicle"], data)[0]
        text = sp.build_block(found, [], data)["text"]
        self.assertIn("Common.Vehicle has Road.", text)
        self.assertIn("Road has Other.Vehicle.", text)


@override_settings(LLM_MAX_EVIDENCE_CHUNKS=6)
class EvidenceListTests(SimpleTestCase):
    def test_the_prompt_shows_the_blocks_after_the_passages(self):
        block = _path_chunk()
        window = sp.prompt_window(_passages(8) + [block], 6)
        self.assertEqual([c["chunkId"] for c in window[:6]], [f"p{i}" for i in range(1, 7)])
        self.assertIs(window[6], block)
        self.assertEqual(len(window), 7)
        self.assertEqual(sp.prompt_window(window, 6), window)  # idempotent

    def test_carry_keeps_the_blocks_of_the_list_it_replaces(self):
        block = _path_chunk()
        merged = sp.carry(_passages(6) + [block], _passages(5))
        self.assertEqual(len(merged), 6)
        self.assertIs(merged[-1], block)
        self.assertEqual(sp.carry(merged, merged), merged)

    def test_the_prompt_numbers_the_block_after_the_sixth_and_does_not_cut_it(self):
        data = _data()
        data["definitions"][CAR] = "Details carriageway and lane locations. " + "Several instances may exist. " * 12
        block = sp.build_block(sp.find_paths([ACC, LANE], data)[0], [], data)
        self.assertGreater(len(block["text"]), 1200)
        messages = _build_messages(question="How is an accident linked to a lane?", chunks=_passages(6) + [block], max_chunks=6, max_chars_per_chunk=1200)
        prompt = "\n".join(m["content"] for m in messages)
        self.assertIn("[E7] chunk=" + block["chunkId"], prompt)
        self.assertIn("Carriageway has Lane.", prompt)
        self.assertIn("[E6] chunk=p6", prompt)
        self.assertIn("Several instances may exist. " * 12, prompt)

    def test_the_citation_of_an_answer_that_reads_the_block_names_it(self):
        block = _path_chunk()
        citations = views._citations_from_prompt_order(_passages(6) + [block], "The chain is Accident, SituationRecord, Lane [E7].")
        self.assertEqual(citations[6]["label"], "E7")
        self.assertEqual(citations[6]["chunkId"], block["chunkId"])
        self.assertEqual(len(citations), 7)
        self.assertEqual(citations[6]["title"], "x ontology: path Accident to Lane")

    def test_the_list_of_the_other_citation_path_does_not_pick_a_block(self):
        block = _path_chunk()
        chosen = views._select_citations(_passages(6) + [block], max_citations=10)
        self.assertNotIn(block["chunkId"], [c["chunkId"] for c in chosen])

    @override_settings(RETRIEVAL_SEMANTIC_PATH_ENABLED=False)
    def test_off_by_default(self):
        self.assertFalse(sp.enabled())
        self.assertFalse(getattr(__import__("django.conf", fromlist=["settings"]).settings, "RETRIEVAL_SEMANTIC_PATH_ENABLED"))

    @override_settings(RETRIEVAL_SEMANTIC_PATH_ENABLED=True)
    def test_on_when_set(self):
        self.assertTrue(sp.enabled())


class OntologyListTests(SimpleTestCase):
    """RETRIEVAL_SEMANTIC_PATH_ONTOLOGIES: which ontologies get path blocks."""

    def _two_ontologies(self):
        data = _data()
        y_a, y_b, y_c = "y:Thing.Alpha", "y:Thing.Beta", "y:Thing.Gamma"
        data["supers"][y_a] = [y_b]
        data["subs"][y_b] = [y_a]
        data["out"][y_b] = [(y_c, "Gamma")]
        return data, [ACC, LANE, y_a, y_c]

    def test_empty_means_every_ontology(self):
        data, concepts = self._two_ontologies()
        with override_settings(RETRIEVAL_SEMANTIC_PATH_ONTOLOGIES=""):
            blocks = sp.path_blocks(concepts, [], data)
        self.assertEqual(sorted(b["sourcePath"].split("#")[0].rsplit("/", 1)[1] for b in blocks), ["x.ttl", "y.ttl"])

    def test_the_list_keeps_only_the_listed_ontologies_case_and_spaces_ignored(self):
        data, concepts = self._two_ontologies()
        with override_settings(RETRIEVAL_SEMANTIC_PATH_ONTOLOGIES=" X , z"):
            blocks = sp.path_blocks(concepts, [], data)
        self.assertEqual([b["sourcePath"].split("#")[0].rsplit("/", 1)[1] for b in blocks], ["x.ttl"])
        with override_settings(RETRIEVAL_SEMANTIC_PATH_ONTOLOGIES="z"):
            self.assertEqual(sp.path_blocks(concepts, [], data), [])

    def test_the_search_is_unchanged_for_the_listed_ontology(self):
        data, concepts = self._two_ontologies()
        with override_settings(RETRIEVAL_SEMANTIC_PATH_ONTOLOGIES="x"):
            listed = sp.path_blocks(concepts, [], data)
        with override_settings(RETRIEVAL_SEMANTIC_PATH_ONTOLOGIES=""):
            every = [b for b in sp.path_blocks(concepts, [], data) if b["sourcePath"].startswith("docs/ontology/standards/x.ttl")]
        self.assertEqual([b["text"] for b in listed], [b["text"] for b in every])


class EndInsideLongerTermTests(SimpleTestCase):
    """A class matched only inside a longer matched term is no end of a path (no database)."""

    ALIASES = {
        "netex:Journey": {"journey"},
        "netex:Vehicle": {"vehicle"},
        "netex:VehicleJourney": {"vehicle journey"},
        "netex:Line": {"line"},
        "netex:Network": {"network"},
        "netex:LineNetwork": {"line network"},
    }

    def _ends(self, question, concepts):
        with mock.patch.object(sg, "GRAPH_CONCEPT_ALIASES", self.ALIASES):
            return sp.without_inside_longer_terms(question, concepts, concepts)

    def test_the_words_of_a_longer_term_are_no_ends_the_term_stays(self):
        found = self._ends("What is a vehicle journey?", {"netex:Vehicle", "netex:Journey", "netex:VehicleJourney"})
        self.assertEqual(found, {"netex:VehicleJourney"})

    def test_a_word_that_stands_alone_stays(self):
        found = self._ends("Is a line part of a vehicle journey?", {"netex:Line", "netex:Journey", "netex:VehicleJourney"})
        self.assertEqual(found, {"netex:Line", "netex:VehicleJourney"})

    def test_the_longer_term_may_belong_to_a_concept_that_is_not_a_candidate(self):
        with mock.patch.object(sg, "GRAPH_CONCEPT_ALIASES", self.ALIASES):
            found = sp.without_inside_longer_terms(
                "A vehicle journey", {"netex:Journey"}, {"netex:Journey", "netex:VehicleJourney"}
            )
        self.assertEqual(found, set())

    def test_a_word_in_a_hyphenated_word_is_not_inside_a_longer_term(self):
        # "multi-line" is read as the words "multi line": no concept's term contains them, so "line" stays an end
        found = self._ends("What is a multi-line network?", {"netex:Line", "netex:Network"})
        self.assertEqual(found, {"netex:Line", "netex:Network"})


@override_settings(RETRIEVAL_SEMANTIC_PATH_ONTOLOGIES="")
class EndCompoundAndPhraseTests(SimpleTestCase):
    """Rules H (a class named only by a part of a hyphenated compound is no end) and P (two ends the question names as one
    phrase make no pair), by the matcher's own records. No database, no network, no model; no word of a real question in code."""

    ALIASES = {
        "x:Alpha": {"alpha"},
        "x:Beta": {"beta"},
        "x:Gamma": {"gamma"},
        "x:AlphaBeta": {"alpha beta"},
        "x:Delta": {"delta"},
        "x:Real": {"real time"},
        "y:Alpha": {"alpha"},
    }

    def _with(self, function, *args):
        with mock.patch.object(sg, "GRAPH_CONCEPT_ALIASES", self.ALIASES):
            return function(*args)

    def _compounds(self, question, concepts):
        return self._with(sp.inside_compounds, question, concepts)

    def _pairs(self, question, concepts):
        return self._with(sp.phrase_pairs, question, concepts)

    def test_a_class_named_only_inside_a_hyphenated_word_is_no_end(self):
        self.assertEqual(self._compounds("A multi-alpha beta", {"x:Alpha", "x:Beta"}), {"x:Alpha"})

    def test_a_class_named_also_as_a_word_of_its_own_stays(self):
        self.assertEqual(self._compounds("A multi-alpha and an alpha", {"x:Alpha"}), set())

    def test_hyphens_of_any_length_and_the_unicode_hyphen_join_words(self):
        self.assertEqual(self._compounds("A multi--alpha", {"x:Alpha"}), {"x:Alpha"})
        self.assertEqual(self._compounds("A multi\u2010alpha", {"x:Alpha"}), {"x:Alpha"})

    def test_a_space_or_a_dash_with_spaces_does_not_make_a_compound(self):
        self.assertEqual(self._compounds("A multi alpha", {"x:Alpha"}), set())
        self.assertEqual(self._compounds("A multi - alpha", {"x:Alpha"}), set())

    def test_a_name_that_is_the_whole_compound_stays(self):
        self.assertEqual(self._compounds("The real-time view", {"x:Real"}), set())

    def test_a_name_that_is_a_part_of_a_longer_compound_goes(self):
        self.assertEqual(self._compounds("A real-time-ish view", {"x:Real"}), {"x:Real"})

    def test_the_ends_are_the_longer_term_rule_and_then_the_compound_rule(self):
        concepts = {"x:Alpha", "x:Beta", "x:AlphaBeta"}
        with mock.patch.object(sg, "GRAPH_CONCEPT_ALIASES", self.ALIASES):
            self.assertEqual(sp.path_end_concepts("An alpha beta", concepts, concepts), {"x:AlphaBeta"})
            self.assertEqual(sp.path_end_concepts("A multi-gamma and a beta", {"x:Gamma", "x:Beta"}, {"x:Gamma", "x:Beta"}), {"x:Beta"})

    def test_two_words_next_to_each_other_are_one_phrase(self):
        self.assertEqual(self._pairs("A gamma delta here", {"x:Gamma", "x:Delta"}), [["x:Delta", "x:Gamma"]])

    def test_a_hyphen_or_spaces_between_keep_the_phrase_a_word_or_a_mark_between_breaks_it(self):
        both = {"x:Gamma", "x:Delta"}
        self.assertEqual(self._pairs("A gamma-delta", both), [["x:Delta", "x:Gamma"]])
        self.assertEqual(self._pairs("A gamma   delta", both), [["x:Delta", "x:Gamma"]])
        self.assertEqual(self._pairs("A gamma, delta", both), [])
        self.assertEqual(self._pairs("A gamma of delta", both), [])  # a stop word between: named separately
        self.assertEqual(self._pairs("A gamma (delta)", both), [])

    def test_the_order_in_the_question_does_not_matter(self):
        self.assertEqual(self._pairs("A delta gamma", {"x:Gamma", "x:Delta"}), [["x:Delta", "x:Gamma"]])

    def test_a_multi_word_name_is_one_occurrence_whose_edge_counts(self):
        self.assertEqual(self._pairs("The real time delta", {"x:Real", "x:Delta"}), [["x:Delta", "x:Real"]])
        self.assertEqual(self._pairs("The real time of a delta", {"x:Real", "x:Delta"}), [])

    def test_occurrences_that_share_a_word_are_not_next_to_each_other(self):
        # "alpha" is both a class of its own and a word of the class "alpha beta": one phrase read two ways, the pair stays
        concepts = {"x:Alpha", "x:AlphaBeta"}
        self.assertEqual(self._pairs("An alpha beta", concepts), [])

    def test_the_same_word_matched_twice_one_adjacent_place_is_enough(self):
        both = {"x:Gamma", "x:Delta"}
        self.assertEqual(self._pairs("A gamma delta, and again a gamma", both), [["x:Delta", "x:Gamma"]])
        self.assertEqual(self._pairs("A gamma in the delta", both), [])

    def test_only_pairs_of_one_ontology_are_looked_at(self):
        self.assertEqual(self._pairs("An alpha delta", {"x:Delta", "y:Alpha"}), [])

    def test_a_dropped_pair_is_not_searched_and_covers_nothing(self):
        data = _data()
        self.assertNotEqual(sp.find_paths([ACC, LANE], data), [])
        self.assertEqual(sp.find_paths([ACC, LANE], data, dropped=[frozenset((LANE, ACC))]), [])
        # the pair Accident-Lane covers Location, so with all three given only that block stays; with the pair dropped
        # the pairs that end in Location are searched
        self.assertEqual(len(sp.find_paths([ACC, LOC, LANE], data)), 1)
        found = sp.find_paths([ACC, LOC, LANE], data, dropped=[frozenset((ACC, LANE))])
        self.assertEqual({frozenset((f["source"], f["target"])) for f in found}, {frozenset((ACC, LOC)), frozenset((LOC, LANE))})

    def test_the_blocks_follow_the_dropped_pairs(self):
        self.assertEqual(sp.path_blocks([ACC, LANE], [], _data(), dropped=[frozenset((ACC, LANE))]), [])
        self.assertEqual(len(sp.path_blocks([ACC, LANE], [], _data())), 1)

    def test_with_two_texts_a_pair_goes_only_when_it_goes_in_every_text_that_has_both_ends(self):
        a, b, c = "x:A", "x:B", "x:C"
        # as asked and in English: the pair is a phrase in both
        self.assertEqual(sp.dropped_pairs([({a, b}, [[a, b]]), ({a, b}, [[a, b]])]), {frozenset((a, b))})
        # a phrase in one text, named separately in the other: it stays
        self.assertEqual(sp.dropped_pairs([({a, b}, [[a, b]]), ({a, b}, [])]), set())
        # only one text has both ends: that text decides
        self.assertEqual(sp.dropped_pairs([({a}, []), ({a, b}, [[a, b]])]), {frozenset((a, b))})
        # the ends found in different texts: never dropped
        self.assertEqual(sp.dropped_pairs([({a, c}, [[a, c]]), ({b}, [])]), {frozenset((a, c))})
        self.assertEqual(sp.dropped_pairs([]), set())

    def test_with_nothing_dropped_the_search_is_unchanged(self):
        data = _data()
        self.assertEqual(sp.find_paths([ACC, LANE], data, dropped=()), sp.find_paths([ACC, LANE], data))


class PolicyForPathBlocksTests(SimpleTestCase):
    """An answer that cites a path block must pass the policy step of the view (production, 23 November 2026: the
    block of DATEX II cited datex.ttl, which no list of accepted ontology files held, and the answer was refused)."""

    def _citations(self, data, concepts):
        found = sp.find_paths(concepts, data)
        block = sp.build_block(found[0], [], data)
        # as the view's citation list carries it: the repository link and the source path of the block
        return [{"repositoryUrl": block["repositoryUrl"], "sourcePath": block["sourcePath"], "label": "E7"}]

    def test_an_answer_citing_a_path_block_is_not_blocked_for_every_ontology_that_has_a_block(self):
        from helpdesk.services.policy_guard import evaluate_policy

        for prefix in ("datex", "netex", "siri", "opra", "transmodel", "tnits", "mdcat"):
            a, b, c = f"{prefix}:G.Alpha", f"{prefix}:G.Beta", f"{prefix}:G.Gamma"
            data = {"supers": {a: [b]}, "subs": {b: [a]}, "out": {b: [(c, "Gamma")]}, "definitions": {}}
            citations = self._citations(data, [a, c])
            with mock.patch.object(sg, "DIRECTED_RELATIONS", data):
                result = evaluate_policy("Alpha is a Beta [E7].", citations)
            self.assertTrue(result["allowed"], (prefix, result))

    def test_a_file_of_an_ontology_the_app_has_not_loaded_is_still_blocked(self):
        from helpdesk.services.policy_guard import evaluate_policy

        data = _data()
        citations = [{"repositoryUrl": f"{sp.STANDARD_ONTOLOGIES_URL}/other.ttl"}]
        with mock.patch.object(sg, "DIRECTED_RELATIONS", data):
            self.assertEqual(evaluate_policy("Text [E1].", citations)["reason"], "POLICY_BLOCK")

    def test_an_unknown_repository_is_still_blocked_with_a_path_block_beside_it(self):
        from helpdesk.services.policy_guard import evaluate_policy

        data = _data()
        citations = self._citations(data, [ACC, LANE]) + [{"repositoryUrl": "https://github.com/someone/else/blob/main/f.xml"}]
        with mock.patch.object(sg, "DIRECTED_RELATIONS", data):
            self.assertEqual(evaluate_policy("Text [E1][E2].", citations)["reason"], "POLICY_BLOCK")

    def test_the_url_test_reads_the_file_only(self):
        data = _data()
        ok = f"{sp.STANDARD_ONTOLOGIES_URL}/x.ttl"
        self.assertTrue(sp.is_path_ontology_url(ok + "#path=A=B", data))
        for bad in (f"{sp.STANDARD_ONTOLOGIES_URL}/x/y.ttl", f"{sp.STANDARD_ONTOLOGIES_URL}/x.xml", "https://example.org/x.ttl", ""):
            self.assertFalse(sp.is_path_ontology_url(bad, data), bad)


class SentenceCheckTests(SimpleTestCase):
    def setUp(self):
        self.block = _path_chunk()
        self.chunks = _passages(6) + [self.block]

    def _error(self, sentence):
        return _sentence_grounding_error(sentence, self.chunks)

    def test_a_sentence_that_states_a_step_of_the_block_passes(self):
        for sentence in (
            "SituationRecord has LocationReference [E7].",
            "`Accident` is a `TrafficElement` [E7].",
            "LocationReference can be a Location [E7].",
            "Carriageway has Lane [E7].",
            "Accident is a SituationRecord [E7].",  # two up steps
            "Accident has LocationReference [E7].",  # inherited from SituationRecord: up steps, then the relation
            "SituationRecord has Location [E7].",  # a subtype of what the relation leads to
            "SituationRecord has a LocationReference, which can be a Location and then a NetworkLocation [E7].",
        ):
            self.assertIsNone(self._error(sentence), sentence)

    def test_a_sentence_that_claims_a_step_the_block_does_not_hold_fails(self):
        for sentence in (
            "LocationReference has SituationRecord [E7].",  # against the relation's direction
            "Lane has Carriageway [E7].",
            "Accident has Lane [E7].",  # the path links them through five classes, not directly
            "SituationRecord is a LocationReference [E7].",
            "Accident can be a Location [E7].",
            "Location is a NetworkLocation [E7].",  # a subtype, not a supertype
        ):
            error = self._error(sentence)
            self.assertIsNotNone(error, sentence)
            self.assertIn("a step the cited block does not hold", error)

    def test_has_the_supertype_and_has_the_subtype_are_read_as_up_and_down_claims(self):
        for sentence in (
            "Accident has the supertype TrafficElement [E7].",
            "Accident has the supertype SituationRecord [E7].",  # two up steps
            "Accident has a supertype SituationRecord [E7].",
            "Accident has the direct supertype TrafficElement [E7].",
            "LocationReference has the subtype Location [E7].",
            "LocationReference has the subtypes Location and NetworkLocation [E7].",
            "Location has the subtype NetworkLocation [E7].",
            "Location has the subtype NetworkLocation and has a SupplementaryPositionalDescription [E7].",
            "`Accident` has the supertype `TrafficElement` [E7].",
        ):
            self.assertIsNone(self._error(sentence), sentence)
        for sentence in (
            "TrafficElement has the supertype Accident [E7].",
            "SituationRecord has the supertype Accident [E7].",
            "Accident has the subtype SituationRecord [E7].",
            "Location has the subtype LocationReference [E7].",
            "NetworkLocation has the subtype Location [E7].",
            "Location has the supertype NetworkLocation [E7].",
            "Accident has the supertype Lane [E7].",  # the path links them, but not upwards
        ):
            error = self._error(sentence)
            self.assertIsNotNone(error, sentence)
            self.assertIn("a step the cited block does not hold", error)
        # a has claim in the other shapes is read as before
        self.assertIsNotNone(self._error("Lane has Carriageway [E7]."))
        self.assertIsNotNone(self._error("Accident has a subtle Lane [E7]."))

    def test_has_as_its_supertype_is_judged_by_direction_when_the_block_links_the_two(self):
        for sentence in (
            "Accident has TrafficElement as its supertype [E7].",
            "Accident has SituationRecord as its supertype [E7].",  # two up steps
            "Accident has TrafficElement as a direct supertype [E7].",
            "Location has NetworkLocation as its subtype [E7].",
            "LocationReference has Location as one of its subtypes [E7].",
            "`Accident` has `TrafficElement` as its supertype [E7].",
            "Accident has TrafficElement as its supertype and has a LocationReference [E7].",
        ):
            self.assertIsNone(self._error(sentence), sentence)
        for sentence in (
            "TrafficElement has Accident as its supertype [E7].",
            "Location has NetworkLocation as its supertype [E7].",
            "NetworkLocation has Location as its subtype [E7].",
            "Accident has Lane as its supertype [E7].",  # linked by the path, but not by a supertype step
            "Accident has TrafficElement [E7].",  # no role stated: still read as ownership
            "Lane has Carriageway [E7].",
        ):
            error = self._error(sentence)
            self.assertIsNotNone(error, sentence)
            self.assertIn("a step the cited block does not hold", error)

    def test_the_same_claim_is_not_judged_against_a_passage(self):
        self.chunks[0] = {**self.chunks[0], "text": "Accident has Lane in the model."}
        self.assertIsNone(self._error("Accident has Lane [E1]."))  # the passage decides, as before

    def test_the_claim_is_read_per_citation_segment(self):
        self.assertIsNone(self._error("Carriageway has Lane [E7]; LocationReference can be a Location [E7]."))
        self.assertIsNotNone(self._error("Carriageway has Lane [E7]; Lane has Carriageway [E7]."))

    def test_a_sentence_in_another_shape_is_left_to_the_other_checks(self):
        self.assertIsNone(sp.step_claim_error("The path from Accident to Lane has eight steps.", self.block))

    def test_the_other_checks_still_apply_to_a_sentence_citing_the_block(self):
        error = self._error("SituationRecord uses `Roadworks.xsd` for it [E7].")
        self.assertIsNotNone(error)  # a file name the block does not hold

    def test_a_purpose_claim_is_grounded_by_a_definition_line_not_by_a_step(self):
        chunks = [*_passages(6), self.block]
        # Carriageway has a definition line in the block; Impact is nowhere.
        self.assertIsNone(_sentence_purpose_error("`Carriageway` is used to describe the lanes of a road [E7].", chunks))
        # SituationRecord's definition line is there too; a class only named in a step line has none.
        plain = sp.build_block(sp.find_paths([ACC, IMP], _data())[0], ["One record within a situation. Collisions between vehicles."], _data())
        plain = {**plain, "semanticPathDefined": []}
        self.assertIn("SituationRecord", plain["text"])
        self.assertIsNotNone(_sentence_purpose_error("`SituationRecord` is used to hold the cause [E7].", [*_passages(6), plain]))


class LoaderTests(SimpleTestCase):
    """The reading of relations, asserted subclass links and definitions from GraphDB's answers."""

    NS = "https://docs.datex2.eu/v3.7/model#"

    def _answers(self, query: str) -> list[dict]:
        def b(**values):
            return {key: {"value": (self.NS + value if key != "label" and key != "definition" else value)} for key, value in values.items()}

        if "SELECT DISTINCT ?prop ?concept ?related" in query and "owl#ObjectProperty" in query and "GRAPH ?g" in query:
            return [b(prop="Situation.SituationRecord.LocationReference", concept="Situation.SituationRecord", related="LocationReferencing.LocationReference"),
                    b(prop="Common.name", concept="Common.A", related="Common.B")]
        if "GRAPH ?g { ?concept <http://www.w3.org/2000/01/rdf-schema#subClassOf>" in query:
            return [b(concept="Situation.Accident", related="Situation.SituationRecord")]
        if "skos/core#definition" in query and "GRAPH ?g" in query:
            return [b(concept="Situation.Accident", definition="Collisions.   Of vehicles.")]
        if "prefLabel" in query:
            return [b(concept=name, label="x") for name in ("Situation.Accident", "Situation.SituationRecord", "LocationReferencing.LocationReference", "Common.A", "Common.B")]
        return []

    def _load(self, fail_new: bool = False):
        def fake_urlopen(request, timeout=0):
            from urllib.parse import parse_qs, urlparse

            query = parse_qs(urlparse(request.full_url).query)["query"][0]
            if fail_new and ("GRAPH ?g" in query):
                raise OSError("refused")
            payload = {"results": {"bindings": self._answers(query)}}
            return io.BytesIO(json.dumps(payload).encode())

        with mock.patch("urllib.request.urlopen", fake_urlopen):
            return sg._load_ontology_from_graphdb("http://graphdb.invalid/repositories/x", 0)

    def test_relations_keep_their_direction_and_the_name_after_the_domain(self):
        onto = self._load()
        self.assertIn(("datex:Situation.SituationRecord", "datex:LocationReferencing.LocationReference", "LocationReference"), onto["relations"])
        self.assertIn(("datex:Common.A", "datex:Common.B", "Common.name"), onto["relations"])

    def test_subclass_links_are_the_asserted_ones_and_definitions_are_read(self):
        onto = self._load()
        self.assertEqual(onto["subclass_edges"], [("datex:Situation.Accident", "datex:Situation.SituationRecord")])
        self.assertEqual(onto["concepts"]["datex:Situation.Accident"]["definition"], "Collisions. Of vehicles.")
        data = sg._build_directed_from_ontology(onto)
        self.assertEqual(data["supers"], {"datex:Situation.Accident": ["datex:Situation.SituationRecord"]})
        self.assertEqual(data["out"]["datex:Situation.SituationRecord"], [("datex:LocationReferencing.LocationReference", "LocationReference")])

    def test_unreadable_relations_leave_the_ontology_load_intact(self):
        with self.assertLogs("helpdesk.services.semantic_graph", level="WARNING"):
            onto = self._load(fail_new=True)
        self.assertTrue(onto["concepts"])
        self.assertEqual(onto["relations"], [])
        self.assertEqual(onto["subclass_edges"], [])
