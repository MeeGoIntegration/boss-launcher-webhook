from webhook_launcher.app.models import WebHookMapping, LastSeenRevision, BuildService
from models import WebHookMapping, LastSeenRevision, BuildService
from django.contrib.auth.models import User
from rest_framework import serializers
from StringIO import StringIO
from rest_framework.parsers import JSONParser
from collections import OrderedDict

class BuildServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = BuildService
        fields = '__all__'

class LastSeenRevisionSerializer(serializers.ModelSerializer):
    class Meta:
        model = LastSeenRevision
        exclude = ('payload',)
        #exclude = ('id', 'handled', 'payload', 'timestamp',)

# Commented out pending testing
# class BuildServiceField(serializers.Field):
#     """
#     Handle references to a BuildService object
#     Outputs namespace
#     Takes a namespace as a key
#     """
#     def to_representation(self, obj):
#         return BuildServiceSerializer().to_representation(obj)

#     def to_internal_value(self, data):
#         try:
#             obs = BuildService.objects.get(namespace=data)
#         except BuildService.DoesNotExist as e:
#             obs = None
#         return obs

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

class LSRField(serializers.Field):
    """
    Handle references to a LastSeenRevision object
    """
    def to_representation(self, obj):
        return LastSeenRevisionSerializer().to_representation(obj.lsr)

    def get_value(self, obj):
        # Pass the entire object through to `to_representation()`,
        # instead of the standard attribute lookup.
        return obj

    def to_internal_value(self, data):
        field_name="lsr"
        if field_name not in data:
            raise Exception("No 'lsr' in data:  %s" % data)
        lsrdata = data[field_name] # An OrderedDict

        # Try and get our existing lsr
        if self.parent.initial_data is None:
            raise Exception("Can't set an lsr on object creation since the lsr needs the id of the object which hasn't been created at the time the lsr is created :(")

        lsr = None
        if "id" in  lsrdata:
            lsr = LastSeenRevision.objects.get(pk=lsrdata["id"])
        if not lsr:
            # create a new lsr
            lsr = LastSeenRevision(mapping = lsrdata["id"])
        # update it with the data and ensure it's valid
        # Passing lsr into LastSeenRevisionSerializer() updates it in place
        # and returns a Serializer reference to it which we use for the useful
        # functions
        lsr_ = LastSeenRevisionSerializer(lsr, data=lsrdata, partial=True)
        if not lsr_.is_valid() :
            raise Exception(lsr_.errors)
        # and just absolutely ensure the mapping is still to us
        lsr_.mapping = data["id"]
        lsr_.save()
        r=OrderedDict()
        r["_lsr"]=lsr_.instance
        return r

class WebHookMappingSerializer(serializers.ModelSerializer):
#    lsr = LastSeenRevisionSerializer(many=False, read_only=True)
#    revision = serializers.CharField(source="lsr.revision", write_only=True, required=False)
    lsr = LSRField(source="*", read_only=False)
    obs = BuildServiceField()
    user = UserField()

    class Meta:
        model = WebHookMapping
#        exclude = ('id',) # don't want/need to expose internal pk
        fields = '__all__'
        depth = 1
