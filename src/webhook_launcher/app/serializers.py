from models import WebHookMapping, LastSeenRevision, BuildService
from django.contrib.auth.models import User
from rest_framework import serializers

class BuildServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = BuildService
        fields = ('apiurl', 'weburl')

class LastSeenRevisionSerializer(serializers.ModelSerializer):
    class Meta:
        model = LastSeenRevision
        fields = ('revision', 'tag', 'timestamp')

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

    lsr = LSRField()
    obs = BuildServiceField()
    user = UserField()
    
    class Meta:
        model = WebHookMapping
        exclude = ('id',)
