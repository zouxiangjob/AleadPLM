import uuid

from django.db import models

class Mpart(models.Model):
    id  = models.UUIDField(primary_key=True, unique=True,default=uuid.uuid4,editable=False)
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=100)
    publication_date = models.DateField()
    price = models.DecimalField(max_digits=5, decimal_places=1)
    file = models.FileField(upload_to='files/', blank=False,null=True)

    def __str__(self):
        return self.title

class Files(models.Model):
    id = models.UUIDField(primary_key=True, unique=True, default=uuid.uuid4, editable=False)
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
