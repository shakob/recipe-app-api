from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient, Recipe
from recipe.serializers import IngredientSerializer

INGREDIENTS_URL = reverse('recipe:ingredient-list')


class PublicIngredientsApiTests(TestCase):
    """Test the publicly available ingredients API"""

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        """Test that login is required to access this endpoint"""
        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientsAPITests(TestCase):
    """Test ingredients can be retrieved by authorized user"""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email='test1@test.com',
            password='testpass'
        )
        self.client.force_authenticate(self.user)

    def test_retrieve_ingredient_list(self):
        """Test retrieving a list of ingredients"""

        # Create ingredient with 'self.user' user
        Ingredient.objects.create(user=self.user, name='kale')
        Ingredient.objects.create(user=self.user, name='salt')

        res = self.client.get(INGREDIENTS_URL)

        ingredients = Ingredient.objects.all().order_by('-name')
        serializer = IngredientSerializer(ingredients, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_ingredients_limited_to_user(self):
        """Test that only ingredients for authenticated user are returned"""
        user2 = get_user_model().objects.create_user(
            'other@test.com',
            'testpass'
        )
        Ingredient.objects.create(user=user2, name='Vinegar')

        ingredient = Ingredient.objects.create(user=self.user, name='tumeric')

        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        # Check that the ingredient name is not Vinegar - (belongs to other user)
        self.assertEqual(res.data[0]['name'], ingredient.name)

    def test_create_ingredient_successful(self):
        """Test creating a new ingredient"""
        payload = {'name': 'Cabbage'}
        self.client.post(INGREDIENTS_URL, payload)

        exists = Ingredient.objects.filter(
            user=self.user,
            name=payload['name']
        ).exists()
        self.assertTrue(exists)

    def test_create_ingredient_invalid(self):
        """Test creating invalid ingredient fails"""
        payload = {'name': ''}
        res = self.client.post(INGREDIENTS_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_tags_assigned_to_recipes(self):
        """Test filtering ingredient by those assigned to recipes"""
        ing1 = Ingredient.objects.create(user=self.user, name='Apples')
        ing2 = Ingredient.objects.create(user=self.user, name='Turkey')

        recipe = Recipe.objects.create(
            title="Apple crumple",
            time_minutes=5,
            price=10.00,
            user=self.user
        )

        recipe.ingredients.add(ing1)
        res = self.client.get(INGREDIENTS_URL, {'assigned_only': 1})

        serializer1 = IngredientSerializer(ing1)
        serializer2 = IngredientSerializer(ing2)

        self.assertIn(serializer1.data, res.data)
        self.assertNotIn(serializer2.data, res.data)

    def test_retrieve_tags_assigned_unique(self):
        """Test filtering ingredient by assigned returns unique items"""
        recipe1 = Recipe.objects.create(
            title="Eggs benedict",
            time_minutes=30,
            price=12.00,
            user=self.user
        )
        recipe2 = Recipe.objects.create(
            title="Coriander eggs on toast",
            time_minutes=20,
            price=5.00,
            user=self.user
        )
        ing = Ingredient.objects.create(user=self.user, name='Cheese')
        recipe1.ingredients.add(ing)
        recipe2.ingredients.add(ing)

        res = self.client.get(INGREDIENTS_URL, {'assigned_only': 1})

        self.assertEqual(len(res.data), 1)
