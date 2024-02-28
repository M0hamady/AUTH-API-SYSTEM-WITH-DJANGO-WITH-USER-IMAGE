import os
from django.contrib.auth.models import AbstractUser
from django.db import models


def get_user_image_path(instance, filename):
    # Construct the file path
    return os.path.join('user_images', instance.username, filename)

class User(AbstractUser):
    is_client = models.BooleanField(default=False)
    image = models.ImageField(upload_to=get_user_image_path, blank=True, null=True, max_length=255)

    def save(self, *args, **kwargs):
        # Check if the image exceeds the maximum file size
        if self.image and self.image.size > 6 * 1024 * 1024:  # 6 megabytes
            raise ValueError("The image file size exceeds the maximum limit of 6 megabytes.")

        # Call the parent save() method to save the user instance
        super().save(*args, **kwargs)
    def delete(self, *args, **kwargs):
        # Check if the image field has changed
        if self._state.adding or self.image != self.__class__.objects.get(pk=self.pk).image:
            # Delete the old image file from storage
            old_image = self.__class__.objects.get(pk=self.pk).image
            if old_image:
                # Get the path of the old image file
                old_image_path = old_image.path

                # Delete the old image file using the os module
                if os.path.exists(old_image_path):
                    os.remove(old_image_path)

        # Call the parent delete() method to delete the user instance
        super().delete(*args, **kwargs)
    @property
    def get_image_url(self):
        # Custom method to get the URL of the user's image
        try:
            self.image
            return self.image.url
        except:
            return None
class BlacklistedToken(models.Model):
    token = models.CharField(max_length=255, unique=True)
    revoked_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.token

    class Meta:
        verbose_name_plural = 'Blacklisted Tokens'
class Project(models.Model):
    name = models.CharField(max_length=100)
    client = models.ForeignKey(User, on_delete=models.CASCADE)