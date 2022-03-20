from django import forms


class IngredientAmountFormset(forms.models.BaseInlineFormSet):
    def clean(self):
        raise forms.ValidationError(f'{self.cleaned_data}')
        if not self.cleaned_data:
            raise forms.ValidationError('Заполните данные ингредиентов')
