from __future__ import annotations

import json
import re
from pathlib import Path

from django.test import SimpleTestCase

from helpdesk.services.rule_engine import evaluate_semantic_rules


class ArtifactRulesCompetencyTests(SimpleTestCase):
    def setUp(self):
        self.repo_root = Path(__file__).resolve().parents[3]
        self.registry_path = self.repo_root / "docs" / "testing" / "competency-questions-artifact-rules.json"
        self.netex_rules_path = self.repo_root / "docs" / "ontology" / "artifact-rules" / "netex-artifact-rules-v1.0.ttl"
        self.opra_rules_path = self.repo_root / "docs" / "ontology" / "artifact-rules" / "opra-artifact-rules-v1.0.ttl"

    def _load_registry(self) -> dict:
        return json.loads(self.registry_path.read_text(encoding="utf-8"))

    def _extract_rule_individual_ids(self, ttl_text: str) -> set[str]:
        matches = re.findall(
            r"^rule:([A-Za-z0-9_\-]+)\s*\n\s*a\s+rule:[A-Za-z0-9_\-]+",
            ttl_text,
            re.MULTILINE,
        )
        return set(matches)

    def test_registry_contains_seed_competency_questions(self):
        data = self._load_registry()
        ids = {item["id"] for item in data["competencyQuestions"]}

        self.assertIn("CQ-NETEX-SVC-01", ids)
        self.assertIn("CQ-NETEX-STOP-01", ids)
        self.assertIn("CQ-NETEX-STOP-02", ids)
        self.assertIn("CQ-OPRA-ROLE-01", ids)
        self.assertIn("CQ-SIRI-RT-01", ids)
        self.assertIn("CQ-DATEX-EVT-01", ids)

    def test_netex_required_rules_exist_with_provenance(self):
        data = self._load_registry()
        ttl_text = self.netex_rules_path.read_text(encoding="utf-8")

        required = [
            item
            for item in data["competencyQuestions"]
            if item.get("standard") == "NeTEx" and item.get("requiresRule") is True
        ]

        for item in required:
            rule_id = item["ruleId"]
            rule_marker = f"rule:{rule_id}"
            start = ttl_text.find(rule_marker)
            self.assertNotEqual(start, -1, msg=f"Missing rule declaration for {rule_id}")

            next_rule = ttl_text.find("\n\nrule:", start + len(rule_marker))
            block = ttl_text[start:] if next_rule == -1 else ttl_text[start:next_rule]
            self.assertIn("rule:derivedFromSchema", block, msg=f"Missing derivedFromSchema for {rule_id}")
            self.assertIn("rule:derivedFromXPath", block, msg=f"Missing derivedFromXPath for {rule_id}")

    def test_no_rule_outcomes_for_netex_stopplace(self):
        data = self._load_registry()
        ttl_text = self.netex_rules_path.read_text(encoding="utf-8")

        stop_questions = [
            item
            for item in data["competencyQuestions"]
            if item["id"].startswith("CQ-NETEX-STOP-")
        ]
        self.assertTrue(stop_questions)
        self.assertTrue(all(item.get("requiresRule") is False for item in stop_questions))

        # No StopPlace-specific mandatory containment rule should be present.
        self.assertNotIn("StopPlace", ttl_text)

    def test_opra_artifact_rules_near_empty(self):
        ttl_text = self.opra_rules_path.read_text(encoding="utf-8")
        individuals = self._extract_rule_individual_ids(ttl_text)
        self.assertEqual(individuals, set())

    def test_rule_engine_reports_competency_question_matches(self):
        semantic_query = {
            "intent": "definition",
            "normativity": "unspecified",
            "original_terms": ["SIRI", "realtime", "monitoring"],
        }

        result = evaluate_semantic_rules(
            semantic_query=semantic_query,
            retrieved_chunks=[
                {
                    "docType": "guide",
                    "standardsScope": ["SIRI"],
                    "sourcePath": "examples/siri/realtime-monitoring.xml",
                }
            ],
            effective_scope=["SIRI"],
        )

        self.assertIn("competencyQuestionIds", result)
        self.assertIn("CQ-SIRI-RT-01", result["competencyQuestionIds"])
        self.assertTrue(
            any(conclusion.get("type") == "COMPETENCY_QUESTION_MATCH" for conclusion in result["conclusions"])
        )
