from django.db import models


class CSVDownload(models.Model):
    uuid = models.UUIDField(db_index=True)
    downloaded_at = models.DateTimeField(auto_now_add=True)
