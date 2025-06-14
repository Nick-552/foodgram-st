import os
import requests
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class RecipeGenerator:
    def __init__(self):
        self.api_key = os.getenv('AI_API_KEY', '')
        self.api_url = "https://api.openai.com/v1/chat/completions"
    
    def _get_all_ingredients(self) -> List[str]:
        from .models import Ingredient
        ingredients = Ingredient.objects.all().values_list('name', flat=True)
        return list(ingredients)
    
    def generate_recipes(
        self, 
        ingredients: List[Dict[str, Any]], 
        allow_additional_ingredients: bool = True,
        recipe_name: Optional[str] = None,
        count: int = 3
    ) -> List[Dict[str, Any]]:
        logger.info(f"Starting recipe generation with {len(ingredients)} ingredients")
        
        if not self.api_key:
            logger.error("AI_API_KEY environment variable not set")
            raise ValueError("API key for recipe generation is not configured")
        
        count = min(max(1, count), 5)
        
        ingredient_list = []
        for ing in ingredients:
            if ing.get('amount'):
                ingredient_list.append(f"{ing['name']} - {ing['amount']} {ing.get('measurement_unit', '')}")
            else:
                ingredient_list.append(ing['name'])
        
        ingredients_str = "\n".join([f"- {item}" for item in ingredient_list])
        
        additional_ingredients_text = ""
        if allow_additional_ingredients:
            all_ingredients = self._get_all_ingredients()
            additional_ingredients_text = (
                f"Можно использовать дополнительные ингредиенты из этого списка: "
                f"{', '.join(all_ingredients[:100])}. "
                f"Используйте их экономно и только если они улучшат рецепт."
            )
        
        recipe_name_text = f" Рецепт должен называться '{recipe_name}'." if recipe_name else ""
        
        prompt = f"""
        Сгенерируй {count} подробных кулинарных рецептов на русском языке, используя следующие основные ингредиенты:
        
        {ingredients_str}
        
        {additional_ingredients_text}
        
        {recipe_name_text}
        
        Для каждого рецепта укажи:
        1. Креативное название (если не указано)
        2. Список всех ингредиентов с точными измерениями
        3. Пошаговые инструкции по приготовлению
        4. Примерное время приготовления
        5. Краткое описание блюда
        
        Формат каждого рецепта должен быть в виде JSON объекта со следующей структурой:
        {{
            "name": "Название рецепта",
            "description": "Краткое описание",
            "cooking_time": время_приготовления_в_минутах,
            "ingredients": [
                {{"name": "Ингредиент1", "amount": "количество", "measurement_unit": "единица измерения"}},
                {{"name": "Ингредиент2", "amount": "количество", "measurement_unit": "единица измерения"}}
            ],
            "instructions": [
                "Шаг 1: Инструкция",
                "Шаг 2: Инструкция"
            ]
        }}
        
        Верни массив из {count} объектов рецептов в формате JSON.
        """
        
        logger.info(f"Sending request to OpenAI API for {count} recipes")
        
        try:
            response = requests.post(
                self.api_url,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}"
                },
                json={
                    "model": "gpt-4o",
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 4000
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                
                import json
                import re
                
                json_match = re.search(r'\[\s*{.*}\s*\]', content, re.DOTALL)
                if json_match:
                    recipes_json = json_match.group(0)
                    recipes = json.loads(recipes_json)
                    logger.info(f"Successfully generated {len(recipes)} recipes")
                    return recipes
                
                logger.error("Failed to parse JSON response from OpenAI API")
                raise ValueError("Failed to parse recipe data from API response")
            else:
                logger.error(f"OpenAI API returned status code {response.status_code}: {response.text}")
                raise ValueError(f"Recipe generation API returned error: {response.status_code}")
                
        except Exception as e:
            logger.exception(f"Error generating recipes: {str(e)}")
            raise ValueError(f"Failed to generate recipes: {str(e)}") 