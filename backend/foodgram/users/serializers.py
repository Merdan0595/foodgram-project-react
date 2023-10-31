from rest_framework import serializers

from recipes.models import Follow
from .models import User


class UserSerializer(serializers.ModelSerializer):
    "Сериализатор для регистрации пользователя"
    class Meta:
        model = User
        fields = (
            'email', 'username', 'first_name', 'last_name', 'password'
        )

    def create(self, validated_data):
        user = User(
            email=validated_data['email'],
            username=validated_data['username']
        )
        user.set_password(validated_data['password'])
        user.save()
        return user

    def validate(self, data):
        if data.get('username') == 'me':
            raise serializers.ValidationError(
                'Нельзя использовать имя "me"'
            )
        if not User.objects.filter(
            username=data.get('username'), email=data.get('email')
        ).exists():
            if User.objects.filter(username=data.get('username')):
                raise serializers.ValidationError(
                    'Пользователь с таким логином уже существует'
                )
            if User.objects.filter(email=data.get("email")):
                raise serializers.ValidationError(
                    'Пользователь с такой почтой уже существует'
                )
        return data


class UsersViewSerializer(serializers.ModelSerializer):
    "Сериализатор для списка пользователей"
    class Meta:
        model = User
        fields = (
            'username', 'email', 'first_name', 'last_name',
        )


class ProfileSerializer(serializers.ModelSerializer):
    "Сериализатор для джосера с возвратом информации"
    "о подписке"
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id', 'email', 'username', 'first_name',
            'last_name', 'is_subscribed'
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Follow.objects.filter(
                user=request.user, following=obj
                ).exists()
        return False
