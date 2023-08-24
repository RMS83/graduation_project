from django.core.management.base import BaseCommand
from order_app.models import Status


class Command(BaseCommand):
    """
        Class to arrange management command export_products.
    """
    help = 'import_status'
    def add_arguments(self, parser):
        """
        Entry point for subclassed commands to add custom arguments.
        """
        pass

    def handle(self, *args, **options):
        """
        Method to describe the actual logic of the command import_status.
        """
        status = ["Отменен", "Подтвержден", "Частично подтвержден", "Доставлен", "Частично доставлен"]

        try:
            for status in status:
                Status.objects.create(name=status)
            self.stdout.write("Import complite")
        except:
            self.stdout.write("ERROR")