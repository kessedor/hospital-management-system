# Generated by Django 5.1.3 on 2024-12-17 14:01

import datetime
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0001_initial'),
        ('patient_management', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AnalyticsData',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('total_appointments', models.IntegerField(default=0)),
                ('completed_appointments', models.IntegerField(default=0)),
                ('cancelled_appointments', models.IntegerField(default=0)),
                ('new_patients', models.IntegerField(default=0)),
                ('active_admissions', models.IntegerField(default=0)),
                ('discharged_patients', models.IntegerField(default=0)),
                ('average_stay_duration', models.DurationField(blank=True, null=True)),
                ('department_stats', models.JSONField(default=dict)),
                ('bed_occupancy_rate', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
            ],
            options={
                'ordering': ['-date'],
            },
        ),
        migrations.CreateModel(
            name='Appointment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('appointment_datetime', models.DateTimeField()),
                ('duration', models.DurationField(default=datetime.timedelta(seconds=1800))),
                ('appointment_type', models.CharField(max_length=50)),
                ('status', models.CharField(choices=[('SCHEDULED', 'Scheduled'), ('CONFIRMED', 'Confirmed'), ('CANCELLED', 'Cancelled'), ('COMPLETED', 'Completed'), ('NO_SHOW', 'No Show')], default='SCHEDULED', max_length=20)),
                ('reason', models.TextField()),
                ('notes', models.TextField(blank=True, null=True)),
                ('reminder_sent', models.BooleanField(default=False)),
            ],
            options={
                'ordering': ['appointment_datetime'],
            },
        ),
        migrations.CreateModel(
            name='LabResult',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('test_name', models.CharField(max_length=100)),
                ('test_category', models.CharField(max_length=50)),
                ('result_value', models.CharField(max_length=100)),
                ('reference_range', models.CharField(blank=True, max_length=100, null=True)),
                ('unit', models.CharField(blank=True, max_length=20, null=True)),
                ('status', models.CharField(choices=[('PENDING', 'Pending'), ('COMPLETED', 'Completed'), ('CANCELLED', 'Cancelled')], default='PENDING', max_length=20)),
                ('performed_date', models.DateTimeField(auto_now_add=True)),
                ('report_file', models.FileField(blank=True, null=True, upload_to='lab_reports/')),
                ('notes', models.TextField(blank=True, null=True)),
            ],
            options={
                'ordering': ['-performed_date'],
            },
        ),
        migrations.AddField(
            model_name='medicalrecord',
            name='attachments',
            field=models.FileField(blank=True, help_text='Upload relevant documents (max 10MB)', null=True, upload_to='medical_records/'),
        ),
        migrations.AddField(
            model_name='medicalrecord',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=datetime.datetime(2024, 12, 17, 14, 1, 16, 202552, tzinfo=datetime.timezone.utc)),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='medicalrecord',
            name='created_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='records_created', to='authentication.staff'),
        ),
        migrations.AddField(
            model_name='medicalrecord',
            name='follow_up_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='medicalrecord',
            name='follow_up_notes',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='medicalrecord',
            name='height',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True),
        ),
        migrations.AddField(
            model_name='medicalrecord',
            name='hospital',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='hospital_records', to='authentication.hospital'),
        ),
        migrations.AddField(
            model_name='medicalrecord',
            name='lab_results',
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='medicalrecord',
            name='oxygen_saturation',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='medicalrecord',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name='medicalrecord',
            name='weight',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True),
        ),
        migrations.AddIndex(
            model_name='medicalrecord',
            index=models.Index(fields=['-date'], name='patient_man_date_2349dc_idx'),
        ),
        migrations.AddIndex(
            model_name='medicalrecord',
            index=models.Index(fields=['patient', '-date'], name='patient_man_patient_d67b0d_idx'),
        ),
        migrations.AddField(
            model_name='analyticsdata',
            name='hospital',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='analytics', to='authentication.hospital'),
        ),
        migrations.AddField(
            model_name='appointment',
            name='doctor',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='doctor_appointments', to='authentication.staff'),
        ),
        migrations.AddField(
            model_name='appointment',
            name='hospital',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='hospital_appointments', to='authentication.hospital'),
        ),
        migrations.AddField(
            model_name='appointment',
            name='patient',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='appointments', to='authentication.patient'),
        ),
        migrations.AddField(
            model_name='labresult',
            name='medical_record',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='detailed_lab_results', to='patient_management.medicalrecord'),
        ),
        migrations.AddField(
            model_name='labresult',
            name='performed_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='lab_tests_performed', to='authentication.staff'),
        ),
        migrations.AddIndex(
            model_name='analyticsdata',
            index=models.Index(fields=['hospital', '-date'], name='patient_man_hospita_ebfc42_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='analyticsdata',
            unique_together={('hospital', 'date')},
        ),
        migrations.AddIndex(
            model_name='appointment',
            index=models.Index(fields=['appointment_datetime'], name='patient_man_appoint_f755c7_idx'),
        ),
        migrations.AddIndex(
            model_name='appointment',
            index=models.Index(fields=['status'], name='patient_man_status_7ae63a_idx'),
        ),
    ]
