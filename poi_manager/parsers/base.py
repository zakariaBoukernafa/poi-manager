import chardet
import os
from abc import ABC, abstractmethod
from typing import Generator, Dict, List, Any
import logging

logger = logging.getLogger("poi_manager.parsers")


class BaseParser(ABC):

    def __init__(self, file_path: str, batch_size: int = 1000):
        self.file_path = file_path
        self.batch_size = batch_size
        self.file_size = os.path.getsize(file_path)
        self.encoding = None
        self.records_processed = 0
        self.errors = []

    def detect_encoding(self) -> str:
        if self.encoding:
            return self.encoding

        with open(self.file_path, "rb") as f:
            raw_data = f.read(10240)
            result = chardet.detect(raw_data)

        self.encoding = result.get("encoding", "utf-8")
        confidence = result.get("confidence", 0)

        logger.info(
            f"Detected encoding: {self.encoding} (confidence: {confidence:.2%})"
        )

        if confidence < 0.7:
            logger.warning(f"Low confidence in encoding detection, using utf-8")
            self.encoding = "utf-8"

        return self.encoding

    @abstractmethod
    def parse(self) -> Generator[List[Dict[str, Any]], None, None]:
        pass

    def validate_record(self, record: Dict[str, Any]) -> bool:
        required_fields = ["id", "name", "latitude", "longitude", "category"]

        for field in required_fields:
            if field not in record or record[field] is None:
                logger.warning(f"Record missing required field: {field}")
                return False

        try:
            lat = float(record["latitude"])
            lon = float(record["longitude"])

            if not (-90 <= lat <= 90):
                logger.warning(f"Invalid latitude: {lat}")
                return False

            if not (-180 <= lon <= 180):
                logger.warning(f"Invalid longitude: {lon}")
                return False
        except (ValueError, TypeError) as e:
            logger.warning(f"Invalid coordinates: {e}")
            return False

        return True

    def normalize_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        normalized = {
            "external_id": str(record.get("id", "")),
            "name": self.clean_string(record.get("name", "")),
            "category": self.clean_string(record.get("category", "")),
            "latitude": float(record.get("latitude", 0)),
            "longitude": float(record.get("longitude", 0)),
            "ratings": self.parse_ratings(record.get("ratings", [])),
            "description": self.clean_string(record.get("description", "")),
        }

        return normalized

    def clean_string(self, value: Any) -> str:
        if value is None:
            return ""

        value = str(value)
        value = value.replace("\x00", "")
        value = " ".join(value.split())
        return value[:500]

    def parse_ratings(self, ratings_data: Any) -> List[float]:
        if isinstance(ratings_data, list):
            return [float(r) for r in ratings_data if r is not None]

        if isinstance(ratings_data, str):
            ratings_str = ratings_data.strip("{}[]")
            if ratings_str:
                try:
                    return [float(r.strip()) for r in ratings_str.split(",")]
                except ValueError:
                    logger.warning(f"Could not parse ratings: {ratings_data}")
                    return []

        return []
