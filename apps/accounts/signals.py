from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, StudentProfile

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """Ensure every user has a linked StudentProfile."""
    if created:
        StudentProfile.objects.get_or_create(user=instance)
    else:
        if hasattr(instance, "student_profile"):
            instance.student_profile.save()
        else:
            StudentProfile.objects.create(user=instance)
