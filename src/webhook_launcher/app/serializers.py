from webhook_launcher.app.models import WebHookMapping, LastSeenRevision, BuildService
from rest_framework import serializers

class BuildServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = BuildService

class LastSeenRevisionSerializer(serializers.ModelSerializer):
    class Meta:
        model = LastSeenRevision

class BuildServiceField(serializers.Field):
    """
    Handle references to a BuildService object
    Outputs namespace
    Takes a namespace as a key
    """
    def to_representation(self, obj):
        return BuildServiceSerializer().to_native(obj)

    def to_internal_value(self, data):
        try:
            obs = BuildService.objects.get(namespace=data)
        except BuildService.DoesNotExist as e:
            obs = None
        return obs

class WebHookMappingSerializer(serializers.ModelSerializer):
    lsr = LastSeenRevisionSerializer(many=False, read_only=True)
    revision = serializers.CharField(source="lsr.revision", write_only=True, required=False)
    obs = BuildServiceField()
    user = serializers.RelatedField(many=False, read_only=True)

    class Meta:
        model = WebHookMapping
        depth = 2
