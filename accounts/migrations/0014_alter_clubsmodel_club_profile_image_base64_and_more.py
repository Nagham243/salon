# Generated by Django 4.2.15 on 2025-02-18 12:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0013_otp'),
    ]

    operations = [
        migrations.AlterField(
            model_name='clubsmodel',
            name='club_profile_image_base64',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='profile_image_base64',
            field=models.TextField(blank=True, null=True),
        ),
    ]
