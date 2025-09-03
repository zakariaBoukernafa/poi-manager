import os
from django.test import TestCase

from poi_manager.parsers.csv_parser import CSVParser
from poi_manager.parsers.json_parser import JSONParser
from poi_manager.parsers.xml_parser import XMLParser


class ParsersTestCase(TestCase):
    
    def setUp(self):
        self.fixtures_dir = os.path.join(
            os.path.dirname(__file__),
            'fixtures'
        )
    
    def test_csv_parser_parse(self):
        """Test CSV parser can parse real data format"""
        csv_file = os.path.join(self.fixtures_dir, 'test_pois.csv')
        parser = CSVParser(csv_file)
        
        # Parse the file
        all_records = []
        for batch in parser.parse():
            all_records.extend(batch)
        
        # Verify we parsed all 5 records
        self.assertEqual(len(all_records), 5)
        self.assertEqual(parser.records_processed, 5)
        
        # Check first record
        first = all_records[0]
        self.assertEqual(first['external_id'], '1806848972')
        self.assertEqual(first['name'], 'Central Park')
        self.assertEqual(first['category'], 'park')
        self.assertAlmostEqual(float(first['latitude']), 40.785091, places=5)
        self.assertAlmostEqual(float(first['longitude']), -73.968285, places=5)
        # Check ratings were parsed from PostgreSQL array format
        self.assertIsInstance(first['ratings'], list)
        self.assertTrue(len(first['ratings']) > 0)
    
    def test_json_parser_parse(self):
        """Test JSON parser can parse real data format"""
        json_file = os.path.join(self.fixtures_dir, 'test_pois.json')
        parser = JSONParser(json_file)
        
        # Parse the file
        all_records = []
        for batch in parser.parse():
            all_records.extend(batch)
        
        # Verify we parsed all 5 records
        self.assertEqual(len(all_records), 5)
        self.assertEqual(parser.records_processed, 5)
        
        # Check first record
        first = all_records[0]
        self.assertEqual(first['external_id'], '1806848972')
        self.assertEqual(first['name'], 'Central Park')
        self.assertEqual(first['category'], 'park')
        self.assertAlmostEqual(float(first['latitude']), 40.785091, places=5)
        self.assertAlmostEqual(float(first['longitude']), -73.968285, places=5)
        self.assertTrue(first['description'])  # Has description
        # Check ratings array
        self.assertIsInstance(first['ratings'], list)
        self.assertEqual(len(first['ratings']), 10)
    
    def test_xml_parser_parse(self):
        """Test XML parser can parse real data format"""
        xml_file = os.path.join(self.fixtures_dir, 'test_pois.xml')
        parser = XMLParser(xml_file)
        
        # Parse the file
        all_records = []
        for batch in parser.parse():
            all_records.extend(batch)
        
        # Verify we parsed all 5 records
        self.assertEqual(len(all_records), 5)
        self.assertEqual(parser.records_processed, 5)
        
        # Check first record
        first = all_records[0]
        self.assertEqual(first['external_id'], '146612179')
        self.assertEqual(first['name'], 'Central Park')
        self.assertEqual(first['category'], 'park')
        self.assertAlmostEqual(float(first['latitude']), 40.785091, places=5)
        self.assertAlmostEqual(float(first['longitude']), -73.968285, places=5)
        # Check ratings were parsed from comma-separated format
        self.assertIsInstance(first['ratings'], list)
        self.assertTrue(len(first['ratings']) > 0)