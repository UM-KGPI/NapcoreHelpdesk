"""The class card (services/class_card.py), step 2 of an internal plan (kept outside the repository).

No database, no network, no model. The tables a card is built from are read from the committed ontology files
(docs/ontology/standards/datex.ttl and transmodel.ttl) the way the ontology load reads them from GraphDB, by rdflib; the
twelve reference cards (benchmarks/class-card-oracle.yaml) were written from the Enterprise Architect files by direct SQL.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from unittest import mock

import rdflib
import yaml
from django.test import SimpleTestCase, override_settings
from rdflib import OWL, RDF, RDFS, SKOS

from helpdesk.api import views
from helpdesk.management.commands.benchmark_utils import local_benchmark_file
from helpdesk.management.commands import locate_answer_sources, run_retrieval_benchmark
from helpdesk.services import class_card, datex, llm_generator, policy_guard, retrieval_gateway, semantic_graph as sg, semantic_path

ROOT = Path(__file__).resolve().parents[3]
STANDARDS = ROOT / "docs" / "ontology" / "standards"
ORACLE = local_benchmark_file("class-card-oracle.yaml")  # kept outside the repository (HELPDESK_BENCHMARKS_DIR)
EA = rdflib.Namespace(class_card.EA)
_tables_cache: dict = {}


def _rows(graph: rdflib.Graph) -> dict[str, list[dict]]:
    """The rows the three member queries of class_card.member_queries return, read from the parsed Turtle file."""
    text = lambda value: str(value) if value is not None else None
    rows: dict[str, list[dict]] = {"classes": [], "members": [], "relations": []}
    for concept, kind in graph.subject_objects(EA.kind):
        rows["classes"].append({"c": str(concept), "kind": str(kind), **({"label": str(graph.value(concept, RDFS.label))} if graph.value(concept, RDFS.label) else {}), **({"comment": str(graph.value(concept, RDFS.comment))} if graph.value(concept, RDFS.comment) else {})})
    for role in (EA.attribute, EA.value):
        for concept, node in graph.subject_objects(role):
            row = {"c": str(concept), "role": str(role), "name": str(graph.value(node, EA.name))}
            for key, predicate in (("pos", EA.position), ("type", EA.type), ("typeName", EA.typeName), ("lo", EA.lowerBound), ("up", EA.upperBound), ("def", EA.definition)):
                value = graph.value(node, predicate)
                if value is not None:
                    row[key] = text(value)
            rows["members"].append(row)
    for prop in graph.subjects(RDF.type, OWL.ObjectProperty):
        row = {"prop": str(prop), "d": str(graph.value(prop, RDFS.domain)), "r": str(graph.value(prop, RDFS.range))}
        for key, predicate in (("label", RDFS.label), ("lo", EA.lowerBound), ("up", EA.upperBound), ("text", EA.multiplicityText)):
            value = graph.value(prop, predicate)
            if value is not None:
                row[key] = text(value)
        rows["relations"].append(row)
    return rows


def _tables(*names: str) -> tuple[dict, dict]:
    """(members, directed) of the named ontology files, as the ontology load builds them."""
    key = tuple(names)
    if key in _tables_cache:
        return _tables_cache[key]
    rows: dict[str, list[dict]] = {"classes": [], "members": [], "relations": []}
    concepts: dict[str, dict] = {}
    relations: set[tuple[str, str, str]] = set()
    edges: set[tuple[str, str]] = set()
    for name in names:
        graph = rdflib.Graph()
        graph.parse(str(STANDARDS / f"{name}.ttl"), format="turtle")
        for part, value in _rows(graph).items():
            rows[part].extend(value)
        for concept in graph.subjects(RDF.type, OWL.Class):
            concept_id = sg.iri_to_concept_id(str(concept))
            entry = concepts.setdefault(concept_id, {"labels": [], "related_to": [], "narrower": []})
            definition = graph.value(concept, SKOS.definition)
            if definition is not None:
                entry["definition"] = " ".join(str(definition).split())
        for prop in graph.subjects(RDF.type, OWL.ObjectProperty):
            domain = sg.iri_to_concept_id(str(graph.value(prop, RDFS.domain)))
            range_ = sg.iri_to_concept_id(str(graph.value(prop, RDFS.range)))
            if domain and range_ and domain != range_:
                relations.add((domain, range_, sg.relation_name(sg.iri_to_concept_id(str(prop)), domain)))
        for sub, sup in graph.subject_objects(RDFS.subClassOf):
            a, b = sg.iri_to_concept_id(str(sub)), sg.iri_to_concept_id(str(sup))
            if a and b and a != b:
                edges.add((a, b))
    members = class_card.build_members(rows, sg.iri_to_concept_id, sg.relation_name)
    directed = sg._build_directed_from_ontology({"concepts": concepts, "relations": sorted(relations), "subclass_edges": sorted(edges)})
    _tables_cache[key] = (members, directed)
    return members, directed


def _concept_of(entry: dict, members: dict) -> str:
    key = "datex" if entry["ontology"] == "DATEX II" else "transmodel"
    if key == "datex":
        return f"datex:{entry['namespace']}.{entry['name']}"
    found = [c for c, e in members["classes"].items() if c.startswith("transmodel:") and e["label"] == entry["name"]]
    assert len(found) == 1, found
    return found[0]


class OracleCardTests(SimpleTestCase):
    """Gate (a): each reference card equals the builder's output, line by line."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.members, cls.directed = _tables("datex", "transmodel")
        cls.cards = yaml.safe_load(ORACLE.read_text(encoding="utf-8"))["cards"] if ORACLE.is_file() else None

    def test_tables_hold_every_class_and_member_of_the_files(self):
        self.assertEqual(len(self.members["classes"]), 1159 + 1648)
        self.assertEqual(sum(len(v) for v in self.members["attributes"].values()), 1539 + 3064)
        self.assertEqual(sum(len(v) for v in self.members["values"].values()), 3489 + 21)

    def test_each_oracle_card_equals_the_builder_line_by_line(self):
        if self.cards is None:
            self.skipTest(f"the reference cards ({ORACLE}) are kept outside the repository; the test only makes sense on them")
        self.assertEqual(len(self.cards), 12)
        for entry in self.cards:
            concept = _concept_of(entry, self.members)
            card = class_card.build_card(concept, members=self.members, directed=self.directed)
            self.assertIsNotNone(card, entry["id"])
            want = entry["text"] if isinstance(entry["text"], list) else entry["text"].split("\n")
            self.assertEqual(card.text.split("\n"), want, entry["id"])
            self.assertEqual(card.ladder, 0, entry["id"])
            self.assertEqual(card.chars, entry["length"], entry["id"])


class CapAndLadderTests(SimpleTestCase):
    """Gate (b): never over the cap, whole lines only, the count line equals what was dropped."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.members, cls.directed = _tables("datex", "transmodel")

    def _card(self, concept, **kwargs):
        return class_card.build_card(concept, members=self.members, directed=self.directed, **kwargs)

    def test_no_card_of_either_ontology_is_over_the_cap_and_the_ladder_is_only_used_when_needed(self):
        steps = {}
        for concept in self.members["classes"]:
            whole = self._card(concept, max_chars=10**9)
            card = self._card(concept)
            self.assertIsNotNone(card, concept)
            self.assertLessEqual(card.chars, class_card.MAX_CARD_CHARS, concept)
            self.assertEqual(card.ladder == 0, whole.chars <= class_card.MAX_CARD_CHARS, concept)
            steps[card.ladder] = steps.get(card.ladder, 0) + 1
        self.assertGreater(steps.get(0, 0), 2000)  # most cards are whole

    def test_every_line_of_a_cut_card_is_a_line_of_the_whole_card_or_that_line_without_its_definition(self):
        for concept in ("datex:EnergyInfrastructure.ElectricChargingPointStatus", "transmodel:FARE_PRODUCT", "datex:Common.SpecialDay", "datex:Situation.Accident"):
            whole = self._card(concept, max_chars=10**9).text.split("\n")
            for limit in (2400, 1800, 1200, 800, 500):
                card = self._card(concept, max_chars=limit)
                if card is None:
                    continue
                lines = card.text.split("\n")
                self.assertLessEqual(len(card.text), limit, (concept, limit))
                for line in lines[:-1]:
                    ok = line in whole or any(w.startswith(line + ": ") for w in whole) or re.search(r" \(and \d+ more, not shown\)$", line)
                    self.assertTrue(ok, (concept, limit, line))
                self.assertTrue(lines[-1].startswith("Source: docs/ontology/standards/"), lines[-1])
                if card.ladder:
                    self.assertIn("left out:", lines[-1])

    def test_the_count_line_equals_what_was_dropped(self):
        concept = "datex:EnergyInfrastructure.ElectricChargingPointStatus"
        whole = self._card(concept, max_chars=10**9)
        members_with_definition = [line for line in whole.text.split("\n") if line.startswith("- ") and "): " in line]
        own = 4 + 0  # remainingChargingTime, currentVoltage, currentChargingPower, nextAvailableChargingSlots
        # step 1: the definitions of inherited members go
        one = self._card(concept, max_chars=len(whole.text) - 1)
        inherited_with_definition = len(members_with_definition) - own
        self.assertEqual(one.ladder, 1)
        self.assertIn(f"left out: {inherited_with_definition} definitions of inherited members.", one.text)
        self.assertEqual(len([line for line in one.text.split("\n") if line.startswith("- ") and "): " in line]), own)
        # step 2: the own ones go too
        two = self._card(concept, max_chars=len(one.text) - 1)
        self.assertEqual(two.ladder, 2)
        self.assertIn(f"{inherited_with_definition} definitions of inherited members; {own} definitions of own members.", two.text)
        self.assertFalse([line for line in two.text.split("\n") if line.startswith("- ") and "): " in line])
        # step 4: the farthest supertype groups go, nearest kept
        four = self._card("datex:EnergyInfrastructure.ElectricChargingPointStatus", max_chars=1000)
        self.assertEqual(four.ladder, 4)
        groups = [line for line in whole.text.split("\n") if line.startswith("Inherited from ")]
        kept = [line for line in four.text.split("\n") if line.startswith("Inherited from ")]
        self.assertEqual(kept, groups[: len(kept)])
        self.assertIn(f"{len(groups) - len(kept)} inherited groups ({', '.join(g[len('Inherited from '):-1] for g in groups[len(kept):])})", four.text)

    def test_values_over_the_limit_say_how_many_are_not_shown(self):
        card = self._card("datex:Common.PublicEventTypeEnum")
        self.assertEqual(len(self.members["values"]["datex:Common.PublicEventTypeEnum"]), 60)
        self.assertIn("Values (60): ", card.text)
        self.assertIn("(and 45 more, not shown)", card.text)
        definitions = sum(1 for v in self.members["values"]["datex:Common.PublicEventTypeEnum"] if v["definition"])
        self.assertTrue(card.text.endswith(f"left out: 45 values of PublicEventTypeEnum; {definitions} definitions of own members."))
        shown = card.text.split("Values (60): ")[1].split(" (and ")[0].split(", ")
        self.assertEqual(shown, [v["name"] for v in self.members["values"]["datex:Common.PublicEventTypeEnum"]][:15])

    def test_values_the_question_names_come_first_and_one_gets_its_definition(self):
        concept = "datex:LocationReferencing.LaneEnum"
        plain = self._card(concept)
        asked = self._card(concept, question="Which lane type is a bus lane, and what is a crawler lane?")
        first = asked.text.split("Values (27): ")[1].split(", ")
        self.assertEqual(sorted(first[:2]), ["busLane", "crawlerLane"])
        self.assertNotEqual(plain.text, asked.text)
        self.assertEqual(len([l for l in asked.text.split("\n") if l.startswith("  busLane: ") or l.startswith("  crawlerLane: ")]), 2)
        self.assertLessEqual(asked.chars, class_card.MAX_CARD_CHARS)

    def test_ladder_steps_do_not_depend_on_the_question(self):
        concept = "datex:EnergyInfrastructure.ElectricChargingPointStatus"
        a = self._card(concept, max_chars=1500)
        b = self._card(concept, max_chars=1500, question="who maintains the thing")  # names no value
        self.assertEqual((a.ladder, a.left_out), (b.ladder, b.left_out))
        c = self._card(concept, max_chars=1500, question="status of the charging point")  # names the value "charging"
        self.assertEqual(c.ladder, a.ladder)

    def test_a_class_without_loaded_members_gets_no_card(self):
        self.assertIsNone(self._card("datex:Nowhere.Nothing"))
        self.assertIsNone(class_card.build_card("datex:Situation.Delays", members={}, directed=self.directed))


class SpecialClassTests(SimpleTestCase):
    """Gate (g): a class that starts in lower case, a name repeated in two namespaces, an enumeration of 60 values,
    a class with two supertypes."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.members, cls.directed = _tables("datex", "transmodel")

    def test_a_transmodel_class_that_starts_in_lower_case_gets_a_card(self):
        concepts = [c for c in self.members["classes"] if c.startswith("transmodel:") and c.partition(":")[2][:1].islower()]
        self.assertEqual(len(concepts), 59)
        card = class_card.build_card(concepts[0], members=self.members, directed=self.directed)
        label = self.members["classes"][concepts[0]]["label"]
        self.assertEqual(card.text.split("\n")[0], f"Transmodel class {label}")
        self.assertTrue(card.text.endswith("docs/ontology/standards/transmodel.ttl; nothing left out."))

    def test_a_name_in_two_namespaces_is_written_with_its_namespace(self):
        status = [c for c in self.members["classes"] if c.endswith(".ElectricChargingPointStatus")]
        self.assertEqual(len(status), 2)
        for concept in status:
            card = class_card.build_card(concept, members=self.members, directed=self.directed)
            self.assertTrue(card.text.split("\n")[0].startswith(f"DATEX II class {concept.partition(':')[2]} (namespace "))
        unique = class_card.build_card("datex:Situation.Delays", members=self.members, directed=self.directed)
        self.assertEqual(unique.text.split("\n")[0], "DATEX II class Delays (namespace Situation / Classes/Impact)")

    def test_two_labels_of_one_transmodel_class_name_are_told_apart_by_the_local_name(self):
        repeated = sorted(c for c in self.members["repeated"] if c.startswith("transmodel:"))
        self.assertEqual(len(repeated), 4)
        heads = {class_card.build_card(c, members=self.members, directed=self.directed).text.split("\n")[0] for c in repeated}
        self.assertEqual(len(heads), 4)

    def test_an_enumeration_of_sixty_values(self):
        card = class_card.build_card("datex:Common.PublicEventTypeEnum", members=self.members, directed=self.directed)
        self.assertEqual(card.text.split("\n")[0], "DATEX II enumeration PublicEventTypeEnum (namespace Common / Enumerations)")
        self.assertLessEqual(card.chars, 2400)

    def test_a_class_with_two_supertypes_lists_both_and_inherits_from_both(self):
        for concept, parents in sorted(self.directed["supers"].items()):
            if len(parents) < 2 or not concept.startswith("transmodel:"):
                continue
            card = class_card.build_card(concept, members=self.members, directed=self.directed, max_chars=10**9)
            names = sorted((class_card.shown_name(p, self.members) for p in parents), key=str.lower)
            line = [l for l in card.text.split("\n") if l.startswith("Supertypes: ")][0]
            self.assertEqual(line, "Supertypes: " + ", ".join(names))
            for parent in parents:
                has_members = bool(self.members["attributes"].get(parent) or self.directed["out"].get(parent))
                self.assertEqual(f"Inherited from {class_card.shown_name(parent, self.members)}:" in card.text, has_members, (concept, parent))
            return
        self.fail("no class with two supertypes")


class SettingAndHookTests(SimpleTestCase):
    """Gate (c): the setting empty, and members missing from the graph: nothing changes."""

    def _served(self):
        return [
            {"chunkId": "a", "sourcePath": "datex-model-v3.7/Situation.Delays", "repositoryUrl": "https://github.com/x/y", "text": "record text", "score": 0.9, "docType": "datex", "commitSha": "c"},
            {"chunkId": "b", "sourcePath": "xsd/a.xsd", "repositoryUrl": "https://github.com/x/z", "text": "xsd", "score": 0.8, "docType": "schema", "commitSha": "c"},
        ]

    @override_settings(RETRIEVAL_CLASS_CARD_ONTOLOGIES="")
    def test_empty_setting_is_off_and_nothing_is_queried(self):
        self.assertEqual(class_card.configured_ontologies(), set())
        self.assertFalse(class_card.enabled())
        called = []
        self.assertEqual(class_card.read_member_rows(lambda name, query: called.append(name) or [], sg._IRI_PREFIX_MAP), {})
        self.assertEqual(called, [])

    @override_settings(RETRIEVAL_CLASS_CARD_ONTOLOGIES=" DATEX , Transmodel ")
    def test_the_setting_is_a_list_of_ontology_keys(self):
        self.assertEqual(class_card.configured_ontologies(), {"datex", "transmodel"})
        names = []
        class_card.read_member_rows(lambda name, query: names.append((name, query)) or [], sg._IRI_PREFIX_MAP)
        self.assertEqual([n for n, _ in names], ["class members: classes", "class members: members", "class members: relations"])
        self.assertIn("https://docs.datex2.eu/v3.7/model#", names[0][1])
        self.assertNotIn("netex.org.uk", names[0][1])

    @override_settings(RETRIEVAL_CLASS_CARD_ONTOLOGIES="datex")
    def test_members_missing_from_the_graph_leave_the_chunks_as_they_were(self):
        chunks = self._served()
        result, info = class_card.with_cards(chunks, 6, members={}, directed={})
        self.assertEqual(result, self._served())
        self.assertEqual(info["cards"], [])
        members, directed = _tables("datex")
        without = {**members, "classes": {}}
        result, info = class_card.with_cards(self._served(), 6, members=without, directed=directed)
        self.assertEqual(result, self._served())

    def _loader(self, member_queries: list[str], ontologies: str):
        def fake_urlopen(request, timeout=None):
            url = request.full_url
            if "prefLabel" in url:
                payload = {"results": {"bindings": [{"concept": {"value": "https://docs.datex2.eu/v3.7/model#Situation.Delays"}, "label": {"value": "Delays"}}]}}
            else:
                payload = {"results": {"bindings": []}}
            if "ea-model" in url or "ea%3A" in url or "ea:kind" in url:
                member_queries.append(url)
            import io

            return io.BytesIO(json.dumps(payload).encode())

        with override_settings(RETRIEVAL_CLASS_CARD_ONTOLOGIES=ontologies), mock.patch("urllib.request.urlopen", fake_urlopen):
            return sg._load_ontology_from_graphdb("http://graphdb.invalid/repositories/x", 0)

    def test_the_load_reads_the_members_only_when_the_setting_names_an_ontology(self):
        asked: list[str] = []
        off = self._loader(asked, "")
        self.assertEqual(asked, [])
        self.assertNotIn("members", off)
        asked = []
        on = self._loader(asked, "datex")
        self.assertEqual(len(asked), 3)
        # the member rows were empty: nothing is stored, and the other tables are those of the load with the setting empty
        self.assertNotIn("members", on)
        self.assertEqual({k: v for k, v in on.items()}, {k: v for k, v in off.items()})

    def test_no_table_without_members(self):
        self.assertEqual(sg._build_members_from_ontology({"concepts": {}}), {})

    @override_settings(RETRIEVAL_CLASS_CARD_ONTOLOGIES="")
    def test_the_gateway_returns_the_same_evidence_and_trace_with_the_setting_empty(self):
        served = self._served()
        trace = {"graphExpansionSource": "none"}
        with mock.patch.object(retrieval_gateway, "_retrieve_chunks_once", return_value=(json.loads(json.dumps(served)), dict(trace))), mock.patch(
            "helpdesk.services.llm_generator.english_search_query", return_value=None
        ), mock.patch.object(retrieval_gateway, "prepared_index", return_value=False):
            chunks, out_trace = retrieval_gateway._retrieve_chunks_with_trace_untimed("What is a delay?", 6, 0.0, english_question=None)
        self.assertEqual(chunks, served)
        self.assertNotIn("classCards", out_trace)

    @override_settings(RETRIEVAL_CLASS_CARD_ONTOLOGIES="datex,transmodel")
    def test_the_gateway_with_the_setting_on_but_no_member_loaded_returns_the_same_evidence(self):
        served = self._served()
        with mock.patch.object(retrieval_gateway, "_retrieve_chunks_once", return_value=(json.loads(json.dumps(served)), {})), mock.patch(
            "helpdesk.services.llm_generator.english_search_query", return_value=None
        ), mock.patch.object(retrieval_gateway, "prepared_index", return_value=False), mock.patch.dict(sg.CLASS_MEMBERS, {}, clear=True):
            chunks, out_trace = retrieval_gateway._retrieve_chunks_with_trace_untimed("What is a delay?", 6, 0.0, english_question=None)
        self.assertEqual(chunks, served)
        self.assertEqual(out_trace["classCards"]["cards"], [])


class ReplacedRecordTests(SimpleTestCase):
    """Gate (d): the card of a record keeps its place, number and replacesSourcePath; a card after a definition block
    is numbered after the passages."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.members, cls.directed = _tables("datex", "transmodel")

    def _record(self, path="datex-model-v3.7/Situation.Delays", chunk_id="datex-model-x-00"):
        return {
            "chunkId": chunk_id, "sourcePath": path, "repositoryUrl": "https://github.com/UM-KGPI/NapcoreHelpdesk", "commitSha": "abc",
            "sourceUrl": "https://docs.datex2.eu/downloads/modelv37/", "text": "DATEX II class Delays (namespace Situation)\nrecord", "score": 0.77,
            "label": "DATEX II class Delays", "heading": "DATEX II class Delays (namespace Situation)", "docType": "datex", "chunkType": "model",
            "standardsScope": ["DATEX II"], "structuredMetadata": {"x": 1}, "retrievalEventId": "re-1", "wholeRecord": True, "pieceText": "p",
        }

    def _definition_block(self):
        return {
            "chunkId": "ontology-def-tm-sensor_equipment", "sourcePath": "docs/ontology/standards/transmodel.ttl#SENSOR_EQUIPMENT",
            "repositoryUrl": "https://github.com/UM-KGPI/NapcoreHelpdesk/blob/main/docs/ontology/standards/transmodel.ttl", "commitSha": "main",
            "text": "CONCEPT DEFINITION: SENSOR EQUIPMENT (SensorEquipment)\nStandard: Transmodel (conceptual reference model, v6.2)\nIRI: https://transmodel-cen.eu/6.2/SENSOR_EQUIPMENT\n\nDefinition:\nAn EQUIPMENT used to measure values.",
            "docType": "ontology-definition", "score": 0.99, "label": "Definition: SENSOR EQUIPMENT (Transmodel)", "standardsScope": ["Transmodel"],
        }

    @override_settings(RETRIEVAL_CLASS_CARD_ONTOLOGIES="datex,transmodel")
    def test_a_record_keeps_its_place_number_and_path(self):
        other = {"chunkId": "o", "sourcePath": "xsd/a.xsd", "repositoryUrl": "https://github.com/x/z", "text": "xsd", "score": 0.5, "docType": "schema", "commitSha": "c"}
        chunks = [other, self._record(), dict(other, chunkId="p", sourcePath="xsd/b.xsd")]
        result, info = class_card.with_cards(chunks, 6, members=self.members, directed=self.directed)
        self.assertEqual(len(result), 3)
        self.assertEqual([c["chunkId"] for c in result][::2], ["o", "p"])
        card = result[1]
        self.assertTrue(class_card.is_card(card))
        self.assertFalse(class_card.is_added_card(card))
        self.assertFalse(semantic_path.is_path_block(card))  # a passage: it keeps its number
        self.assertEqual(card["replacesSourcePath"], "datex-model-v3.7/Situation.Delays")
        self.assertEqual(card["replacesRepositoryUrl"], "https://github.com/UM-KGPI/NapcoreHelpdesk")
        self.assertEqual(card["replacesChunkId"], "datex-model-x-00")
        self.assertEqual((card["score"], card["retrievalEventId"], card["standardsScope"]), (0.77, "re-1", ["DATEX II"]))
        self.assertEqual(card["sourcePath"], "docs/ontology/standards/datex.ttl#class=Situation.Delays")
        self.assertEqual(card["repositoryUrl"], "https://github.com/UM-KGPI/NapcoreHelpdesk/blob/main/docs/ontology/standards/datex.ttl")
        for dropped in ("sourceUrl", "pieceText", "wholeRecord"):
            self.assertNotIn(dropped, card)
        self.assertTrue(card["text"].startswith("DATEX II class Delays (namespace Situation / Classes/Impact)\nDefinition: "))
        self.assertEqual(info["cards"][0]["trigger"], "record")
        # numbers: the prompt window shows the passages in order, the card at the record's number
        self.assertEqual([c["chunkId"] for c in semantic_path.prompt_window(result, 6)][1], card["chunkId"])
        # the file found: the record's, for the yardstick and for locate_answer_sources
        self.assertEqual(class_card.found_source(card), ("https://github.com/UM-KGPI/NapcoreHelpdesk", "datex-model-v3.7/Situation.Delays"))
        self.assertEqual(locate_answer_sources._item_fields(card)[:2], ("https://github.com/UM-KGPI/NapcoreHelpdesk", "datex-model-v3.7/Situation.Delays"))
        self.assertEqual(locate_answer_sources._snapshot(result)[1][1], "datex-model-v3.7/Situation.Delays")
        self.assertTrue(run_retrieval_benchmark._hit_at_k(result, ["Situation.Delays"], 3, 1))
        self.assertEqual(run_retrieval_benchmark._mrr_at_k(result, ["Situation.Delays"], 3), 0.5)
        # a chunk that is no card is read as before
        self.assertEqual(locate_answer_sources._item_fields(other)[:2], ("https://github.com/x/z", "xsd/a.xsd"))

    @override_settings(RETRIEVAL_CLASS_CARD_ONTOLOGIES="datex,transmodel")
    def test_a_card_after_a_definition_block_is_numbered_after_the_passages_and_is_no_file_found(self):
        path_block = {"chunkId": "semantic-path-x", "semanticPath": True, "sourcePath": "p", "text": "t"}
        passages = [dict(self._record(chunk_id=f"c{i}", path=f"xsd/{i}.xsd"), docType="schema") for i in range(6)]
        chunks = passages[:2] + [self._definition_block()] + passages[2:] + [path_block]
        result, info = class_card.with_cards(chunks, 6, members=self.members, directed=self.directed)
        self.assertEqual(result[:-1], chunks)
        card = result[-1]
        self.assertTrue(class_card.is_added_card(card))
        self.assertTrue(semantic_path.is_path_block(card))
        self.assertNotIn("Definition:", card["text"])  # the block has the definition
        self.assertTrue(card["text"].startswith("Transmodel class SENSOR EQUIPMENT\nSupertypes: INSTALLED EQUIPMENT"))
        window = semantic_path.prompt_window(result, 6)
        self.assertEqual([c["chunkId"] for c in window][-2:], ["semantic-path-x", card["chunkId"]])
        self.assertEqual(len([c for c in window if not semantic_path.is_path_block(c)]), 6)
        self.assertEqual(len(locate_answer_sources._snapshot(result)), len(chunks) - 1)
        self.assertEqual(card["sourcePath"], "docs/ontology/standards/transmodel.ttl#class=SENSOR_EQUIPMENT")
        # carried like a path block when the evidence is replaced
        self.assertIn(card["chunkId"], [c["chunkId"] for c in semantic_path.carry(result, passages)])

    @override_settings(RETRIEVAL_CLASS_CARD_ONTOLOGIES="datex")
    def test_only_listed_ontologies_get_cards(self):
        chunks = [self._definition_block(), self._record()]
        result, _info = class_card.with_cards(chunks, 6, members=self.members, directed=self.directed)
        self.assertEqual(len(result), 2)
        self.assertTrue(class_card.is_card(result[1]))
        self.assertFalse(class_card.is_card(result[0]))

    @override_settings(RETRIEVAL_CLASS_CARD_ONTOLOGIES="datex,transmodel")
    def test_at_most_three_cards_and_a_class_only_once_and_only_in_the_six(self):
        paths = ["Situation.Delays", "Situation.Accident", "Common.SpecialDay", "Vms.VmsController", "TrafficRegulation.AdvisorySpeed"]
        chunks = [self._record(f"datex-model-v3.7/{p}", f"c{i}") for i, p in enumerate(paths)] + [self._record("datex-model-v3.7/Situation.Delays", "dup")]
        with mock.patch.object(class_card, "MAX_NET_CHARS", 10**6):
            result, info = class_card.with_cards(chunks, 6, members=self.members, directed=self.directed)
        self.assertEqual(sum(class_card.is_card(c) for c in result), 3)
        self.assertEqual([c["trigger"] for c in info["cards"]], ["record"] * 3)
        # the cap removes the lowest ranked: the cards are those of the first three records, in their order
        self.assertEqual([c["concept"] for c in info["cards"]], [f"datex:{p}" for p in paths[:3]])
        self.assertEqual([class_card.is_card(c) for c in result[:5]], [True, True, True, False, False])
        with mock.patch.object(class_card, "MAX_NET_CHARS", 10**6):
            reversed_result, reversed_info = class_card.with_cards(list(reversed(chunks[:5])), 6, members=self.members, directed=self.directed)
        self.assertEqual([c["concept"] for c in reversed_info["cards"]], [f"datex:{p}" for p in reversed(paths)][:3])
        beyond = [self._record(f"xsd/{i}.xsd") for i in range(6)] + [self._record("datex-model-v3.7/Situation.Delays")]
        beyond = [dict(c, sourcePath=f"xsd/{i}.xsd") for i, c in enumerate(beyond[:6])] + beyond[6:]
        result, info = class_card.with_cards(beyond, 6, members=self.members, directed=self.directed)
        self.assertEqual(info["cards"], [])

    @override_settings(RETRIEVAL_CLASS_CARD_ONTOLOGIES="datex")
    def test_a_card_that_would_add_more_than_the_budget_is_not_made(self):
        chunks = [self._record("datex-model-v3.7/Situation.Accident", "a"), self._record("datex-model-v3.7/Common.SpecialDay", "b")]
        with mock.patch.object(class_card, "MAX_NET_CHARS", 10):
            result, info = class_card.with_cards(chunks, 6, members=self.members, directed=self.directed)
        self.assertEqual(result, chunks)

    @override_settings(RETRIEVAL_CLASS_CARD_ONTOLOGIES="datex")
    def test_a_card_over_what_is_left_of_the_budget_is_built_again_down_the_ladder(self):
        # step 4b: the card that does not fit is cut by the ladder (definitions first) until it does, and is skipped only when no rung fits
        path = "datex-model-v3.7/Situation.Accident"
        whole = class_card.build_card("datex:Situation.Accident", members=self.members, directed=self.directed)
        record = self._record(path, "a")
        replaced = len(record["text"])
        budget = whole.chars - replaced - 300  # the whole card goes over by 300 characters
        with mock.patch.object(class_card, "MAX_NET_CHARS", budget):
            result, info = class_card.with_cards([record], 6, members=self.members, directed=self.directed)
        self.assertTrue(class_card.is_card(result[0]))
        (entry,) = info["cards"]
        self.assertLessEqual(entry["netChars"], budget)
        self.assertEqual(entry["netChars"], entry["chars"] - replaced)
        self.assertGreater(entry["ladder"], whole.ladder)
        self.assertLess(entry["chars"], whole.chars)
        self.assertTrue(entry["leftOut"])  # the count line says what the ladder dropped
        self.assertIn("left out:", result[0]["text"])
        # the second card of the question gets what is left, not the whole budget
        other = self._record("datex-model-v3.7/Common.SpecialDay", "b")
        with mock.patch.object(class_card, "MAX_NET_CHARS", budget):
            _result, info = class_card.with_cards([record, other], 6, members=self.members, directed=self.directed)
        self.assertLessEqual(sum(max(0, c["netChars"]) for c in info["cards"]), budget)
        # a record whose card fits when whole is built as before
        with mock.patch.object(class_card, "MAX_NET_CHARS", 10**6):
            _result, info = class_card.with_cards([record], 6, members=self.members, directed=self.directed)
        self.assertEqual((info["cards"][0]["ladder"], info["cards"][0]["chars"]), (whole.ladder, whole.chars))

    @override_settings(RETRIEVAL_CLASS_CARD_ONTOLOGIES="transmodel")
    def test_a_card_after_a_definition_block_is_cut_to_what_is_left_of_the_budget(self):
        whole = class_card.build_card("transmodel:SENSOR_EQUIPMENT", members=self.members, directed=self.directed, with_definition=False)
        with mock.patch.object(class_card, "MAX_NET_CHARS", whole.chars - 100):
            _result, info = class_card.with_cards([self._definition_block()], 6, members=self.members, directed=self.directed)
        (entry,) = info["cards"]
        self.assertLessEqual(entry["netChars"], whole.chars - 100)
        self.assertEqual(entry["netChars"], entry["chars"])  # a block is replaced by nothing
        self.assertGreater(entry["ladder"], whole.ladder)

    @override_settings(RETRIEVAL_CLASS_CARD_ONTOLOGIES="datex")
    def test_the_card_text_is_shown_whole_by_the_prompt(self):
        card = class_card.with_cards([self._record()], 6, members=self.members, directed=self.directed)[0][0]
        messages = llm_generator._build_messages("What is a delay?", [card], max_chars_per_chunk=50)
        self.assertIn(json.dumps(card["text"])[1:-1], json.dumps(messages))


class RecordPathTests(SimpleTestCase):
    """Gate (h): the record path of a DATEX II element and the concept of its class, for all 1,159 records."""

    def test_round_trip_of_record_path_to_concept_for_every_record(self):
        model = json.loads((ROOT / "docs" / "datex" / "model-v3.7.json").read_text(encoding="utf-8"))
        records = datex.model_records(model)
        paths = {record["source_path"] for record in records}
        self.assertEqual(len(paths), 1159)
        graph = rdflib.Graph()
        graph.parse(str(STANDARDS / "datex.ttl"), format="turtle")
        classes = {sg.iri_to_concept_id(str(subject)) for subject in graph.subjects(EA.kind, None)}
        self.assertEqual(len(classes), 1159)
        found = {datex.concept_id_of_source_path(path) for path in paths}
        self.assertEqual(found, classes)
        for element in model["elements"]:
            path = datex.model_record_path(model["version"], element["namespace"], element["name"])
            self.assertIn(path, paths)
            self.assertEqual(datex.concept_id_of_source_path(path), f"datex:{element['namespace']}.{element['name']}")

    def test_other_paths_are_no_record(self):
        for path in ("docs.datex2.eu/v3.7/home", "xsd/a.xsd", "datex-model-v3.7/", "datex-model-v3.7/nodot", "datex-model-v3.6/A.B", ""):
            self.assertIsNone(datex.concept_id_of_source_path(path))


class CitationAndChecksTests(SimpleTestCase):
    """Gates (e) and (f): the policy, the title, the term check and the sentence check."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.members, cls.directed = _tables("datex", "transmodel")
        cls.sensor = class_card.added_card_chunk(class_card.build_card("transmodel:SENSOR_EQUIPMENT", members=cls.members, directed=cls.directed), cls.members)
        cls.advisory = class_card.replacing_card_chunk(
            class_card.build_card("datex:TrafficRegulation.AdvisorySpeed", members=cls.members, directed=cls.directed),
            ReplacedRecordTests()._record("datex-model-v3.7/TrafficRegulation.AdvisorySpeed"), cls.members,
        )

    def _loaded(self):
        return mock.patch.dict(sg.DIRECTED_RELATIONS, self.directed), mock.patch.dict(sg.CLASS_MEMBERS, self.members)

    def test_the_policy_accepts_the_citation_of_a_card_and_refuses_a_file_not_loaded(self):
        a, b = self._loaded()
        with a, b:
            for chunk in (self.sensor, self.advisory):
                result = policy_guard.evaluate_policy("A sentence [E1].", [{"repositoryUrl": chunk["repositoryUrl"], "sourcePath": chunk["sourcePath"]}])
                self.assertTrue(result["allowed"], chunk["sourcePath"])
            gtfs = "https://github.com/UM-KGPI/NapcoreHelpdesk/blob/main/docs/ontology/standards/gtfs.ttl"
            result = policy_guard.evaluate_policy("A sentence [E1].", [{"repositoryUrl": gtfs, "sourcePath": "docs/ontology/standards/gtfs.ttl#class=X"}])
            self.assertFalse(result["allowed"])
            self.assertEqual(result["reason"], "POLICY_BLOCK")

    def test_the_title_names_the_ontology_and_the_class(self):
        a, b = self._loaded()
        with a, b:
            self.assertEqual(views._citation_title(self.advisory["sourcePath"]), {"title": "DATEX II ontology: class AdvisorySpeed"})
            self.assertEqual(views._citation_title(self.sensor["sourcePath"]), {"title": "Transmodel ontology: class SENSOR EQUIPMENT"})
            self.assertEqual(views._citation_title("docs/ontology/standards/datex.ttl#path=A=B")["title"], "DATEX II ontology: path A to B")
        self.assertEqual(class_card.citation_title("docs/ontology/standards/datex.ttl"), "")
        self.assertEqual(class_card.citation_title("xsd/a.xsd#class=B"), "")

    def test_the_term_check_reads_what_the_card_defines(self):
        defined = lambda name, chunk: llm_generator._element_has_definition_in_evidence(name, [chunk])
        self.assertTrue(defined("SENSOR EQUIPMENT", self.sensor))
        self.assertTrue(defined("Id", self.sensor))  # an attribute it lists
        self.assertTrue(defined("AdvisorySpeed", self.advisory))
        self.assertTrue(defined("UnitOfSpeedEnum", self.advisory))  # an enumeration whose values it lists
        self.assertTrue(defined("unitOfMeasure", self.advisory))
        self.assertFalse(defined("Accident", self.advisory))  # no other
        self.assertFalse(defined("SpotSensor", self.sensor))
        # every class the card names (supertype, subtype, relation target) counts as defined, as the record's text did
        for name in ("INSTALLED EQUIPMENT", "ENTRANCE SENSOR", "DECK SENSOR ENTRY", "EQUIPMENT PLACE"):
            self.assertTrue(defined(name, self.sensor), name)

    def _error(self, sentence, chunk):
        return llm_generator._sentence_grounding_error(sentence, [chunk])

    def test_the_sentence_check_accepts_every_true_claim_of_a_transmodel_card_and_refuses_the_reversed_ones(self):
        true = [
            "SENSOR EQUIPMENT is an INSTALLED EQUIPMENT [E1].",
            "SENSOR EQUIPMENT is an EQUIPMENT [E1].",  # through the inherited groups
            "SENSOR EQUIPMENT can be an ENTRANCE SENSOR [E1].",
            "SENSOR EQUIPMENT can be a SPOT SENSOR [E1].",
            "SENSOR EQUIPMENT has a DECK SENSOR ENTRY [E1].",  # own relation
            "SENSOR EQUIPMENT has an EQUIPMENT PLACE [E1].",  # inherited relation
            "INSTALLED EQUIPMENT can be a SENSOR EQUIPMENT [E1].",
        ]
        reversed_ = [
            "INSTALLED EQUIPMENT is a SENSOR EQUIPMENT [E1].",
            "ENTRANCE SENSOR can be a SENSOR EQUIPMENT [E1].",
            "DECK SENSOR ENTRY has a SENSOR EQUIPMENT [E1].",
            "EQUIPMENT PLACE has an SENSOR EQUIPMENT [E1].",
            "SENSOR EQUIPMENT is an ENTRANCE SENSOR [E1].",
            "SENSOR EQUIPMENT has an INSTALLED EQUIPMENT [E1].",
        ]
        for sentence in true:
            self.assertIsNone(self._error(sentence, self.sensor), sentence)
        for sentence in reversed_:
            message = self._error(sentence, self.sensor)
            self.assertIsNotNone(message, sentence)
            self.assertIn("a step the cited block does not hold", message)

    def test_has_the_supertype_is_an_up_claim_and_has_the_subtype_a_down_claim(self):
        true = [
            "SENSOR EQUIPMENT has the supertype INSTALLED EQUIPMENT [E1].",
            "SENSOR EQUIPMENT has the supertype EQUIPMENT [E1].",  # through the inherited groups
            "SENSOR EQUIPMENT has the direct supertype INSTALLED EQUIPMENT [E1].",
            "SENSOR EQUIPMENT has a supertype INSTALLED EQUIPMENT [E1].",
            "The class SENSOR EQUIPMENT has the supertype INSTALLED EQUIPMENT and has a DECK SENSOR ENTRY [E1].",
            "SENSOR EQUIPMENT has the subtype ENTRANCE SENSOR [E1].",
            "SENSOR EQUIPMENT has the subtypes ENTRANCE SENSOR and SPOT SENSOR [E1].",
            "INSTALLED EQUIPMENT has the subtype SENSOR EQUIPMENT [E1].",
            "SENSOR EQUIPMENT has the subtype SPOT SENSOR and has a DECK SENSOR ENTRY [E1].",
        ]
        reversed_ = [
            "INSTALLED EQUIPMENT has the supertype SENSOR EQUIPMENT [E1].",
            "ENTRANCE SENSOR has the subtype SENSOR EQUIPMENT [E1].",
            "SENSOR EQUIPMENT has the supertype ENTRANCE SENSOR [E1].",
            "SENSOR EQUIPMENT has the subtype INSTALLED EQUIPMENT [E1].",
            "SENSOR EQUIPMENT has the subtype EQUIPMENT [E1].",
        ]
        for sentence in true:
            self.assertIsNone(self._error(sentence, self.sensor), sentence)
        for sentence in reversed_:
            self.assertIsNotNone(self._error(sentence, self.sensor), sentence)
        # a has claim is still read as one: the supertype words do not switch the reading off for another link
        self.assertIsNotNone(self._error("DECK SENSOR ENTRY has a SENSOR EQUIPMENT [E1].", self.sensor))

    def test_has_y_as_its_supertype_is_judged_by_direction_not_as_ownership(self):
        for sentence in (
            "SENSOR EQUIPMENT has INSTALLED EQUIPMENT as its supertype [E1].",
            "The class SENSOR EQUIPMENT has EQUIPMENT as its supertype [E1].",
            "INSTALLED EQUIPMENT has SENSOR EQUIPMENT as one of its subtypes [E1].",
            "SENSOR EQUIPMENT has INSTALLED EQUIPMENT as its supertype and has a DECK SENSOR ENTRY [E1].",
        ):
            self.assertIsNone(self._error(sentence, self.sensor), sentence)
        for sentence in (
            "INSTALLED EQUIPMENT has SENSOR EQUIPMENT as its supertype [E1].",
            "SENSOR EQUIPMENT has ENTRANCE SENSOR as its supertype [E1].",
            "SENSOR EQUIPMENT has INSTALLED EQUIPMENT as its subtype [E1].",
            "SENSOR EQUIPMENT has INSTALLED EQUIPMENT [E1].",  # no role stated
        ):
            self.assertIsNotNone(self._error(sentence, self.sensor), sentence)

    def test_the_sentence_check_on_a_datex_card_that_replaced_a_record(self):
        card = class_card.replacing_card_chunk(
            class_card.build_card("datex:RoadTrafficData.TrafficFlow", members=self.members, directed=self.directed),
            ReplacedRecordTests()._record("datex-model-v3.7/RoadTrafficData.TrafficFlow"), self.members,
        )
        self.assertIsNone(self._error("TrafficFlow is a TrafficData [E1].", card))
        self.assertIsNone(self._error("TrafficFlow is a BasicData [E1].", card))
        self.assertIsNone(self._error("TrafficFlow has an AxleFlowValue [E1].", card))
        self.assertIsNone(self._error("TrafficFlow has a VehicleCharacteristics [E1].", card))  # inherited relation
        self.assertIsNotNone(self._error("TrafficData is a TrafficFlow [E1].", card))
        self.assertIsNotNone(self._error("AxleFlowValue has a TrafficFlow [E1].", card))
        self.assertIsNotNone(self._error("BasicData is a TrafficFlow [E1].", card))

    def test_a_sentence_about_something_the_card_does_not_name_is_left_to_the_other_checks(self):
        self.assertIsNone(class_card.step_claim_error("DUTY is a SENSOR EQUIPMENT [E1].", self.sensor))
        self.assertIsNone(class_card.step_claim_error("The card has no more.", self.sensor))


class HeadAndCountTests(SimpleTestCase):
    """Step 2b: the card's head carries the record head's namespace and package; every definition of an enumeration's
    values that the card does not show is counted."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.members, cls.directed = _tables("datex", "transmodel")

    def test_the_place_is_read_from_the_comment_of_the_generator_and_from_no_other_comment(self):
        self.assertEqual(class_card.place_of("class", "DATEX II class in namespace Parking / Classes/ParkingStatus"), "namespace Parking / Classes/ParkingStatus")
        self.assertEqual(class_card.place_of("enumeration", "DATEX II enumeration in namespace Common / Enumerations"), "namespace Common / Enumerations")
        self.assertEqual(class_card.place_of("data type", "DATEX II data type in namespace Common"), "namespace Common")
        self.assertEqual(class_card.place_of("class", "A MODE used outside of public transport services, in namespace terms."), "")
        self.assertEqual(class_card.place_of("class", "DATEX II enumeration in namespace Common / Enumerations"), "")  # the kind must be the class's own
        self.assertEqual(class_card.place_of("class", ""), "")

    def test_every_datex_card_head_carries_the_text_the_record_head_carries(self):
        model = json.loads((ROOT / "docs" / "datex" / "model-v3.7.json").read_text(encoding="utf-8"))
        ambiguous = datex.ambiguous_names(model)
        checked = 0
        for element in model["elements"]:
            if not element["name"]:
                continue
            record_head = datex.element_text(element, ambiguous).split("\n", 1)[0]
            card = class_card.build_card(f"datex:{element['namespace']}.{element['name']}", members=self.members, directed=self.directed)
            self.assertIsNotNone(card, record_head)
            self.assertTrue(card.text.split("\n", 1)[0].endswith(record_head[record_head.index(" (namespace ") :]), (record_head, card.text.split("\n", 1)[0]))
            checked += 1
        self.assertEqual(checked, 1159)

    def test_a_transmodel_card_has_no_place(self):
        for concept in list(c for c in self.members["classes"] if c.startswith("transmodel:"))[:300]:
            self.assertEqual(self.members["classes"][concept]["place"], "", concept)

    def test_every_value_definition_an_enumeration_card_does_not_show_is_counted(self):
        questions = ["", "Which lane type is a bus lane, a crawler lane, a hard shoulder or a cycle lane?"]
        enumerations = [c for c, e in self.members["classes"].items() if e["kind"] == "enumeration"]
        self.assertGreater(len(enumerations), 300)
        for concept in enumerations:
            total = sum(1 for v in self.members["values"].get(concept, []) if v["definition"])
            for question in questions:
                for limit in (class_card.MAX_CARD_CHARS, 700):
                    card = class_card.build_card(concept, members=self.members, directed=self.directed, question=question, max_chars=limit)
                    if card is None:
                        continue
                    shown = len([line for line in card.text.split("\n") if re.match(r"^  \S.*: ", line)])
                    counted = re.search(r"(\d+) definitions of own members", card.text.rsplit("\n", 1)[1])
                    self.assertEqual(shown + (int(counted.group(1)) if counted else 0), total, (concept, question, limit))
