from rest_framework.serializers import ModelSerializer
from .models import User


class GetUser(ModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'avatar')
        read_only_fields = ('username', 'avatar')
