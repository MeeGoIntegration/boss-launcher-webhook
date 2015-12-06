from django.contrib.auth.models import User, Permission
from django.contrib.auth.backends import RemoteUserBackend
from django.db.models.signals import post_save

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

post_save.connect(default_perms, sender=User, weak=False,
                  dispatch_uid="default_perms")

def default_perms(sender, **kwargs):
    if kwargs['created']:
        user = kwargs['instance']
        # Set the is_staff flag in a transaction-safe way, while
        # working around django_auth_ldap which saves unsafely.
        User.objects.filter(id=user.id).update(is_staff=True)
        user.is_staff = True
        try:
            user.user_permissions.add(Permission.objects.get(codename=WebHookMapping._meta.get_add_permission()))
            user.user_permissions.add(Permission.objects.get(codename=WebHookMapping._meta.get_change_permission()))
            user.user_permissions.add(Permission.objects.get(codename=WebHookMapping._meta.get_delete_permission()))
            user.user_permissions.add(Permission.objects.get(codename=LastSeenRevision._meta.get_add_permission()))
            user.user_permissions.add(Permission.objects.get(codename=LastSeenRevision._meta.get_change_permission()))
            user.user_permissions.add(Permission.objects.get(codename=LastSeenRevision._meta.get_delete_permission()))
        except Permission.DoesNotExist:
            # we're probably creating the superuser during syncdb
            pass

