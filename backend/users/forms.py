from django import forms
from recipes.models import Recipe


class RecipeForm(forms.ModelForm):
    class Meta:
        model = Recipe
        fields = ('author', 'name', 'image', 'text',
                  'tags', 'cooking_time')

    def clean(self):
        """
        Проверка наличия ингредиентов
        """
        ingredient = self.cleaned_data.get('ingredient')
        if ingredient:
            return self.cleaned_data
        raise forms.ValidationError('Заполните данные ингредиента')
