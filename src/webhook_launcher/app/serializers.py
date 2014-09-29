from webhook_launcher.app.models import WebHookMapping, LastSeenRevision, BuildService
from models import WebHookMapping, LastSeenRevision, BuildService
from django.contrib.auth.models import User
from rest_framework import serializers

class BuildServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = BuildService

class LastSeenRevisionSerializer(serializers.ModelSerializer):
    class Meta:
        model = LastSeenRevision

# Commented out pending testing
# class BuildServiceField(serializers.Field):
#     """
#     Handle references to a BuildService object
#     Outputs namespace
#     Takes a namespace as a key
#     """
#     def to_representation(self, obj):
#         return BuildServiceSerializer().to_native(obj)

#     def to_internal_value(self, data):
#         try:
#             obs = BuildService.objects.get(namespace=data)
#         except BuildService.DoesNotExist as e:
#             obs = None
#         return obs

class BuildServiceField(serializers.WritableField):
    """
    Handle references to a BuildService object
    Outputs namespace
    Takes a namespace as a key
    """
    def to_native(self, obj):
        return obj.namespace

    def from_native(self, data):
        obs = BuildService.objects.get(namespace=data)
        return obs

class UserField(serializers.WritableField):
    """
    Handle references to a User object
    """
    def to_native(self, obj):
        return obj.username


    def from_native(self, data):
        user = User.objects.get(username=data)
        return user

class LSRField(serializers.Field):
    """
    Handle references to a LastSeenRevision object
    """
    def to_native(self, obj):
        return LastSeenRevisionSerializer(obj).to_native(obj)

class WebHookMappingSerializer(serializers.ModelSerializer):
#    lsr = LastSeenRevisionSerializer(many=False, read_only=True)
    revision = serializers.CharField(source="lsr.revision", write_only=True, required=False)
#    obs = BuildServiceField()
#    user = serializers.RelatedField(many=False, read_only=True)

    lsr = LSRField()
    obs = BuildServiceField()
    user = UserField()

    class Meta:
        model = WebHookMapping
#        depth = 2
        exclude = ('id',)
