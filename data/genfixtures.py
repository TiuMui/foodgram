import json

app_name = 'recipes'
model_name = 'ingredient'

with open('ingredients.json', 'r', encoding='utf-8') as file:
    data = json.load(file)

fixtures = []
for index, item in enumerate(data, start=1):
    fixture = {
        'model': f'{app_name}.{model_name}',
        'pk': index,
        'fields': item
    }
    fixtures.append(fixture)
with open('ingredients_fixtures.json', 'w', encoding='utf-8') as file:
    json.dump(fixtures, file, ensure_ascii=False, indent=4)

print('Фикстуры успешно созданы!')
