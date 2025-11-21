from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_add_profile_fields'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='role',
        ),
    ]

