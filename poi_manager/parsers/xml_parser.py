from lxml import etree
from typing import Generator, List, Dict, Any
import logging

from .base import BaseParser

logger = logging.getLogger("poi_manager.parsers.xml")


class XMLParser(BaseParser):

    def parse(self) -> Generator[List[Dict[str, Any]], None, None]:
        batch = []

        try:
            context = etree.iterparse(
                self.file_path, events=("start", "end")
            )
            context = iter(context)

            for event, elem in context:
                if event == "end" and elem.tag in ["DATA_RECORD", "poi"]:
                    try:
                        record = {
                            "id": self.get_text(elem, "pid"),
                            "name": self.get_text(elem, "pname"),
                            "category": self.get_text(elem, "pcategory"),
                            "latitude": self.get_text(elem, "platitude"),
                            "longitude": self.get_text(elem, "plongitude"),
                            "ratings": self.get_text(elem, "pratings"),
                            "description": self.get_text(elem, "description"),
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
                                f"Skipping invalid XML record: {record.get('id')}"
                            )

                        elem.clear()
                        while elem.getprevious() is not None:
                            del elem.getparent()[0]

                    except Exception as e:
                        logger.error(f"Error processing XML element: {e}")
                        self.errors.append(
                            {
                                "error": str(e),
                                "element": etree.tostring(elem, encoding="unicode"),
                            }
                        )

            if batch:
                yield batch

        except Exception as e:
            logger.error(f"Fatal error parsing XML file: {e}")
            raise

        logger.info(f"XML parsing complete. Processed {self.records_processed} records")

    def get_text(self, element, tag):
        child = element.find(tag)
        if child is not None and child.text:
            return child.text.strip()
        return None

