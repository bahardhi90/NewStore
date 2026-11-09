from django.db import migrations

from apps.notifications.events import SPECS


def seed(apps, schema_editor):
    SmsSettings = apps.get_model("notifications", "SmsSettings")
    SmsTemplate = apps.get_model("notifications", "SmsTemplate")
    SmsSettings.objects.get_or_create(pk=1)
    for event, spec in SPECS.items():
        SmsTemplate.objects.get_or_create(
            event=str(event), defaults={"text": spec.default_text, "is_active": spec.default_active}
        )


class Migration(migrations.Migration):
    dependencies = [("notifications", "0001_initial")]

    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
