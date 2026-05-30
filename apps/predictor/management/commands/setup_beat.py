from django.core.management.base import BaseCommand
from django_celery_beat.models import CrontabSchedule, PeriodicTask


class Command(BaseCommand):
    help = "Create Celery Beat periodic task for weekly retrain"

    def handle(self, *args, **options):
        schedule, _ = CrontabSchedule.objects.get_or_create(
            minute="0",
            hour="0",
            day_of_week="sun",
            day_of_month="*",
            month_of_year="*",
            timezone="Asia/Jakarta",
        )

        task, created = PeriodicTask.objects.update_or_create(
            name="Weekly IHSG Retrain",
            defaults={
                "crontab": schedule,
                "task": "apps.predictor.tasks.retrain_pipeline",
                "enabled": True,
            },
        )

        if created:
            self.stdout.write(
                self.style.SUCCESS("Created weekly retrain schedule (Sun 00:00 WIB)")
            )
        else:
            self.stdout.write(
                self.style.SUCCESS("Updated weekly retrain schedule (Sun 00:00 WIB)")
            )
