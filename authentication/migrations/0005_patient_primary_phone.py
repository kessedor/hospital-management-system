# Generated by Django 5.1.3 on 2025-01-06 22:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0004_hospital_email_hospital_phone_number'),
    ]

    operations = [
        migrations.AddField(
            model_name='patient',
            name='primary_phone',
            field=models.CharField(blank=True, default='', max_length=15),
        ),
    ]
