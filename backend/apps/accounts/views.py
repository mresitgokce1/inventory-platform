"""Views for user authentication and management."""

from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, RetrieveUpdateAPIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from django.contrib.auth import get_user_model
from apps.common.permissions import RequireRolesMixin
from apps.accounts.roles import SYSTEM_ADMIN
from .serializers import (
    CustomTokenObtainPairSerializer,
    UserSerializer,
    UserListSerializer,
    UserCreateSerializer
)

User = get_user_model()


class SystemAdminPermission(permissions.BasePermission):
    """Permission class that only allows system admins."""
    
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and 
            hasattr(request.user, 'role') and 
            request.user.role == SYSTEM_ADMIN
        )


class CustomTokenObtainPairView(TokenObtainPairView):
    """Custom login view that handles deleted users."""
    serializer_class = CustomTokenObtainPairSerializer


class CustomTokenRefreshView(TokenRefreshView):
    """Custom refresh view that rotates refresh tokens."""
    pass


class LogoutView(APIView):
    """Logout view that blacklists the refresh token."""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            if not refresh_token:
                return Response(
                    {"detail": "Refresh token is required"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            return Response(
                {"detail": "Successfully logged out"}, 
                status=status.HTTP_205_RESET_CONTENT
            )
        except TokenError:
            return Response(
                {"detail": "Invalid or expired refresh token"}, 
                status=status.HTTP_400_BAD_REQUEST
            )


class UserMeView(RetrieveUpdateAPIView):
    """View for authenticated user to view and update their own profile."""
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user


class UserListView(ListAPIView):
    """View for system admins to list all users."""
    queryset = User.objects.all()
    serializer_class = UserListSerializer
    permission_classes = [SystemAdminPermission]
    
    def get_queryset(self):
        """Return all users including soft-deleted ones for admins."""
        return User.objects.unfiltered().all()


class UserCreateView(APIView):
    """View for system admins to create new users."""
    permission_classes = [SystemAdminPermission]
    
    def post(self, request):
        serializer = UserCreateSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(
                UserSerializer(user).data, 
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
