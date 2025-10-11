import uuid

from django.db import models

from django.db import models

class Product(models.Model):
    id = models.UUIDField(primary_key=True, unique=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f'{self.code} - {self.name}'

class BomItem(models.Model):
    id = models.UUIDField(primary_key=True, unique=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, related_name='bom_items', on_delete=models.CASCADE)
    component = models.ForeignKey(Product, related_name='used_in_boms', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    parent = models.ForeignKey('self', null=True, blank=True, related_name='children', on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.product.code} -> {self.component.code} x{self.quantity}'
