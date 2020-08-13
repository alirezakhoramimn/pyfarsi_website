from rest_framework.serializers import ModelSerializer, PrimaryKeyRelatedField
from rest_framework.validators import ValidationError
from .models import Group, UserInvite, Member
from account.models import User


class GetGroup(ModelSerializer):
    class Meta:
        model = Group
        fields = ('id', 'name', 'logo', 'type')
        read_only_fields = ('id', 'name', 'logo', 'type')


class CreateUserInvite(ModelSerializer):
    user = PrimaryKeyRelatedField(queryset=User.objects)
    group = PrimaryKeyRelatedField(queryset=Group.objects)

    class Meta:
        model = UserInvite
        fields = ('user', 'group')
    
    def is_valid(self, *args, **kwargs):
        validation_result = super().is_valid(*args, **kwargs)
        try:
            Member.objects.get(user=validated_data['user'], group=self.context['view'].kwargs['group_id'])
        except Member.DoesNotExist:
            return True and validation_result
        raise ValidationError('User is already invited to the group !')
   
    def create(self, validated_data):
        return UserInvite.objects.get_or_create(
            user=validated_data['user'], group=self.context['view'].kwargs['group_id']
            )[0]
