from __future__ import annotations

from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from helpdesk.services.index_builder import DEFAULT_EXTENSIONS, index_repository


class Command(BaseCommand):
    help = "Build retrieval index (SourceChunk) from an approved repository path."

    def add_arguments(self, parser):
        # Explicit repo URL/path keep indexing operations deliberate and auditable.
        parser.add_argument("--repo-url", required=True, help="Approved repository URL (e.g., https://github.com/NeTEx-CEN/NeTEx)")
        parser.add_argument("--repo-path", required=True, help="Local filesystem path to repository checkout")
        parser.add_argument(
            "--include-ext",
            action="append",
            dest="include_ext",
            default=None,
            help="File extension to include (repeatable), e.g. --include-ext .md",
        )
        parser.add_argument(
            "--include-path",
            action="append",
            dest="include_path",
            default=None,
            help="Path substring to include (repeatable)",
        )
        parser.add_argument(
            "--exclude-path",
            action="append",
            dest="exclude_path",
            default=None,
            help="Path substring to exclude (repeatable)",
        )
        parser.add_argument(
            "--profile",
            default="default",
            help="Indexing profile with include/exclude defaults",
        )
        parser.add_argument("--chunk-size", type=int, default=1200)
        parser.add_argument("--chunk-overlap", type=int, default=200)
        parser.add_argument("--incremental", action="store_true", help="Skip unchanged files based on hash + commit")
        parser.add_argument("--prune", action="store_true", help="Delete old chunks for this repository not seen in current run")
        parser.add_argument("--include-issues", action="store_true", help="Include GitHub issues/comments in the index")

    def handle(self, *args, **options):
        # Parse command arguments and enforce basic operational safety checks.
        repo_url = options["repo_url"].strip()
        repo_path = Path(options["repo_path"]).expanduser().resolve()
        include_ext = options.get("include_ext")
        include_path = options.get("include_path") or []
        exclude_path = options.get("exclude_path") or []
        profile = options["profile"]
        chunk_size = int(options["chunk_size"])
        chunk_overlap = int(options["chunk_overlap"])
        incremental = bool(options["incremental"])
        prune = bool(options["prune"])
        include_issues = bool(options["include_issues"])

        if not repo_url:
            raise CommandError("--repo-url must be non-empty")
        if not repo_path.exists() or not repo_path.is_dir():
            raise CommandError(f"--repo-path does not exist or is not a directory: {repo_path}")
        if chunk_size < 100:
            raise CommandError("--chunk-size must be >= 100")
        if chunk_overlap < 0:
            raise CommandError("--chunk-overlap must be >= 0")

        include_extensions = {ext if ext.startswith(".") else f".{ext}" for ext in include_ext} if include_ext else DEFAULT_EXTENSIONS

        try:
            stats = index_repository(
                repo_url=repo_url,
                repo_path=repo_path,
                allowed_repositories=settings.ALLOWED_SOURCE_REPOSITORIES,
                include_extensions=include_extensions,
                profile=profile,
                include_paths=include_path,
                exclude_paths=exclude_path,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                incremental=incremental,
                prune=prune,
                include_issues=include_issues,
                github_token=settings.GITHUB_API_TOKEN or None,
                github_verify_ssl=settings.GITHUB_API_VERIFY_SSL,
                github_ca_bundle=settings.GITHUB_CA_BUNDLE,
            )
        except ValueError as exc:
            raise CommandError(str(exc)) from exc

        # Emit summary lines so pipeline runners can capture run metrics from stdout.
        self.stdout.write(self.style.SUCCESS("Index build completed."))
        self.stdout.write(f"repo_url={repo_url}")
        self.stdout.write(f"repo_path={repo_path}")
        self.stdout.write(f"profile={profile}")
        self.stdout.write(f"incremental={incremental}")
        self.stdout.write(f"include_issues={include_issues}")
        self.stdout.write(f"scanned_files={stats.scanned_files}")
        self.stdout.write(f"skipped_files={stats.skipped_files}")
        self.stdout.write(f"created_chunks={stats.created_chunks}")
        self.stdout.write(f"updated_chunks={stats.updated_chunks}")
        self.stdout.write(f"deleted_chunks={stats.deleted_chunks}")
