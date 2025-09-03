from django.contrib.postgres.operations import TrigramExtension, BtreeGinExtension
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("poi_manager", "0002_add_processing_time"),
    ]

    operations = [
        TrigramExtension(),
        BtreeGinExtension(),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS poi_category_rating_idx ON poi_manager_pointofinterest(category, avg_rating DESC NULLS LAST);",
            reverse_sql="DROP INDEX IF EXISTS poi_category_rating_idx;",
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS poi_name_trgm_idx ON poi_manager_pointofinterest USING gin(name gin_trgm_ops);",
            reverse_sql="DROP INDEX IF EXISTS poi_name_trgm_idx;",
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS poi_name_category_idx ON poi_manager_pointofinterest(lower(name), category);",
            reverse_sql="DROP INDEX IF EXISTS poi_name_category_idx;",
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS poi_rating_idx ON poi_manager_pointofinterest(avg_rating DESC NULLS LAST) WHERE avg_rating IS NOT NULL;",
            reverse_sql="DROP INDEX IF EXISTS poi_rating_idx;",
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS poi_spatial_idx ON poi_manager_pointofinterest USING gist(location) WHERE location IS NOT NULL;",
            reverse_sql="DROP INDEX IF EXISTS poi_spatial_idx;",
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS poi_category_count_idx ON poi_manager_pointofinterest(category) INCLUDE (id);",
            reverse_sql="DROP INDEX IF EXISTS poi_category_count_idx;",
            hints={"model": "PointOfInterest"},
        ),
        migrations.RunSQL(
            "CLUSTER poi_manager_pointofinterest USING poi_manager_pointofinterest_pkey;",
            reverse_sql="",
        ),
        migrations.RunSQL("ANALYZE poi_manager_pointofinterest;", reverse_sql=""),
    ]
