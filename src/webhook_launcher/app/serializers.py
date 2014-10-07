from webhook_launcher.app.models import WebHookMapping, LastSeenRevision, BuildService
from models import WebHookMapping, LastSeenRevision, BuildService
from django.contrib.auth.models import User
from rest_framework import serializers
from StringIO import StringIO
from rest_framework.parsers import JSONParser

class BuildServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = BuildService

class LastSeenRevisionSerializer(serializers.ModelSerializer):
    class Meta:
        model = LastSeenRevision
        exclude = ('id', 'handled', 'payload', 'timestamp',)

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
        return LastSeenRevisionSerializer().to_native(obj.lsr)

    def field_from_native(self, data, files, field_name, into):
        if field_name not in data:
            return
        mydata = data[field_name]
        
        # create a new lsr
        lsr = LastSeenRevision(mapping = self.parent.object)
        # update it with the data and ensure it's valid
        lsr_ = LastSeenRevisionSerializer(lsr, data=mydata, partial=True)
        if not lsr_.is_valid() :
            raise Exception(lsr_.errors)
        # and ensure the mapping is still to us
        lsr.mapping = self.parent.object
        lsr.save()

class WebHookMappingSerializer(serializers.ModelSerializer):
#    lsr = LastSeenRevisionSerializer(many=False, read_only=True)
#    revision = serializers.CharField(source="lsr.revision", write_only=True, required=False)
    lsr = LSRField(source="*", read_only=True)
    obs = BuildServiceField()
    user = UserField()

    class Meta:
        model = WebHookMapping
        exclude = ('id',) # don't want/need to expose internal pk
        depth = 1
