import os
import time
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction, connection
from django.utils import timezone
import django_rq

from poi_manager.models import PointOfInterest, ImportBatch
from poi_manager.parsers.csv_parser import CSVParser
from poi_manager.parsers.json_parser import JSONParser
from poi_manager.parsers.xml_parser import XMLParser
from poi_manager.jobs import import_poi_file_async
from poi_manager.utils import get_file_type, format_duration

import logging

logger = logging.getLogger("poi_manager.import")


class Command(BaseCommand):
    help = "Import Point of Interest data from CSV, JSON, or XML files"

    def add_arguments(self, parser):
        parser.add_argument(
            "files", nargs="+", type=str, help="One or more file paths to import"
        )

        parser.add_argument(
            "--async",
            action="store_true",
            dest="run_async",
            help="Process files asynchronously using RQ",
        )

        parser.add_argument(
            "--batch-size",
            type=int,
            default=1000,
            help="Number of records to process in each batch (default: 1000)",
        )

        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear all existing POI data before import",
        )

        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Perform a dry run without saving data",
        )

        parser.add_argument(
            "--skip-duplicates",
            action="store_true",
            default=True,
            help="Skip duplicate records (based on external_id)",
        )

        parser.add_argument(
            "--update-existing",
            action="store_true",
            help="Update existing records instead of skipping",
        )

    def handle(self, *args, **options):
        files = options["files"]
        run_async = options.get("run_async", False)
        batch_size = options.get("batch_size", 1000)
        clear_existing = options.get("clear", False)
        dry_run = options.get("dry_run", False)

        for file_path in files:
            if not os.path.exists(file_path):
                raise CommandError(f"File not found: {file_path}")

            file_type = get_file_type(file_path)
            if not file_type:
                raise CommandError(f"Unsupported file type: {file_path}")

        if clear_existing and not dry_run:
            self.stdout.write("Clearing existing POI data...")
            count = PointOfInterest.objects.all().delete()[0]
            self.stdout.write(
                self.style.SUCCESS(f"Deleted {count} existing POI records")
            )

        if run_async:
            self.handle_async(files, options)
        else:
            self.handle_sync(files, options)

    def handle_sync(self, files, options):
        total_start = time.time()
        total_processed = 0
        total_failed = 0

        for file_path in files:
            self.stdout.write(f"\nProcessing: {file_path}")

            try:
                batch = ImportBatch.objects.create(
                    file_path=file_path,
                    file_name=os.path.basename(file_path),
                    file_type=get_file_type(file_path),
                    file_size=os.path.getsize(file_path),
                    status="processing",
                )

                processed, failed = self.process_file(file_path, batch, options)

                total_processed += processed
                total_failed += failed

                batch.mark_completed()

                self.stdout.write(
                    self.style.SUCCESS(
                        f"✓ Imported {processed} records "
                        f"({failed} failed) from {os.path.basename(file_path)}"
                    )
                )

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"✗ Error processing {file_path}: {e}")
                )
                if "batch" in locals():
                    batch.status = "failed"
                    batch.add_error(str(e))
                    batch.save()

        duration = time.time() - total_start
        self.stdout.write("\n" + "=" * 50)
        self.stdout.write(
            self.style.SUCCESS(
                f"Import complete!\n"
                f"Total records processed: {total_processed}\n"
                f"Total records failed: {total_failed}\n"
                f"Time taken: {format_duration(duration)}"
            )
        )

    def handle_async(self, files, options):
        queue = django_rq.get_queue("default")
        jobs = []

        for file_path in files:
            batch = ImportBatch.objects.create(
                file_path=file_path,
                file_name=os.path.basename(file_path),
                file_type=get_file_type(file_path),
                file_size=os.path.getsize(file_path),
                status="pending",
            )

            job = queue.enqueue(import_poi_file_async, batch.id, file_path, options)

            batch.job_id = job.id
            batch.save()

            jobs.append((batch, job))

            self.stdout.write(
                f"Queued: {os.path.basename(file_path)} " f"(Job ID: {job.id})"
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"\n{len(jobs)} file(s) queued for processing.\n"
                f"Monitor progress in Django Admin or check RQ logs."
            )
        )

    def process_file(self, file_path, batch, options):
        file_type = get_file_type(file_path)
        batch_size = options.get("batch_size", 1000)
        dry_run = options.get("dry_run", False)
        update_existing = options.get("update_existing", False)

        parser_class = {
            "csv": CSVParser,
            "json": JSONParser,
            "xml": XMLParser,
        }.get(file_type)

        if not parser_class:
            raise CommandError(f"No parser available for {file_type}")

        parser = parser_class(file_path, batch_size)

        processed = 0
        failed = 0
        skipped = 0

        for batch_data in parser.parse():
            if dry_run:
                processed += len(batch_data)
                self.stdout.write(f"  [DRY RUN] Would import {len(batch_data)} records")
                continue

            try:
                with transaction.atomic():
                    pois = []

                    for record in batch_data:
                        try:
                            if update_existing:
                                poi, created = PointOfInterest.objects.update_or_create(
                                    external_id=record["external_id"],
                                    defaults={
                                        "name": record["name"],
                                        "category": record["category"],
                                        "latitude": record["latitude"],
                                        "longitude": record["longitude"],
                                        "ratings": record["ratings"],
                                        "description": record.get("description", ""),
                                        "source_file": os.path.basename(file_path),
                                        "import_batch": batch,
                                    },
                                )
                                if not created:
                                    skipped += 1
                            else:
                                from django.contrib.gis.geos import Point

                                ratings_list = record["ratings"]
                                avg_rating = None
                                rating_count = 0
                                if ratings_list and len(ratings_list) > 0:
                                    avg_rating = sum(ratings_list) / len(ratings_list)
                                    rating_count = len(ratings_list)
                                
                                poi = PointOfInterest(
                                    external_id=record["external_id"],
                                    name=record["name"],
                                    category=record["category"],
                                    latitude=record["latitude"],
                                    longitude=record["longitude"],
                                    location=Point(
                                        record["longitude"], record["latitude"]
                                    ),
                                    ratings=record["ratings"],
                                    avg_rating=avg_rating,
                                    rating_count=rating_count,
                                    description=record.get("description", ""),
                                    source_file=os.path.basename(file_path),
                                    import_batch=batch,
                                )
                                pois.append(poi)

                            processed += 1

                        except Exception as e:
                            logger.error(f"Error creating POI record: {e}")
                            failed += 1
                            batch.add_error(str(e), record)

                    if pois and not update_existing:
                        PointOfInterest.objects.bulk_create(
                            pois, ignore_conflicts=True, batch_size=500
                        )

                    batch.records_processed = processed
                    batch.records_failed = failed
                    batch.records_skipped = skipped
                    batch.save()

                    if processed % 10000 == 0:
                        self.stdout.write(f"  Processed {processed} records...")

            except Exception as e:
                logger.error(f"Batch processing error: {e}")
                batch.add_error(f"Batch error: {e}")
                failed += len(batch_data)

        return processed, failed
