import logging
from .recipe_generator import RecipeGenerator
from .models import Ingredient
from .serializers import IngredientDetailSerializer

logger = logging.getLogger(__name__)

def generate_recipes_with_ai(serializer_data):
    logger.info("Starting recipe generation process")
    
    ingredients_data = []
    for ing_data in serializer_data['ingredients']:
        ingredient = Ingredient.objects.get(id=ing_data['id'])
        serializer = IngredientDetailSerializer(ingredient)
        ingredient_data = serializer.data
        ingredient_data['amount'] = ing_data.get('amount')
        ingredients_data.append(ingredient_data)
    
    generator = RecipeGenerator()
    recipes = generator.generate_recipes(
        ingredients=ingredients_data,
        allow_additional_ingredients=serializer_data['allow_additional_ingredients'],
        recipe_name=serializer_data.get('recipe_name'),
        count=serializer_data['count']
    )
    
    logger.info(f"Successfully generated {len(recipes)} recipes")
    return recipes 