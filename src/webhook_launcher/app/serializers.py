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
#        exclude = ('id', 'handled', 'payload', 'timestamp',)

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
        
class LSRField(serializers.WritableField):
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
# Alternate approach is to report lsr and accept revision
#    lsr = LastSeenRevisionSerializer(many=False, read_only=True)
#    revision = serializers.CharField(source="lsr.revision", write_only=True)
    lsr = LSRField(source="*", read_only=True)
    obs = BuildServiceField()
    user = UserField()

# Alternate approach is to link to User
#    user = serializers.RelatedField(many=False, read_only=True)

    class Meta:
        model = WebHookMapping
        exclude = ('id',) # don't want/need to expose internal pk
        depth = 1

