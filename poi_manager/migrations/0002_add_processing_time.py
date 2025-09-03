from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("poi_manager", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="importbatch",
            name="processing_time",
            field=models.DurationField(
                blank=True, null=True, verbose_name="Processing Time"
            ),
        ),
    ]
