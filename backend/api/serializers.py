from django.contrib.auth import get_user_model
from djoser.serializers import UserSerializer, UserCreateSerializer
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
import base64
from django.core.files.base import ContentFile
import string
import random


from .models import (
    Follow, Ingredient, Recipe, IngredientAmount,
    Favorite, ShoppingCart, User, MIN_COOKING_TIME, MAX_COOKING_TIME, MIN_AMOUNT, MAX_AMOUNT
)

class CustomUserCreateSerializer(UserCreateSerializer):
    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name',
            'last_name', 'password'
        )
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class CustomUserSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id', 'username', 'first_name', 'last_name',
            'email', 'is_subscribed', 'avatar'
        )

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return user.follower.filter(author=obj).exists()
        
    def get_avatar(self, obj):
        if obj.avatar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.avatar.url)
        return None


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            random_str = ''.join(random.choices(string.ascii_letters + string.digits, k=7))
            data = ContentFile(base64.b64decode(imgstr), name=f'temp_{random_str}.{ext}')
        return super().to_internal_value(data)


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientAmountSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(source='ingredient.measurement_unit')

    class Meta:
        model = IngredientAmount
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeMinifiedSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        
    def get_image(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
        return None


class RecipeSerializer(serializers.ModelSerializer):
    author = CustomUserSerializer(read_only=True)
    ingredients = IngredientAmountSerializer(
        source='ingredientamount_set',
        many=True,
        read_only=True,
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'author', 'ingredients',
            'is_favorited', 'is_in_shopping_cart',
            'name', 'image', 'text', 'cooking_time'
        )

    def get_is_favorited(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return user.favorites.filter(recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return user.shopping_cart.filter(recipe=obj).exists()
        
    def get_image(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
        return None


class IngredientAmountCreateSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    amount = serializers.IntegerField(
        min_value=MIN_AMOUNT,
        max_value=MAX_AMOUNT
    )

    class Meta:
        model = IngredientAmount
        fields = ('id', 'amount')


class RecipeCreateSerializer(serializers.ModelSerializer):
    ingredients = IngredientAmountCreateSerializer(many=True)
    image = Base64ImageField()
    cooking_time = serializers.IntegerField(
        min_value=MIN_COOKING_TIME,
        max_value=MAX_COOKING_TIME
    )

    class Meta:
        model = Recipe
        fields = (
            'ingredients', 'image',
            'name', 'text', 'cooking_time'
        )

    def validate(self, data):
        if 'ingredients' not in data or not data['ingredients']:
            raise serializers.ValidationError({'ingredients': ['Это поле обязательно.']})
            
        ingredient_ids = [item['id'] for item in data['ingredients']]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError({'ingredients': ['Ингредиенты не должны повторяться.']})
            
        existing_ingredients = Ingredient.objects.filter(id__in=ingredient_ids).count()
        if existing_ingredients != len(ingredient_ids):
            raise serializers.ValidationError({'ingredients': ['Некоторые ингредиенты не существуют.']})
                
        return data
        
    def _create_ingredients(self, recipe, ingredients_data):
        for ingredient_data in ingredients_data:
            IngredientAmount.objects.create(
                recipe=recipe,
                ingredient_id=ingredient_data['id'],
                amount=ingredient_data['amount']
            )

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        
        self._create_ingredients(recipe, ingredients_data)
        return recipe

    def update(self, instance, validated_data):
        if 'ingredients' in validated_data:
            ingredients_data = validated_data.pop('ingredients')
            
            instance.ingredientamount_set.all().delete()
            
            self._create_ingredients(instance, ingredients_data)
                
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

    def to_representation(self, instance):
        request = self.context.get('request')
        context = {'request': request}
        return RecipeSerializer(instance, context=context).data


class FavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = ('user', 'recipe')
        validators = [
            UniqueTogetherValidator(
                queryset=Favorite.objects.all(),
                fields=('user', 'recipe'),
                message='Рецепт уже в избранном'
            )
        ]


class ShoppingCartSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe')
        validators = [
            UniqueTogetherValidator(
                queryset=ShoppingCart.objects.all(),
                fields=('user', 'recipe'),
                message='Рецепт уже в списке покупок'
            )
        ]


class FollowSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='author.id')
    username = serializers.ReadOnlyField(source='author.username')
    first_name = serializers.ReadOnlyField(source='author.first_name')
    last_name = serializers.ReadOnlyField(source='author.last_name')
    email = serializers.ReadOnlyField(source='author.email')
    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()

    class Meta:
        model = Follow
        fields = (
            'id', 'username', 'first_name', 'last_name',
            'email', 'is_subscribed', 'avatar',
            'recipes_count', 'recipes'
        )

    def get_is_subscribed(self, obj):
        return obj.user.follower.filter(author=obj.author).exists()

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.GET.get('recipes_limit')
        queryset = obj.author.recipes.all()
        if limit:
            queryset = queryset[:int(limit)]
        return RecipeMinifiedSerializer(queryset, many=True, context={'request': request}).data

    def get_recipes_count(self, obj):
        return obj.author.recipes.count()
        
    def get_avatar(self, obj):
        request = self.context.get('request')
        if obj.author.avatar:
            return request.build_absolute_uri(obj.author.avatar.url)
        return None


# Генерация рецепта с помощью ИИ

class GenerateRecipeIngredientSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=True)
    amount = serializers.CharField(required=False)
    measurement_unit = serializers.CharField(required=False, read_only=True)
    name = serializers.CharField(required=False, read_only=True)
    
    def validate_id(self, value):
        try:
            Ingredient.objects.get(id=value)
            return value
        except Ingredient.DoesNotExist:
            raise serializers.ValidationError("Ингредиент с указанным ID не существует.")


class GenerateRecipeRequestSerializer(serializers.Serializer):
    ingredients = GenerateRecipeIngredientSerializer(many=True, required=True)
    allow_additional_ingredients = serializers.BooleanField(default=True)
    recipe_name = serializers.CharField(required=False, allow_blank=True)
    count = serializers.IntegerField(min_value=1, max_value=5, default=3)
    
    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError("Необходимо указать хотя бы один ингредиент.")
        return value


class GeneratedRecipeIngredientSerializer(serializers.Serializer):
    name = serializers.CharField()
    amount = serializers.CharField()
    measurement_unit = serializers.CharField(allow_blank=True)


class GeneratedRecipeSerializer(serializers.Serializer):
    name = serializers.CharField()
    description = serializers.CharField()
    cooking_time = serializers.IntegerField()
    ingredients = GeneratedRecipeIngredientSerializer(many=True)
    instructions = serializers.ListField(child=serializers.CharField()) 