import csv
from typing import Generator, List, Dict, Any
import logging

from .base import BaseParser

logger = logging.getLogger("poi_manager.parsers.csv")


class CSVParser(BaseParser):

    def parse(self) -> Generator[List[Dict[str, Any]], None, None]:
        encoding = self.detect_encoding()
        batch = []

        try:
            with open(self.file_path, "r", encoding=encoding, errors="replace") as f:
                reader = csv.DictReader(f)

                for row_num, row in enumerate(reader, start=2):
                    try:
                        row = {k: v for k, v in row.items() if k and k.strip()}
                        record = {
                            "id": row.get("poi_id"),
                            "name": row.get("poi_name"),
                            "category": row.get("poi_category"),
                            "latitude": row.get("poi_latitude"),
                            "longitude": row.get("poi_longitude"),
                            "ratings": row.get("poi_ratings"),
                        }

                        if self.validate_record(record):
                            normalized = self.normalize_record(record)
                            batch.append(normalized)
                            self.records_processed += 1

                            if len(batch) >= self.batch_size:
                                yield batch
                                batch = []
                        else:
                            logger.warning(f"Skipping invalid record at row {row_num}")

                    except Exception as e:
                        logger.error(f"Error processing row {row_num}: {e}")
                        self.errors.append(
                            {"row": row_num, "error": str(e), "data": row}
                        )

                if batch:
                    yield batch

        except Exception as e:
            logger.error(f"Fatal error parsing CSV file: {e}")
            raise

        logger.info(f"CSV parsing complete. Processed {self.records_processed} records")
