from __future__ import annotations

from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from helpdesk.services.source_refresh import configured_sources, refresh_all_sources


class Command(BaseCommand):
    help = (
        "Fetch each configured standards repository (NeTEx, SIRI, OpRa) into the checkout "
        "directory and index it with its own profile. This is what the daily task runs."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--only",
            nargs="+",
            metavar="NAME",
            help="Refresh only these repositories (for example SIRI). Default: all.",
        )
        parser.add_argument(
            "--full",
            action="store_true",
            help=(
                "Index every file instead of only the changed ones. Use it once after the first "
                "checkout so existing chunks get the real commit SHA."
            ),
        )
        parser.add_argument(
            "--checkout-dir",
            default=None,
            help="Where the repositories are checked out (default: SOURCE_CHECKOUT_DIR).",
        )

    def handle(self, *args, **options):
        known = {source.name.lower(): source.name for source in configured_sources()}
        unknown = [name for name in (options["only"] or []) if name.lower() not in known]
        if unknown:
            raise CommandError(f"Unknown repository: {', '.join(unknown)}. Known: {', '.join(known.values())}")

        checkout_dir = Path(options["checkout_dir"]).expanduser() if options["checkout_dir"] else None
        result = refresh_all_sources(only=options["only"], full=options["full"], checkout_root=checkout_dir)

        for name, row in result["results"].items():
            if row["status"] == "ok":
                self.stdout.write(
                    f"{name}: ok {row['mode']} commit={row['commit'][:12]} scanned={row['scanned_files']} "
                    f"skipped={row['skipped_files']} created={row['created_chunks']} "
                    f"updated={row['updated_chunks']} deleted={row['deleted_chunks']} "
                    f"alias_removed={row.get('alias_chunks_removed', 0)} ({row['seconds']}s)"
                )
            else:
                self.stderr.write(f"{name}: FAILED {row['error']} ({row['seconds']}s)")

        if result["status"] == "skipped":
            self.stdout.write(self.style.WARNING("Skipped: another refresh is running."))
        elif result["status"] != "ok":
            raise CommandError(f"Source refresh {result['status']}.")
        else:
            self.stdout.write(self.style.SUCCESS("Source refresh completed."))
