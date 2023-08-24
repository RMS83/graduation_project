import yaml
from django.core.management.base import BaseCommand
from order_app.models import Category, Stock, Vendor


class Command(BaseCommand):
    """
        Class to arrange management command export_products.
    """
    help = 'export_products'
    def add_arguments(self, parser):
        """
        Entry point for subclassed commands to add custom arguments.
        """
        pass

    def handle(self, *args, **options):
        """
        Method to describe the actual logic of the command export_products.
        """

        result = {'categories': [],
                  'vendors': [],
                  'products': []}
        for category in Category.objects.all():
            result['categories'].append({'id': category.id,
                                         'name': category.name,
                                         'description': category.description})
        for vendor in Vendor.objects.all():
            result['vendors'].append({'id': vendor.id, 'name': vendor.vendor_name, 'accepting_orders': vendor.accepting_orders})

        for stock in Stock.objects.all().\
                prefetch_related('product_characteristics', 'product_characteristics__characteristic').\
                select_related('product', 'product__category', 'vendor'):
            parameters = {}
            for parameter in stock.product_characteristics.all():
                parameters[parameter.characteristic.name] = parameter.value

            result['products'].append({'id': stock.id,
                                    'category': stock.product.category.id,
                                    'model': stock.model,
                                    'name': stock.product.name,
                                    'vendor': stock.vendor.id,
                                    'price': float('{:.2f}'.format(stock.price)),
                                    'price_rrc': float('{:.2f}'.format(stock.price_rrc)),
                                    'quantity': stock.quantity,
                                    'characteristics': parameters})
        with open('export.yml', 'w', encoding='utf8') as outfile:
            yaml.dump(result, outfile, allow_unicode=True, default_flow_style=False)
            self.stdout.write("Export complite")