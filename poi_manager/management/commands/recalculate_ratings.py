from django.core.management.base import BaseCommand
from django.db import transaction
from poi_manager.models import PointOfInterest


class Command(BaseCommand):
    help = "Recalculate average ratings and rating counts for all POIs"

    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-size',
            type=int,
            default=1000,
            help='Number of records to process in each batch'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes'
        )

    def handle(self, *args, **options):
        batch_size = options['batch_size']
        dry_run = options['dry_run']
        
        pois_to_update = PointOfInterest.objects.filter(
            ratings__isnull=False
        ).exclude(
            ratings=[]
        ).filter(
            avg_rating__isnull=True
        )
        
        total = pois_to_update.count()
        self.stdout.write(f"Found {total} POIs with uncalculated ratings")
        
        if dry_run:
            self.stdout.write("DRY RUN - No changes will be made")
            sample = pois_to_update[:5]
            for poi in sample:
                if poi.ratings:
                    avg = sum(poi.ratings) / len(poi.ratings)
                    count = len(poi.ratings)
                    self.stdout.write(
                        f"  Would update {poi.external_id}: "
                        f"avg={avg:.2f}, count={count}"
                    )
            return
        
        updated = 0
        
        for i in range(0, total, batch_size):
            batch = pois_to_update[i:i+batch_size]
            
            with transaction.atomic():
                for poi in batch:
                    if poi.ratings:
                        poi.avg_rating = sum(poi.ratings) / len(poi.ratings)
                        poi.rating_count = len(poi.ratings)
                        poi.save(update_fields=['avg_rating', 'rating_count'])
                        updated += 1
            
            if updated % 10000 == 0:
                self.stdout.write(f"Processed {updated}/{total} POIs...")
        
        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully updated {updated} POIs with calculated ratings"
            )
        )
        
        sample_pois = PointOfInterest.objects.filter(
            avg_rating__isnull=False
        )[:5]
        
        self.stdout.write("\nSample updated POIs:")
        for poi in sample_pois:
            self.stdout.write(
                f"  {poi.name}: avg={poi.avg_rating:.2f}, count={poi.rating_count}"
            )