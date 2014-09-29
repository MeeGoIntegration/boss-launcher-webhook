from models import WebHookMapping, LastSeenRevision, BuildService
from rest_framework import serializers

class BuildServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = BuildService
        fields = ('apiurl', 'weburl')

class LastSeenRevisionSerializer(serializers.ModelSerializer):
    class Meta:
        model = LastSeenRevision
        fields = ('revision', 'tag', 'timestamp')

class WebHookMappingSerializer(serializers.ModelSerializer):
    lsr = LastSeenRevisionSerializer()

    class Meta:
        model = WebHookMapping
        fields = ('repourl', 'branch', 'project', 'package', 'obs', 'lsr')
        depth = 2
