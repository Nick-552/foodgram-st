import base64
import uuid
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from djoser.views import UserViewSet
from rest_framework import serializers, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from .models import Follow
from .pagination import UserPagination
from .serializers import CustomUserSerializer, FollowSerializer

User = get_user_model()


class CustomUserViewSet(UserViewSet):
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    pagination_class = UserPagination
    
    def get_permissions(self):
        if self.action == 'retrieve':
            return [AllowAny()]
        return super().get_permissions()

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def subscribe(self, request, id):
        user = request.user
        try:
            author = User.objects.get(id=id)
        except User.DoesNotExist:
            return Response(
                {'detail': 'Пользователь не найден.'},
                status=status.HTTP_404_NOT_FOUND
            )

        if request.method == 'POST':
            if user == author:
                return Response(
                    {'error': 'Нельзя подписаться на самого себя'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if Follow.objects.filter(user=user, author=author).exists():
                return Response(
                    {'error': 'Вы уже подписаны на этого пользователя'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            follow = Follow.objects.create(user=user, author=author)
            serializer = FollowSerializer(
                follow, context={'request': request}
            )
            return Response(
                serializer.data, status=status.HTTP_201_CREATED
            )

        if request.method == 'DELETE':
            follow = Follow.objects.filter(user=user, author=author)
            if not follow.exists():
                return Response(
                    {'error': 'Вы не подписаны на этого пользователя'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            follow.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        permission_classes=[IsAuthenticated]
    )
    def subscriptions(self, request):
        user = request.user
        follows = Follow.objects.filter(user=user)
        pages = self.paginate_queryset(follows)
        serializer = FollowSerializer(
            pages, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)
        
    @action(
        detail=False,
        methods=['put', 'delete'],
        permission_classes=[IsAuthenticated],
        url_path='me/avatar'
    )
    def me_avatar(self, request):
        user = request.user
        
        if request.method == 'DELETE':
            if user.avatar:
                user.avatar.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        
        if request.method == 'PUT':
            try:
                avatar_data = request.data.get('avatar')
                if not avatar_data:
                    raise serializers.ValidationError({'avatar': ['Это поле обязательно.']})
                
                # Check if the data is base64 encoded
                if avatar_data.startswith('data:image'):
                    # Split the base64 string to get the actual data
                    format, imgstr = avatar_data.split(';base64,')
                    ext = format.split('/')[-1]
                    
                    # Generate a unique filename
                    avatar_filename = f"{uuid.uuid4()}.{ext}"
                    
                    # Convert base64 to file
                    avatar_file = ContentFile(
                        base64.b64decode(imgstr),
                        name=avatar_filename
                    )
                    
                    # Save the avatar
                    user.avatar = avatar_file
                    user.save()
                    
                    return Response(
                        {'avatar': request.build_absolute_uri(user.avatar.url)},
                        status=status.HTTP_200_OK
                    )
                else:
                    raise serializers.ValidationError({'avatar': ['Неверный формат данных.']})
                    
            except Exception as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
    