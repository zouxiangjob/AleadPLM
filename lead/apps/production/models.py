import shortuuid
from decimal import Decimal
from django.db import models





class Mpart(models.Model):
    id = models.CharField(primary_key=True, unique=True,default=shortuuid.uuid, editable=False)
    code = models.CharField(max_length=200)
    name = models.CharField(max_length=200)
    unit = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=5, decimal_places=1)
    created_time = models.DateField(auto_now_add=True)
    file = models.FileField(upload_to='files/', blank=False,null=True)

    def __str__(self):
        return self.title

class Files(models.Model):
    id = models.CharField(primary_key=True, unique=True,default=shortuuid.uuid, editable=False)
    name = models.CharField(max_length=200)
    created_time = models.DateField(auto_now_add=True)
    mpart = models.ForeignKey(
        Mpart,
        on_delete=models.CASCADE,
        related_name='files'
    )
    attachment = models.FileField(
        upload_to='files/',
        blank=True,
        null=True
    )

    def __str__(self):
        return self.name

class BomItem(models.Model):
    id = models.CharField(primary_key=True, unique=True,default=shortuuid.uuid, editable=False)
    pid = models.ForeignKey(Mpart, related_name='bom_items', on_delete=models.CASCADE)
    cid = models.ForeignKey(Mpart, related_name='used_in_boms', on_delete=models.CASCADE)
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )

    def __str__(self):
        return f'{self.pid} -> {self.cid} x {self.quantity}'




