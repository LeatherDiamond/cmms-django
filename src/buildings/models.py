from django.db import models


class Building(models.Model):
    name = models.CharField(
        max_length=255,
        verbose_name="Name",
    )
    address = models.CharField(
        max_length=255,
        verbose_name="Address",
    )

    def __str__(self):
        return self.name
