from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='first_name',
            field=models.CharField(max_length=150, blank=True, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='last_name',
            field=models.CharField(max_length=150, blank=True, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='specialty',
            field=models.CharField(max_length=255, blank=True, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='role',
            field=models.CharField(max_length=50, blank=True, null=True),
        ),
    ]

