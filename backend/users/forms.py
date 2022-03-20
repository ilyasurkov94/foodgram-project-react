from django import forms


class IngredientAmountFormset(forms.models.BaseInlineFormSet):
    def clean(self):
        if not self.cleaned_data:
            raise forms.ValidationError('Заполните данные ингредиентов')
