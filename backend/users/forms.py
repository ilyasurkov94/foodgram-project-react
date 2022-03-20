from django import forms
from recipes.models import IngredientAmount


class IngredientAmountForm(forms.ModelForm):
    class Meta:
        model = IngredientAmount
        fields = ['ingredient', 'amount']

    def clean(self):
        """
        Проверка наличия информации о рецепте
        """
        ingredient = self.cleaned_data.get('ingredient')
        amount = self.cleaned_data.get('amount')
        if ingredient and amount:
            return self.cleaned_data
        raise forms.ValidationError('Заполните данные ингредиента')
