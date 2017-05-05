from django.contrib.auth.models import User
from rest_framework import serializers

from webhook_launcher.app.models import (
    BuildService, LastSeenRevision, WebHookMapping
)


class BuildServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = BuildService
        fields = '__all__'


class LastSeenRevisionSerializer(serializers.ModelSerializer):
    class Meta:
        model = LastSeenRevision
        fields = ['tag', 'revision']


class BuildServiceField(serializers.Field):
    """
    Handle references to a BuildService object
    Outputs namespace
    Takes a namespace as a key
    """
    def to_representation(self, obj):
        return obj.namespace

    def to_internal_value(self, data):
        obs = BuildService.objects.get(namespace=data)
        return obs


class UserField(serializers.Field):
    """
    Handle references to a User object
    """
    def to_representation(self, obj):
        return obj.username

    def to_internal_value(self, data):
        user = User.objects.get(username=data)
        return user


class WebHookMappingSerializer(serializers.ModelSerializer):
    lsr = LastSeenRevisionSerializer(
        many=False,
        read_only=False,
        required=False,
    )
    obs = BuildServiceField()
    user = UserField()

    class Meta:
        model = WebHookMapping
        fields = '__all__'
        depth = 1

    def create(self, validated_data):
        lsr_data = validated_data.pop('lsr', None)
        whm = super(
            WebHookMappingSerializer, self
        ).create(validated_data)
        if lsr_data:
            lsr = whm.lsr
            lsr.revision = lsr_data.get('revision', lsr.revision)
            lsr.tag = lsr_data.get('tag', lsr.tag)
            lsr.save()
        return whm

    def update(self, whm, validated_data):
        lsr_data = validated_data.pop('lsr', None)
        whm = super(
            WebHookMappingSerializer, self
        ).update(whm, validated_data)

        if lsr_data:
            lsr = whm.lsr
            lsr.revision = lsr_data.get('revision', lsr.revision)
            lsr.tag = lsr_data.get('tag', lsr.tag)
            lsr.save()

        return whm
