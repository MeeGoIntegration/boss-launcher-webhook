from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework.utils import model_meta

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

    def validate(self, attrs):
        # Since DRF 3.0 the model clean() method is no longer called
        # automatically. And this is probably not the best solution to do the
        # validation, but at the moment it's the simplest one.
        if self.instance is None:
            instance = WebHookMapping(**attrs)
            instance.clean()
        else:
            info = model_meta.get_field_info(self.instance)
            for attr, value in attrs.items():
                if attr == 'lsr':
                    # lsr can not be set directly at the moment, so skip it
                    continue
                if attr in info.relations and info.relations[attr].to_many:
                    # We don't have any to-many relations at the moment, but
                    # this is to avoid setting them in the future if they are
                    # added. Manipulating to-many relation directly changes
                    # the DB so it can't be done here.
                    continue
                else:
                    setattr(self.instance, attr, value)
                self.instance.clean()
        return attrs
