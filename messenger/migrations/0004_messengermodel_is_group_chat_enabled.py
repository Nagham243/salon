# Generated by Django 4.2.15 on 2025-04-12 05:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('messenger', '0003_alter_blockusermodel_creator_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='messengermodel',
            name='is_group_chat_enabled',
            field=models.BooleanField(default=True, verbose_name='تفعيل الدردشة الجماعية'),
        ),
    ]
