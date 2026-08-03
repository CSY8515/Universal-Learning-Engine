import inspect
import json
import tempfile
import unittest
from pathlib import Path

from operational_database import (
    DatabaseManager,
    OperationalDataPlane,
    OperationalDatabase,
    OperationalQuery,
    OperationalRegistryError,
    OperationalValidationError,
    PERSONAL_SECRETARY_CAPABILITY_ID,
    PersonalSecretaryCoreCapability,
    PersonalSecretaryIntegration,
    PersonalSecretaryIntegrationError,
    RecordCategory,
    default_manager_registry,
    default_record_registry,
)


class ExamplePersonalSecretaryCore(PersonalSecretaryCoreCapability):
    def __init__(self):
        self.deliveries = []

    def receive_operational_report(self, capability_id, envelope):
        self.deliveries.append((capability_id, envelope))
        return "accepted"


class OperationalDatabaseV108Tests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.database = OperationalDatabase(
            Path(self.temporary.name) / "operational.db"
        )
        self.manager = DatabaseManager(self.database)

    def tearDown(self):
        self.database.close()
        self.temporary.cleanup()

    @staticmethod
    def event(category, index=0, **overrides):
        value = {
            "category": category,
            "source": "learning-engine",
            "event_type": "lesson_execution",
            "message": f"operational event {index}",
            "occurred_at": f"2026-08-03T12:{index:02d}:00+00:00",
            "correlation_id": f"correlation-{index}",
            "operation_id": f"operation-{index}",
            "payload": {"attempt": index},
        }
        value.update(overrides)
        return value

    def test_required_record_types_and_manager_capabilities_are_registered(self):
        definitions = default_record_registry().definitions()
        self.assertEqual(
            {definition.category for definition in definitions},
            set(RecordCategory),
        )
        capabilities = {
            definition.name
            for definition in default_manager_registry().definitions()
        }
        self.assertEqual(
            capabilities,
            {
                "data_validation",
                "classification",
                "duplicate_control",
                "pattern_analysis",
                "operational_analysis",
                "recommendation",
                "rule_candidate",
                "standard_candidate",
                "operational_reporting",
            },
        )

    def test_every_required_operational_category_is_preserved(self):
        for index, category in enumerate(RecordCategory):
            self.manager.ingest(self.event(category.value, index))
        retained = self.database.query(OperationalQuery(limit=100))
        self.assertEqual(len(retained), len(RecordCategory))
        self.assertEqual({record.category for record in retained}, set(RecordCategory))
        self.assertEqual(self.database.count(), len(RecordCategory))

    def test_validation_classification_and_sensitive_value_redaction(self):
        record = self.manager.ingest(
            self.event(
                "validation-failure",
                payload={"api_key": "must-not-persist", "nested": {"token": "x"}},
                metadata={"password": "secret", "safe": True},
            )
        )
        self.assertEqual(record.category, RecordCategory.VALIDATION_FAILURE)
        self.assertEqual(record.payload["api_key"], "[REDACTED]")
        self.assertEqual(record.payload["nested"]["token"], "[REDACTED]")
        self.assertEqual(record.metadata["password"], "[REDACTED]")
        with self.assertRaises(OperationalRegistryError):
            self.manager.ingest(self.event("unknown-category"))
        with self.assertRaises(OperationalValidationError):
            self.manager.ingest(self.event("error", payload={"bad": object()}))

    def test_duplicates_are_preserved_but_removed_from_canonical_analysis(self):
        raw = self.event("execution_failure", 1)
        first = self.manager.ingest(raw)
        second = self.manager.ingest(raw)
        self.assertEqual(second.duplicate_of, first.record_id)
        self.assertEqual(self.database.count(), 2)
        self.assertEqual(self.database.count(include_duplicates=False), 1)
        analysis = self.manager.operational_analysis()
        self.assertEqual(analysis["total_records"], 2)
        self.assertEqual(analysis["unique_records"], 1)
        self.assertEqual(analysis["duplicate_records"], 1)
        self.assertIsNotNone(self.database.get(first.record_id))
        self.assertIsNotNone(self.database.get(second.record_id))

    def test_manager_builds_patterns_recommendations_and_inactive_candidates(self):
        for index in range(3):
            self.manager.ingest(
                self.event(
                    "failure",
                    index,
                    source="challenge",
                    event_type="session_start",
                )
            )
            self.manager.ingest(
                self.event(
                    "success",
                    index + 10,
                    source="recovery",
                    event_type="session_complete",
                )
            )
        self.manager.ingest(
            self.event(
                "recovery",
                20,
                correlation_id="correlation-0",
                source="challenge",
                event_type="session_recovered",
            )
        )
        report = self.manager.generate_operational_report()
        self.assertTrue(report.patterns)
        self.assertTrue(report.recommendations)
        self.assertTrue(report.rule_candidates)
        self.assertTrue(report.standard_candidates)
        self.assertTrue(all(item.status == "candidate" for item in report.rule_candidates))
        self.assertNotIn(
            next(
                record.record_id
                for record in self.database.query(OperationalQuery(limit=100))
                if record.correlation_id == "correlation-0"
                and record.category == RecordCategory.FAILURE
            ),
            report.unresolved_record_ids,
        )

    def test_operational_report_is_retained_as_summary(self):
        self.manager.ingest(self.event("incident"))
        report = self.manager.generate_operational_report()
        stored = json.loads(self.database.latest_report())
        self.assertEqual(stored["report_id"], report.report_id)
        self.assertEqual(stored["category_counts"]["incident"], 1)
        self.assertNotIn("payload", stored)
        self.assertNotIn("message", stored)

    def test_personal_secretary_integration_delivers_versioned_report(self):
        integration = PersonalSecretaryIntegration()
        with self.assertRaises(PersonalSecretaryIntegrationError):
            self.manager.generate_operational_report(publish_to=integration)
        core = ExamplePersonalSecretaryCore()
        integration.connect(core)
        self.manager.ingest(self.event("warning"))
        report = self.manager.generate_operational_report(publish_to=integration)
        self.assertEqual(len(core.deliveries), 1)
        capability_id, envelope = core.deliveries[0]
        self.assertEqual(capability_id, PERSONAL_SECRETARY_CAPABILITY_ID)
        self.assertEqual(envelope["report"]["report_id"], report.report_id)
        integration.disconnect()
        self.assertFalse(integration.connected)

    def test_data_plane_has_no_record_deletion_contract_and_runtime_is_unchanged(self):
        methods = {
            name
            for name, value in inspect.getmembers(
                OperationalDataPlane, inspect.isfunction
            )
            if not name.startswith("_")
        }
        self.assertFalse(methods & {"delete", "remove", "truncate", "reset"})
        app_source = Path("app.py").read_text(encoding="utf-8")
        self.assertNotIn("operational_database", app_source)


if __name__ == "__main__":
    unittest.main()
