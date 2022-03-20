from django import forms


class IngredientAmountFormset(forms.models.BaseInlineFormSet):
    def clean(self):
        if not self.cleaned.data:
            raise forms.ValidationError('Заполните данные')
