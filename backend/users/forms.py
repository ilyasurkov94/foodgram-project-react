from django.forms.models import BaseInlineFormSet
from django.forms import ValidationError


class IngredientAmountFormset(BaseInlineFormSet):
    def clean(self):
        raise ValidationError(f'{self.forms}')
        if self.cleaned_data is None:
            raise ValidationError('Заполните данные ингредиентов')
        if self.cleaned_data == [{}]:
            raise ValidationError('Заполните данные ингредиентов')
        for data in self.cleaned_data:
            if data.get('ingredient') is None:
                raise ValidationError('Добавьте ингредиент')
            elif data.get('amount') is None:
                raise ValidationError('Заполните количество ингредиента')
