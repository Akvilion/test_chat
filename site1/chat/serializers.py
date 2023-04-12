from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Thread, Message
from rest_framework.serializers import ValidationError


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username']


class ThreadSerializer(serializers.ModelSerializer):
    participants = UserSerializer(many=True)

    class Meta:
        model = Thread
        fields = ['id', 'participants', 'created', 'updated']


class MessageSerializer(serializers.ModelSerializer):
    sender = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = Message
        fields = ['id', 'sender', 'text', 'thread', 'created', 'is_read']

    def validate(self, data):
        sender = data['sender']
        thread = data['thread']

        if sender not in thread.participants.all():
            raise ValidationError("Sender must be a participant in the thread.")

        return data
