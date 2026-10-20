"""
Django management command to harvest XSD element definitions from schema repositories.

This is a one-time operation (or periodic refresh) that:
1. Scans all XSD files in configured repositories
2. Extracts element definitions (elements, types, groups)
3. Stores them as SourceChunk records with doc_type="xsd-definition"
4. Indexes them for semantic search

After harvesting, the runtime system no longer depends on repository access.

Usage:
    python manage.py harvest_xsd_definitions
    python manage.py harvest_xsd_definitions --standard NeTEx
    python manage.py harvest_xsd_definitions --dry-run
"""

import logging
from pathlib import Path
from xml.etree import ElementTree as ET
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.utils import timezone
from helpdesk.models import SourceChunk

logger = logging.getLogger(__name__)


# Configuration: Repository paths and their standards
REPO_CONFIG = {
    "NeTEx": {
        "path": "/Users/andrejt/Research/repositories/git/NeTEx",
        "xsd_subdirs": ["xsd/netex_framework", "xsd/netex_part_1", "xsd/netex_part_2"],
        "repo_url": "https://github.com/TransmodelEcosystem/NeTEx",
    },
    "SIRI": {
        "path": "/Users/andrejt/Research/repositories/git/SIRI",
        "xsd_subdirs": ["xsd"],
        "repo_url": "https://github.com/TransmodelEcosystem/SIRI",
    },
    "OpRa": {
        "path": "/Users/andrejt/Research/repositories/git/OpRa",
        "xsd_subdirs": ["xsd"],
        "repo_url": "https://github.com/TransmodelEcosystem/OpRa",
    },
}


class XSDHarvester:
    """Harvest XSD element definitions from schema repositories."""

    def __init__(self, standard="NeTEx", dry_run=False):
        self.standard = standard
        self.dry_run = dry_run
        self.definitions_found = 0
        self.definitions_stored = 0

    def harvest(self):
        """Harvest XSD definitions for specified standard."""
        config = REPO_CONFIG.get(self.standard)
        if not config:
            raise CommandError(f"Standard {self.standard} not configured")

        repo_path = Path(config["path"])
        if not repo_path.exists():
            raise CommandError(f"Repository path not found: {repo_path}")

        logger.info(f"Harvesting XSD definitions from {self.standard} ({repo_path})")

        # Find all XSD files
        xsd_files = []
        for subdir in config["xsd_subdirs"]:
            subdir_path = repo_path / subdir
            if subdir_path.exists():
                xsd_files.extend(subdir_path.glob("**/*.xsd"))

        logger.info(f"Found {len(xsd_files)} XSD files")

        # Extract definitions from each file
        for xsd_file in xsd_files:
            self._extract_from_file(xsd_file, config)

        logger.info(f"Harvest complete: {self.definitions_found} definitions found, {self.definitions_stored} stored")

    def _extract_from_file(self, xsd_file: Path, config: dict):
        """Extract element definitions from a single XSD file."""
        try:
            tree = ET.parse(xsd_file)
            root = tree.getroot()
            ns = {"xs": "http://www.w3.org/2001/XMLSchema"}

            # Extract xs:element definitions
            for elem in root.findall(".//xs:element", ns):
                name = elem.get("name")
                elem_type = elem.get("type")
                if name:
                    self.definitions_found += 1
                    if not self.dry_run:
                        self._store_definition(
                            name=name,
                            elem_type=elem_type,
                            element_xml=ET.tostring(elem, encoding="unicode"),
                            source_file=str(xsd_file.relative_to(config["path"])),
                            config=config,
                        )

            # Extract xs:complexType definitions
            for elem in root.findall(".//xs:complexType", ns):
                name = elem.get("name")
                if name:
                    self.definitions_found += 1
                    if not self.dry_run:
                        self._store_definition(
                            name=name,
                            elem_type="complexType",
                            element_xml=ET.tostring(elem, encoding="unicode")[:1000],
                            source_file=str(xsd_file.relative_to(config["path"])),
                            config=config,
                        )

            # Extract xs:group definitions (named groups, e.g. ServiceJourneyGroup).
            # These hold the actual <xs:element ref="..."/> declarations that
            # complexTypes merely reference via <xs:group ref="..."/>, so without
            # this pass most element content inside groups is never indexed.
            for elem in root.findall(".//xs:group", ns):
                name = elem.get("name")
                if name:
                    self.definitions_found += 1
                    if not self.dry_run:
                        self._store_definition(
                            name=name,
                            elem_type="group",
                            element_xml=ET.tostring(elem, encoding="unicode")[:2000],
                            source_file=str(xsd_file.relative_to(config["path"])),
                            config=config,
                        )

        except ET.ParseError as e:
            logger.warning(f"Failed to parse {xsd_file}: {e}")

    def _store_definition(self, name: str, elem_type: str, element_xml: str, source_file: str, config: dict):
        """Store a definition as a SourceChunk."""
        from helpdesk.services.embeddings import build_text_embedding

        chunk_id = f"xsd-def-{self.standard.lower()}-{name.lower()}"

        # Build chunk text
        chunk_text = f"""
XSD SCHEMA DEFINITION: {name}
Standard: {self.standard}
Type: {elem_type or 'element'}
Source: {source_file}

Definition:
{element_xml[:2000]}
"""

        # Generate embedding for the definition
        try:
            embedding = build_text_embedding(chunk_text.strip())
        except Exception as e:
            logger.warning(f"Failed to generate embedding for {name}: {e}")
            embedding = []

        chunk_data = {
            "text": chunk_text.strip(),
            "label": f"XSD Definition: {name}",
            "doc_type": "xsd-definition",
            "chunk_type": "xsd-definition",
            "quality_score": 0.96,
            "standards_scope": [self.standard],
            "repository_url": config["repo_url"],
            "commit_sha": "master",
            "source_path": source_file,
            "heading": f"{name} - {self.standard} XSD Definition",
            "embedding_vector": embedding,
            "updated_at": timezone.now(),
        }

        try:
            # Use update_or_create to handle re-harvests
            SourceChunk.objects.update_or_create(chunk_id=chunk_id, defaults=chunk_data)
            self.definitions_stored += 1
            logger.debug(f"Stored: {name}")
        except Exception as e:
            logger.error(f"Failed to store definition {name}: {e}")


class Command(BaseCommand):
    help = "Harvest XSD element definitions from schema repositories"

    def add_arguments(self, parser):
        parser.add_argument(
            "--standard",
            type=str,
            default="NeTEx",
            choices=["NeTEx", "SIRI", "OpRa", "all"],
            help="Standard to harvest (default: NeTEx)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be done without storing",
        )

    def handle(self, *args, **options):
        standard = options["standard"]
        dry_run = options["dry_run"]

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN MODE - no data will be stored"))

        standards = ["NeTEx", "SIRI", "OpRa"] if standard == "all" else [standard]

        for std in standards:
            try:
                harvester = XSDHarvester(standard=std, dry_run=dry_run)
                harvester.harvest()
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✓ {std}: {harvester.definitions_found} found, {harvester.definitions_stored} stored"
                    )
                )
            except CommandError as e:
                self.stdout.write(self.style.ERROR(f"✗ {std}: {e}"))
