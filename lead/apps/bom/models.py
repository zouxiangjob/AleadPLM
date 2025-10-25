import uuid
from decimal import Decimal

from django.db import models

from lead.apps.mparts.models import Mpart

class BomItem(models.Model):
    id = models.UUIDField(primary_key=True, unique=True, default=uuid.uuid4, editable=False)
    pid = models.ForeignKey(Mpart, related_name='bom_items', on_delete=models.CASCADE)
    cid = models.ForeignKey(Mpart, related_name='used_in_boms', on_delete=models.CASCADE)
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )

    def __str__(self):
        return f'{self.pid} -> {self.cid} x {self.quantity}'


