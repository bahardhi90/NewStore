from django.db import migrations


def seed(apps, schema_editor):
    apps.get_model("content", "SiteSettings").objects.get_or_create(pk=1)


class Migration(migrations.Migration):
    dependencies = [("content", "0002_sitesettings")]

    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
