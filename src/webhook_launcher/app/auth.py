from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.backends import RemoteUserBackend
from django.db.models.signals import post_save
from django.dispatch import receiver

from rest_framework import authentication
from rest_framework import exceptions

from webhook_launcher.app.models import LastSeenRevision, WebHookMapping

class RemoteAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        username = request.META.get('REMOTE_USER')
        if not username:
            return None

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise exceptions.AuthenticationFailed('No such user')

        return (user, None)

class RemoteStaffBackend(RemoteUserBackend):

    def configure_user(self, user):
        default_perms(User, created=True, instance=user)
        return user


@receiver(post_save, sender=User, weak=False, dispatch_uid="default_perms")
def default_perms(sender, **kwargs):
    if kwargs['created']:
        user = kwargs['instance']
        # Set the is_staff flag in a transaction-safe way, while
        # working around django_auth_ldap which saves unsafely.
        User.objects.filter(id=user.id).update(is_staff=True)
        user.is_staff = True
        try:
            whm_ct = ContentType.objects.get_for_model(WebHookMapping)
            lsr_ct = ContentType.objects.get_for_model(LastSeenRevision)
            user.user_permissions.add(*whm_ct.permission_set.all())
            user.user_permissions.add(*lsr_ct.permission_set.all())
        except ContentType.DoesNotExist:
            # we're probably creating the superuser during syncdb
            pass
