# Generated by Django 4.2.15 on 2025-04-07 19:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('club_dashboard', '0013_rename_time_salonappointment_start_time_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='salonappointment',
            name='start_time',
            field=models.TimeField(blank=True, null=True),
        ),
    ]
