import os
from django.test import TestCase
from django.core.management import call_command
from django.core.management.base import CommandError
from io import StringIO

from poi_manager.models import ImportBatch


class ImportPOIsCommandTestCase(TestCase):
    
    def setUp(self):
        self.fixtures_dir = os.path.join(
            os.path.dirname(__file__),
            'fixtures'
        )
    
    def test_import_command_creates_batch(self):
        """Test import command creates an import batch"""
        csv_file = os.path.join(self.fixtures_dir, 'test_pois.csv')
        out = StringIO()
        
        # Import command will parse but may not import due to field mapping
        call_command('import_pois', csv_file, stdout=out, stderr=StringIO())
        
        # Check batch was created
        self.assertEqual(ImportBatch.objects.count(), 1)
        batch = ImportBatch.objects.first()
        self.assertEqual(batch.file_type, 'csv')
    
    def test_import_command_invalid_file(self):
        """Test import command with non-existent file"""
        with self.assertRaises(CommandError):
            call_command('import_pois', '/non/existent/file.csv')