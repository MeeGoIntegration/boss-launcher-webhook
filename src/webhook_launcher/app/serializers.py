from models import WebHookMapping, LastSeenRevision, BuildService
from rest_framework import serializers

class BuildServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = BuildService

class LastSeenRevisionSerializer(serializers.ModelSerializer):
    class Meta:
        model = LastSeenRevision

class WebHookMappingSerializer(serializers.ModelSerializer):
    lsr = LastSeenRevisionSerializer(many=False, read_only=True)
    revision = serializers.CharField(source="lsr.revision", write_only=True)
    obs = BuildServiceSerializer(many=False, read_only=True)
    obs_id = serializers.IntegerField(source="obs.pk", write_only=True)
    user = serializers.RelatedField(many=False, read_only=True)

    class Meta:
        model = WebHookMapping
        depth = 2

