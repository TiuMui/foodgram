from django.contrib import admin

from users.models import CustomUser, Subscription


@admin.register(CustomUser)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        'username',
        'first_name',
        'last_name',
        'email',
        'is_staff',
        'subscribers_count',
        'recipes_count'
    )
    search_fields = ('email', 'username')

    @admin.display(description='Количество подписчиков')
    def subscribers_count(self, obj):
        return obj.subscribers.count()

    @admin.display(description='Количество рецептов')
    def recipes_count(self, obj):
        return obj.author_recipes.count()


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('subscriber', 'subscription')
    search_fields = ('subscriber', )


admin.site.empty_value_display = 'Не задано'
