import logging
import os
from django.db import transaction
from django.contrib.gis.geos import Point

from poi_manager.models import PointOfInterest, ImportBatch
from poi_manager.parsers.csv_parser import CSVParser
from poi_manager.parsers.json_parser import JSONParser
from poi_manager.parsers.xml_parser import XMLParser
from poi_manager.utils import get_file_type

logger = logging.getLogger("poi_manager.jobs")


def import_poi_file_async(batch_id, file_path, options=None):
    options = options or {}

    try:
        batch = ImportBatch.objects.get(id=batch_id)
        batch.status = "processing"
        batch.save()

        logger.info(f"Starting async import for {file_path}")

        file_type = get_file_type(file_path)
        parser_class = {
            "csv": CSVParser,
            "json": JSONParser,
            "xml": XMLParser,
        }.get(file_type)

        if not parser_class:
            raise ValueError(f"Unsupported file type: {file_type}")

        batch_size = options.get("batch_size", 1000)
        parser = parser_class(file_path, batch_size)

        processed = 0
        failed = 0

        for batch_num, batch_data in enumerate(parser.parse(), 1):
            try:
                with transaction.atomic():
                    pois = []

                    for record in batch_data:
                        try:
                            poi = PointOfInterest(
                                external_id=record["external_id"],
                                name=record["name"],
                                category=record["category"],
                                latitude=record["latitude"],
                                longitude=record["longitude"],
                                location=Point(record["longitude"], record["latitude"]),
                                ratings=record["ratings"],
                                description=record.get("description", ""),
                                source_file=os.path.basename(file_path),
                                import_batch=batch,
                            )
                            pois.append(poi)

                        except Exception as e:
                            logger.error(f"Error creating POI: {e}")
                            failed += 1
                            batch.add_error(str(e), record)

                    if pois:
                        created = PointOfInterest.objects.bulk_create(
                            pois, ignore_conflicts=True, batch_size=500
                        )
                        processed += len(created)

                    batch.records_processed = processed
                    batch.records_failed = failed
                    batch.save()

                    logger.info(f"Batch {batch_num}: Processed {len(pois)} records")

            except Exception as e:
                logger.error(f"Batch processing error: {e}")
                batch.add_error(f"Batch {batch_num} error: {e}")
                failed += len(batch_data)

        batch.mark_completed()

        logger.info(f"Import complete: {processed} processed, {failed} failed")

        return {
            "status": "completed",
            "processed": processed,
            "failed": failed,
            "batch_id": str(batch_id),
        }

    except ImportBatch.DoesNotExist:
        logger.error(f"ImportBatch {batch_id} not found")
        raise

    except Exception as e:
        logger.error(f"Import job failed: {e}")

        if "batch" in locals():
            batch.status = "failed"
            batch.add_error(f"Job failed: {e}")
            batch.save()

        raise


