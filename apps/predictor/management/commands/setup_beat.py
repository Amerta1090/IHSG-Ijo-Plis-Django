from django.core.management.base import BaseCommand
from django_celery_beat.models import CrontabSchedule, PeriodicTask


class Command(BaseCommand):
    help = "Create Celery Beat periodic tasks for weekly retrain"

    def handle(self, *args, **options):
        # IHSG: Sunday 00:00 WIB
        ihsg_schedule, _ = CrontabSchedule.objects.get_or_create(
            minute="0",
            hour="0",
            day_of_week="sun",
            day_of_month="*",
            month_of_year="*",
            timezone="Asia/Jakarta",
        )
        ihsg_task, ihsg_created = PeriodicTask.objects.update_or_create(
            name="Weekly IHSG Retrain",
            defaults={
                "crontab": ihsg_schedule,
                "task": "apps.predictor.tasks.retrain_pipeline",
                "enabled": True,
            },
        )
        if ihsg_created:
            self.stdout.write(
                self.style.SUCCESS("Created IHSG retrain schedule (Sun 00:00 WIB)")
            )
        else:
            self.stdout.write(
                self.style.SUCCESS("Updated IHSG retrain schedule (Sun 00:00 WIB)")
            )

        # USD/IDR: Sunday 01:00 WIB (offset from IHSG to avoid resource contention)
        usdidr_schedule, _ = CrontabSchedule.objects.get_or_create(
            minute="0",
            hour="1",
            day_of_week="sun",
            day_of_month="*",
            month_of_year="*",
            timezone="Asia/Jakarta",
        )
        usdidr_task, usdidr_created = PeriodicTask.objects.update_or_create(
            name="Weekly USD/IDR Retrain",
            defaults={
                "crontab": usdidr_schedule,
                "task": "apps.predictor.tasks.retrain_usdidr_pipeline",
                "enabled": True,
            },
        )
        if usdidr_created:
            self.stdout.write(
                self.style.SUCCESS("Created USD/IDR retrain schedule (Sun 01:00 WIB)")
            )
        else:
            self.stdout.write(
                self.style.SUCCESS("Updated USD/IDR retrain schedule (Sun 01:00 WIB)")
            )
