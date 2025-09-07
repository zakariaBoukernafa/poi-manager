from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("poi_manager", "0001_initial"),
    ]

    operations = [
        migrations.RunSQL(
            sql=(
                "CREATE EXTENSION IF NOT EXISTS postgis;\n"
                "CREATE EXTENSION IF NOT EXISTS pg_trgm;\n"
            ),
            reverse_sql=(
                # Do not drop extensions on reverse to avoid breaking shared DBs
                ""
            ),
        ),
    ]

