"""Serializers for user authentication and management."""

from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate
from .roles import ROLE_CHOICES

User = get_user_model()


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Custom token serializer that blocks deleted users."""
    
    def validate(self, attrs):
        # Check if user exists and is not soft-deleted before authentication
        email = attrs.get('email') or attrs.get(self.username_field)
        
        if email:
            try:
                # Use unfiltered to get even soft-deleted users
                user = User.objects.unfiltered().get(email=email)
                if user.is_deleted:
                    raise serializers.ValidationError({
                        "detail": "Account is deleted", 
                        "code": "ACCOUNT_DELETED"
                    })
            except User.DoesNotExist:
                pass  # Let the parent validation handle this
        
        # Use parent validation which handles authentication
        data = super().validate(attrs)
        
        # Add custom claims
        refresh = self.get_token(self.user)
        data['refresh'] = str(refresh)
        data['access'] = str(refresh.access_token)
        data['user'] = UserSerializer(self.user).data
        
        return data


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""
    
    full_name = serializers.ReadOnlyField()
    password = serializers.CharField(write_only=True, required=False)
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'role', 'is_active', 'is_staff', 'created_at', 'updated_at',
            'password'
        ]
        extra_kwargs = {
            'password': {'write_only': True},
            'id': {'read_only': True},
            'created_at': {'read_only': True},
            'updated_at': {'read_only': True},
        }
    
    def create(self, validated_data):
        """Create a new user with encrypted password."""
        password = validated_data.pop('password', None)
        user = User.objects.create_user(**validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user
    
    def update(self, instance, validated_data):
        """Update user, handling password separately."""
        password = validated_data.pop('password', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        if password:
            instance.set_password(password)
        
        instance.save()
        return instance


class UserCreateSerializer(UserSerializer):
    """Serializer for creating users with required password."""
    
    password = serializers.CharField(write_only=True, required=True)
    role = serializers.ChoiceField(choices=ROLE_CHOICES, required=True)
    
    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields
        extra_kwargs = {
            **UserSerializer.Meta.extra_kwargs,
            'email': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
        }


class UserListSerializer(serializers.ModelSerializer):
    """Simplified serializer for user listing."""
    
    full_name = serializers.ReadOnlyField()
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'role', 'is_active', 'created_at'
        ]