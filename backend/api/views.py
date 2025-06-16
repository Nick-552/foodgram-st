from django.shortcuts import render
import base64
import uuid
import logging
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from .models import (
    Favorite, Follow, Ingredient, Recipe,
    ShoppingCart, IngredientAmount
)
from .serializers import (
    CustomUserSerializer, FollowSerializer,
    IngredientSerializer, RecipeCreateSerializer,
    RecipeSerializer, GenerateRecipeRequestSerializer,
    GeneratedRecipeSerializer, UserAvatarSerializer
)
from .filters import IngredientFilter, RecipeFilter
from .permissions import IsAuthorOrReadOnly
from .pagination import CustomPagination
from .utils import generate_recipes_with_ai

logger = logging.getLogger(__name__)
User = get_user_model()


class CustomUserViewSet(UserViewSet):
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    pagination_class = CustomPagination

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
            if user.follower.filter(author=author).exists():
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
            follow = user.follower.filter(author=author)
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
        follows = user.follower.all()
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
            serializer = UserAvatarSerializer(user, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(
                {'avatar': request.build_absolute_uri(user.avatar.url)},
                status=status.HTTP_200_OK
            )


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = (IsAuthorOrReadOnly,)
    pagination_class = CustomPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action in ('create', 'partial_update', 'update'):
            return RecipeCreateSerializer
        return RecipeSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def favorite(self, request, pk):
        return self._handle_recipe_action(
            request, pk, Favorite, 'favorite'
        )

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request, pk):
        return self._handle_recipe_action(
            request, pk, ShoppingCart, 'shopping_cart'
        )

    def _handle_recipe_action(self, request, pk, model, action_name):
        user = request.user
        recipe = get_object_or_404(Recipe, id=pk)

        if request.method == 'POST':
            if model.objects.filter(user=user, recipe=recipe).exists():
                return Response(
                    {'error': f'Рецепт уже в {action_name}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            model.objects.create(user=user, recipe=recipe)
            return Response({
                'id': recipe.id,
                'name': recipe.name,
                'image': request.build_absolute_uri(recipe.image.url) if recipe.image else None,
                'cooking_time': recipe.cooking_time
            }, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            item = model.objects.filter(user=user, recipe=recipe)
            if not item.exists():
                return Response(
                    {'error': f'Рецепт не в {action_name}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['get'],
        url_path='get-link'
    )
    def get_link(self, request, pk=None):
        recipe = get_object_or_404(Recipe, id=pk)
        host = request.get_host()
        protocol = 'https' if request.is_secure() else 'http'
        short_link = f"{protocol}://{host}/s/{pk}"
        return Response({'short-link': short_link})
        
    @action(
        detail=False,
        permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        user = request.user
        ingredients = IngredientAmount.objects.filter(
            recipe__shopping_cart__user=user
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(amount=Sum('amount'))

        shopping_list = ['Список покупок:\n']
        for ingredient in ingredients:
            shopping_list.append(
                f'{ingredient["ingredient__name"]} - '
                f'{ingredient["amount"]} '
                f'{ingredient["ingredient__measurement_unit"]}\n'
            )

        response = HttpResponse(
            ''.join(shopping_list),
            content_type='text/plain'
        )
        response['Content-Disposition'] = (
            'attachment; filename="shopping_list.txt"'
        )
        return response

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, 
            data=request.data,
            partial=partial,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)
    
    @action(
        detail=False,
        methods=['post'],
        url_path='generate',
        permission_classes=[AllowAny]
    )
    def generate_recipes(self, request):
        serializer = GenerateRecipeRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            recipes = generate_recipes_with_ai(serializer.validated_data)
            
            response_serializer = GeneratedRecipeSerializer(data=recipes, many=True)
            response_serializer.is_valid(raise_exception=True)
            
            logger.info(f"Successfully generated {len(recipes)} recipes")
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        except ValueError as e:
            if "API key" in str(e):
                logger.error("API key for recipe generation not configured")
                return Response(
                    {"error": "OpenAI API ключ для генерации рецептов не настроен. Обратитесь к администратору."},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
            logger.error(f"Recipe generation error: {str(e)}")
            return Response(
                {"error": f"Ошибка генерации рецептов: {str(e)}"},
                status=status.HTTP_502_BAD_GATEWAY
            )
