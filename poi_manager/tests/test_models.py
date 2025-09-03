from decimal import Decimal
from django.test import TestCase
from django.utils import timezone

from poi_manager.models import ImportBatch, PointOfInterest


class ImportBatchTestCase(TestCase):
    
    def test_create_import_batch(self):
        """Test creating an import batch"""
        batch = ImportBatch.objects.create(
            file_path='/test/data.csv',
            file_name='data.csv',
            file_type='csv'
        )
        self.assertEqual(batch.status, 'pending')
        self.assertEqual(batch.records_processed, 0)
    
    def test_mark_completed(self):
        """Test marking batch as completed"""
        batch = ImportBatch.objects.create(
            file_path='/test/data.csv',
            file_name='data.csv',
            file_type='csv'
        )
        batch.mark_completed()
        
        self.assertEqual(batch.status, 'completed')
        self.assertIsNotNone(batch.completed_at)
        self.assertIsNotNone(batch.processing_time)
    
    def test_mark_completed_with_errors(self):
        """Test marking batch with errors shows partial status"""
        batch = ImportBatch.objects.create(
            file_path='/test/data.csv',
            file_name='data.csv',
            file_type='csv',
            records_failed=5
        )
        batch.mark_completed()
        
        self.assertEqual(batch.status, 'partial')
    
    def test_add_error(self):
        """Test adding error to batch"""
        batch = ImportBatch.objects.create(
            file_path='/test/data.csv',
            file_name='data.csv',
            file_type='csv'
        )
        batch.add_error('Test error', {'id': 'TEST001'})
        
        self.assertEqual(batch.records_failed, 1)
        self.assertIn('errors', batch.error_log)
        self.assertEqual(len(batch.error_log['errors']), 1)


class PointOfInterestTestCase(TestCase):
    
    def setUp(self):
        self.batch = ImportBatch.objects.create(
            file_path='/test/data.csv',
            file_name='data.csv',
            file_type='csv'
        )
    
    def test_create_poi(self):
        """Test creating a POI"""
        poi = PointOfInterest(
            external_id='POI001',
            name='Test Location',
            category='restaurant',
            latitude=Decimal('40.7128'),
            longitude=Decimal('-74.0060'),
            source_file='test.csv',
            import_batch=self.batch
        )
        poi.clean()  # This creates the location from lat/lon
        poi.save()
        
        self.assertEqual(poi.name, 'Test Location')
        self.assertIsNotNone(poi.location)
    
    def test_poi_rating_calculation(self):
        """Test automatic average rating calculation"""
        poi = PointOfInterest(
            external_id='POI002',
            name='Test Restaurant',
            category='restaurant',
            latitude=Decimal('40.7128'),
            longitude=Decimal('-74.0060'),
            ratings=[4.0, 5.0, 3.0],
            source_file='test.csv',
            import_batch=self.batch
        )
        poi.clean()
        poi.save()
        
        self.assertEqual(poi.avg_rating, 4.0)
        self.assertEqual(poi.rating_count, 3)
    
    def test_poi_location_from_coordinates(self):
        """Test location point is created from lat/lon"""
        poi = PointOfInterest(
            external_id='POI003',
            name='Test Place',
            category='park',
            latitude=Decimal('40.7128'),
            longitude=Decimal('-74.0060'),
            source_file='test.csv',
            import_batch=self.batch
        )
        poi.clean()
        poi.save()
        
        self.assertIsNotNone(poi.location)
        self.assertAlmostEqual(poi.location.y, 40.7128, places=4)
        self.assertAlmostEqual(poi.location.x, -74.0060, places=4)