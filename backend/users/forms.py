from django import forms


class IngredientAmountFormset(forms.models.BaseInlineFormSet):
    def clean(self):
        if self.cleaned_data is None:
            raise forms.ValidationError('Заполните данные ингредиентов')
        if self.cleaned_data == [{}]:
            raise forms.ValidationError('Заполните данные ингредиентов')
        for data in self.cleaned_data:
            if data.get('ingredient') is None:
                raise forms.ValidationError('Добавьте ингредиент')
            elif data.get('amount') is None:
                raise forms.ValidationError('Заполните количество ингредиента')
