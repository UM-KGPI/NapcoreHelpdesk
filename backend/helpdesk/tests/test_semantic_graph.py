from __future__ import annotations

from unittest.mock import patch

from django.test import SimpleTestCase

import helpdesk.services.semantic_graph as semantic_graph
from helpdesk.services.semantic_graph import (
    _alias_matches_text,
    _normalize_for_matching,
    _parse_transmodel_alignment_file,
    expand_graph_concepts,
    get_concept_transmodel_ids,
)


class SemanticGraphMappingTests(SimpleTestCase):
    def test_extract_graph_concepts_can_match_example_alias_on_standard_concept(self):
        with patch.object(
            semantic_graph,
            "GRAPH_CONCEPT_ALIASES",
            {"netex:Line": {"simple line", "simple line xml"}},
        ):
            concepts = semantic_graph.extract_graph_concepts(
                "Show me a NeTEx XML example for a simple line with stop points."
            )

        self.assertIn("netex:Line", concepts)


class AliasMatchesTextTests(SimpleTestCase):
    """Regression coverage for the word-boundary bug found investigating a weak
    production answer to "What is OnwardCall?": a multi-word alias like "is on"
    is a plain substring of "what is onwardcall" (the end of "is" plus the start
    of "onwardcall"), even though "on" is never a real token in that text. The
    fix drops the substring check and relies solely on the token-subset check,
    which already requires every alias word to appear as its own token."""

    def test_multiword_alias_does_not_match_across_a_word_boundary(self):
        text = _normalize_for_matching("What is OnwardCall?")
        self.assertFalse(_alias_matches_text("is on", text))

    def test_multiword_alias_still_matches_as_separate_real_words(self):
        text = _normalize_for_matching("the light is on now")
        self.assertTrue(_alias_matches_text("is on", text))

    def test_multiword_alias_still_matches_scattered_out_of_order(self):
        text = _normalize_for_matching("what type of line is used")
        self.assertTrue(_alias_matches_text("type of line", text))

    def test_multiword_alias_matches_glued_camelcase_class_name(self):
        """"OnwardCall" typed with no space lowercases to one glued token
        ("onwardcall") the subset check alone can't split. Checking whether the
        alias's words concatenated form a single existing text token covers this
        for every multi-word alias, not just this one concept."""
        text = _normalize_for_matching("What is OnwardCall?")
        self.assertTrue(_alias_matches_text("onward call", text))

    def test_glued_match_does_not_reopen_the_word_boundary_bug(self):
        """"is on" joined is "ison", which must not equal "onwardcall"."""
        text = _normalize_for_matching("What is OnwardCall?")
        self.assertFalse(_alias_matches_text("is on", text))


class SubclassTraversalTests(SimpleTestCase):
    """rdfs:subClassOf is followed from a class to its subclasses only. Followed
    upward, netex:Journey reaches framework roots such as netex:DataManagedObject
    (92 subclasses), and the next hop floods the expansion with unrelated
    siblings."""

    def _relations(self):
        ontology = {
            "concepts": {
                "netex:DataManagedObject": {"labels": ["x"], "related_to": [], "narrower": ["netex:Journey", "netex:Unrelated"]},
                "netex:Journey": {"labels": ["x"], "related_to": [], "narrower": ["netex:ServiceJourney"]},
                "netex:ServiceJourney": {"labels": ["x"], "related_to": ["netex:Line"], "narrower": []},
                "netex:Line": {"labels": ["x"], "related_to": [], "narrower": []},
                "netex:Unrelated": {"labels": ["x"], "related_to": [], "narrower": []},
            }
        }
        with patch.object(semantic_graph, "TRANSMODEL_TO_CONCEPTS", {}):
            return semantic_graph._build_graph_relations_from_ontology(ontology)

    def test_abstract_class_reaches_its_subclass(self):
        self.assertIn("netex:ServiceJourney", self._relations()["netex:Journey"])

    def test_class_does_not_climb_to_its_superclass(self):
        self.assertNotIn("netex:DataManagedObject", self._relations().get("netex:Journey", set()))
        self.assertNotIn("netex:Journey", self._relations().get("netex:ServiceJourney", set()))

    def test_object_properties_stay_bidirectional(self):
        relations = self._relations()
        self.assertIn("netex:Line", relations["netex:ServiceJourney"])
        self.assertIn("netex:ServiceJourney", relations["netex:Line"])


class TransmodelPivotTests(SimpleTestCase):
    """The static, GraphDB-independent replacement for the NITS cross-standard
    pivot (Phase 0.1 of docs/ontology/NITS-REMOVAL-PLAN.md)."""

    def test_parse_transmodel_alignment_file_extracts_exact_match_pairs(self):
        import tempfile
        from pathlib import Path

        sample = (
            "@prefix skos: <http://www.w3.org/2004/02/skos/core#> .\n"
            "@prefix tm:   <https://transmodel-cen.eu/6.2/> .\n"
            "@prefix netex: <https://netex.org.uk/netex/2.0#> .\n"
            "\n"
            "netex:StopPlace\n"
            "    skos:exactMatch tm:STOP_PLACE ;\n"
            '    tmalign:transmodelDefinitionStatus "differs" ;\n'
            '    tmalign:alignmentMethod "name-match" .\n'
            "\n"
            "netex:QuayList\n"
            "    skos:exactMatch tm:NOT_A_REAL_CLASS ;\n"
            '    tmalign:transmodelDefinitionStatus "equivalent" ;\n'
            '    tmalign:alignmentMethod "curated" .\n'
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "transmodel-netex-align.ttl"
            path.write_text(sample, encoding="utf-8")
            mapping = _parse_transmodel_alignment_file(path)

        self.assertEqual(
            mapping,
            {
                "netex:StopPlace": "transmodel:STOP_PLACE",
                "netex:QuayList": "transmodel:NOT_A_REAL_CLASS",
            },
        )

    def test_parse_transmodel_alignment_file_missing_file_returns_empty(self):
        from pathlib import Path

        self.assertEqual(_parse_transmodel_alignment_file(Path("/nonexistent/x.ttl")), {})

    def test_get_concept_transmodel_ids_resolves_only_known_concepts(self):
        with patch.object(
            semantic_graph,
            "CONCEPT_TO_TRANSMODEL",
            {"netex:DatedVehicleJourney": "transmodel:DATED_VEHICLE_JOURNEY"},
        ):
            resolved = get_concept_transmodel_ids({"netex:DatedVehicleJourney", "netex:Unrelated"})

        self.assertEqual(resolved, {"transmodel:DATED_VEHICLE_JOURNEY"})

    def test_expand_graph_concepts_bridges_standards_through_shared_transmodel_class(self):
        """The static Transmodel pivot, with no live ontology/GraphDB data at
        all -- this is the mechanism that keeps working when
        GRAPHDB_ENABLED=False."""
        with (
            patch.object(
                semantic_graph,
                "CONCEPT_TO_TRANSMODEL",
                {
                    "netex:DatedVehicleJourney": "transmodel:DATED_VEHICLE_JOURNEY",
                    "siri:DatedVehicleJourney": "transmodel:DATED_VEHICLE_JOURNEY",
                },
            ),
            patch.object(
                semantic_graph,
                "TRANSMODEL_TO_CONCEPTS",
                {"transmodel:DATED_VEHICLE_JOURNEY": {"netex:DatedVehicleJourney", "siri:DatedVehicleJourney"}},
            ),
            patch.object(semantic_graph, "GRAPH_RELATIONS", {}),
        ):
            expanded = expand_graph_concepts({"netex:DatedVehicleJourney"}, hops=1)

        self.assertIn("siri:DatedVehicleJourney", expanded)

    def test_real_committed_alignment_files_bridge_netex_and_siri_dated_vehicle_journey(self):
        """Regression test against the actual committed alignment TTLs (not a
        mock): confirms the plan's own worked example -- a NeTEx vehicle-
        journey concept must still surface its SIRI sibling with
        GRAPHDB_ENABLED=False -- holds against real data, not just a
        synthetic fixture."""
        expanded = expand_graph_concepts({"netex:DatedVehicleJourney"}, hops=1)
        self.assertIn("siri:DatedVehicleJourney", expanded)


class QuestionWordVariantTests(SimpleTestCase):
    """A question may name a class in everyday wording: a plural, or a word the
    model spells with a short prefix ("charging station" for RECHARGING STATION)."""

    def _concepts(self, aliases, question):
        with patch.object(semantic_graph, "GRAPH_CONCEPT_ALIASES", aliases):
            return semantic_graph.extract_graph_concepts(question, word_variants=True)

    def test_word_without_the_model_prefix_matches(self):
        concepts = self._concepts({"netex:RechargingStation": {"recharging station"}}, "How are e charging stations represented in NeTex ?")
        self.assertEqual(concepts, {"netex:RechargingStation"})

    def test_plural_matches(self):
        concepts = self._concepts({"netex:JourneyPattern": {"journey pattern"}}, "How does NeTEx represent journey patterns?")
        self.assertEqual(concepts, {"netex:JourneyPattern"})

    def test_prefix_stripped_words_alone_do_not_match(self):
        """At least one label word must appear as itself or its plural."""
        concepts = self._concepts({"netex:RechargingRebooking": {"recharging rebooking"}}, "charging booking")
        self.assertEqual(concepts, set())

    def test_short_words_never_match_by_suffix(self):
        concepts = self._concepts({"netex:Deadline": {"deadline date"}}, "line date")
        self.assertEqual(concepts, set())

    def test_association_labels_keep_the_strict_match(self):
        """Verb phrases like "relates to" would otherwise match ordinary wording."""
        concepts = self._concepts({"transmodel:relatesTo": {"relates to"}}, "How does it relate to a line?")
        self.assertEqual(concepts, set())

    def test_chunk_text_keeps_the_strict_match(self):
        with patch.object(semantic_graph, "GRAPH_CONCEPT_ALIASES", {"netex:RechargingStation": {"recharging station"}}):
            self.assertEqual(semantic_graph.extract_graph_concepts("charging stations"), set())


class ConceptsNamedByTermsTests(SimpleTestCase):
    ALIASES = {
        "netex:ScheduledStopPoint": {"scheduled stop point"},
        "netex:Point": {"point"},
        "netex:FlexibleServiceProperties": {"flexible service properties"},
        "transmodel:relatesTo": {"relates to"},
    }

    def _concepts(self, terms):
        with patch.object(semantic_graph, "GRAPH_CONCEPT_ALIASES", self.ALIASES):
            return semantic_graph.concepts_named_by_terms(terms)

    def test_term_yields_its_longest_matching_label_only(self):
        self.assertEqual(self._concepts(["SCHEDULED STOP POINT"]), {"netex:ScheduledStopPoint"})

    def test_underscored_term_matches(self):
        self.assertEqual(self._concepts(["FLEXIBLE_SERVICE_PROPERTIES"]), {"netex:FlexibleServiceProperties"})

    def test_invented_term_yields_nothing(self):
        self.assertEqual(self._concepts(["DEMAND RESPONSIVE OPERATION"]), set())

    def test_associations_are_never_named(self):
        self.assertEqual(self._concepts(["RELATES TO"]), set())


class OptInConceptScopeTests(SimpleTestCase):
    """TN-ITS concepts count only for questions whose scope names TN-ITS, like TN-ITS's text passages."""

    ALIASES = {
        "netex:DataSource": {"data source"},
        "tnits:Dataset": {"Dataset"},
        "tnits:SpeedLimit": {"speed limit"},
    }

    def _extract(self, text, scope=None):
        with patch.object(semantic_graph, "GRAPH_CONCEPT_ALIASES", self.ALIASES):
            return semantic_graph.extract_graph_concepts(text, word_variants=True, scope=scope)

    def test_tn_its_concepts_are_left_out_of_a_question_that_does_not_name_tn_its(self):
        question = "Which data source publishes the speed limit dataset?"
        self.assertEqual(self._extract(question), {"netex:DataSource"})
        self.assertEqual(self._extract(question, scope=["NeTEx", "SIRI"]), {"netex:DataSource"})

    def test_tn_its_concepts_count_when_the_scope_names_tn_its(self):
        question = "Which data source publishes the speed limit dataset?"
        self.assertEqual(
            self._extract(question, scope=["tn-its"]), {"netex:DataSource", "tnits:Dataset", "tnits:SpeedLimit"}
        )

    def test_terms_never_name_opt_in_concepts(self):
        # The vocabulary bridge (legislation, everyday wording) works on the core standards only.
        with patch.object(semantic_graph, "GRAPH_CONCEPT_ALIASES", self.ALIASES):
            self.assertEqual(semantic_graph.concepts_named_by_terms(["SPEED LIMIT"]), set())

    def test_concepts_in_scope_filters_a_set(self):
        concepts = {"netex:DataSource", "tnits:Dataset"}
        self.assertEqual(semantic_graph.concepts_in_scope(concepts, None), {"netex:DataSource"})
        self.assertEqual(semantic_graph.concepts_in_scope(concepts, ["TN-ITS"]), concepts)


class OntologyReloadTests(SimpleTestCase):
    """A source ontology loaded after the process read the labels (nightly refresh) is picked up without a restart."""

    def _run(self, *, latest_loaded_at, read_at, last_check_ago=10_000, aliases=None):
        import datetime as dt

        tables = {"tnits:Dataset": {"Dataset"}} if aliases is None else aliases
        live_aliases = {"netex:Line": {"line"}}
        live_relations: dict = {}
        aggregate = patch(
            "helpdesk.models.OntologyAssetVersion.objects.aggregate", return_value={"latest": latest_loaded_at}
        )
        with aggregate, patch.object(semantic_graph, "GRAPH_CONCEPT_ALIASES", live_aliases), patch.object(
            semantic_graph, "GRAPH_RELATIONS", live_relations
        ), patch.object(semantic_graph, "_ONTOLOGY_READ_AT", read_at), patch.object(
            semantic_graph, "_last_ontology_check", semantic_graph.time.monotonic() - last_check_ago
        ), patch.object(semantic_graph, "_load_ontology", return_value={"concepts": {}}), patch.object(
            semantic_graph, "_build_concept_aliases_from_ontology", return_value=tables
        ), patch.object(semantic_graph, "_build_graph_relations_from_ontology", return_value={"tnits:Dataset": set()}):
            reloaded = semantic_graph.reload_ontology_if_updated()
            return reloaded, dict(live_aliases), dict(live_relations)

    def test_rereads_after_a_later_load(self):
        import datetime as dt

        read_at = dt.datetime(2026, 11, 6, 9, 0, tzinfo=dt.timezone.utc)
        reloaded, aliases, relations = self._run(latest_loaded_at=read_at + dt.timedelta(hours=1), read_at=read_at)
        self.assertTrue(reloaded)
        self.assertEqual(aliases, {"tnits:Dataset": {"Dataset"}})  # updated in place, so other modules see it
        self.assertIn("tnits:Dataset", relations)

    def test_keeps_the_tables_when_nothing_was_loaded_since(self):
        import datetime as dt

        read_at = dt.datetime(2026, 11, 6, 9, 0, tzinfo=dt.timezone.utc)
        reloaded, aliases, _ = self._run(latest_loaded_at=read_at - dt.timedelta(hours=1), read_at=read_at)
        self.assertFalse(reloaded)
        self.assertEqual(aliases, {"netex:Line": {"line"}})

    def test_checks_at_most_every_few_minutes(self):
        import datetime as dt

        read_at = dt.datetime(2026, 11, 6, 9, 0, tzinfo=dt.timezone.utc)
        reloaded, _, _ = self._run(latest_loaded_at=read_at + dt.timedelta(hours=1), read_at=read_at, last_check_ago=5)
        self.assertFalse(reloaded)

    def test_an_empty_read_keeps_the_old_tables(self):
        import datetime as dt

        read_at = dt.datetime(2026, 11, 6, 9, 0, tzinfo=dt.timezone.utc)
        reloaded, aliases, _ = self._run(latest_loaded_at=read_at + dt.timedelta(hours=1), read_at=read_at, aliases={})
        self.assertFalse(reloaded)
        self.assertEqual(aliases, {"netex:Line": {"line"}})
