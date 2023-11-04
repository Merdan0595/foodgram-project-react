import re
from rest_framework import serializers
from djoser.serializers import UserCreateSerializer
from recipes.models import Follow
from .models import User


class UsersViewSerializer(serializers.ModelSerializer):
    "Сериализатор для возврата пользователя при регистрации"
    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name',
        )


class UserSerializer(UserCreateSerializer):
    "Сериализатор для регистрации пользователя"
    class Meta:
        model = User
        fields = (
            'email', 'username', 'first_name', 'last_name', 'password'
        )

    def create(self, validated_data):
        user = User(
            email=validated_data['email'],
            username=validated_data['username'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name']
        )
        user.set_password(validated_data['password'])
        user.save()
        return user

    def validate(self, data):
        username = data.get('username')

        if not re.match(r'^[\w.@+-]+$', username):
            raise serializers.ValidationError('Неправильный формат логина')
        if username == 'me':
            raise serializers.ValidationError(
                'Нельзя использовать имя "me"'
            )
        if not User.objects.filter(
            username=username, email=data.get('email')
        ).exists():
            if User.objects.filter(username=username):
                raise serializers.ValidationError(
                    'Пользователь с таким логином уже существует'
                )
            if User.objects.filter(email=data.get("email")):
                raise serializers.ValidationError(
                    'Пользователь с такой почтой уже существует'
                )
        return data

    def to_representation(self, instance):
        return UsersViewSerializer(instance, context=self.context).data


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
