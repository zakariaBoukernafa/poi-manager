import json
import ijson
from typing import Generator, List, Dict, Any
import logging

from .base import BaseParser

logger = logging.getLogger("poi_manager.parsers.json")


class JSONParser(BaseParser):

    def parse(self) -> Generator[List[Dict[str, Any]], None, None]:
        encoding = self.detect_encoding()
        batch = []

        try:
            with open(self.file_path, "rb") as f:
                parser = ijson.items(f, "item")

                for item in parser:
                    try:
                        coords = item.get("coordinates", {})
                        record = {
                            "id": item.get("id"),
                            "name": item.get("name"),
                            "category": item.get("category"),
                            "latitude": coords.get("latitude"),
                            "longitude": coords.get("longitude"),
                            "ratings": item.get("ratings"),
                            "description": item.get("description"),
                        }

                        if self.validate_record(record):
                            normalized = self.normalize_record(record)
                            batch.append(normalized)
                            self.records_processed += 1

                            if len(batch) >= self.batch_size:
                                yield batch
                                batch = []
                        else:
                            logger.warning(
                                f"Skipping invalid JSON record: {item.get('id')}"
                            )

                    except Exception as e:
                        logger.error(f"Error processing JSON item: {e}")
                        self.errors.append(
                            {"item_id": item.get("id"), "error": str(e), "data": item}
                        )

                if batch:
                    yield batch

        except ijson.JSONError:
            logger.info("Streaming failed, attempting standard JSON parsing")
            with open(self.file_path, "r", encoding=encoding) as f:
                try:
                    data = json.load(f)
                    if not isinstance(data, list):
                        logger.error(
                            "JSON file does not contain an array at root level"
                        )
                        raise ValueError("Expected JSON array at root level")

                    for item in data:
                        try:
                            coords = item.get("coordinates", {})
                            record = {
                                "id": item.get("id"),
                                "name": item.get("name"),
                                "category": item.get("category"),
                                "latitude": coords.get("latitude"),
                                "longitude": coords.get("longitude"),
                                "ratings": item.get("ratings"),
                                "description": item.get("description"),
                            }

                            if self.validate_record(record):
                                normalized = self.normalize_record(record)
                                batch.append(normalized)
                                self.records_processed += 1

                                if len(batch) >= self.batch_size:
                                    yield batch
                                    batch = []

                        except Exception as e:
                            logger.error(f"Error processing JSON item: {e}")
                            self.errors.append(
                                {
                                    "item_id": item.get("id"),
                                    "error": str(e),
                                    "data": item,
                                }
                            )

                    if batch:
                        yield batch

                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON file: {e}")
                    raise

        except Exception as e:
            logger.error(f"Fatal error parsing JSON file: {e}")
            raise

        logger.info(
            f"JSON parsing complete. Processed {self.records_processed} records"
        )
