from django.contrib import admin

from .models import Group, Post


class PostAdmin(admin.ModelAdmin):
    empty_value_display = '-пусто-'
    list_display = (
        'pk',
        'text',
        'created',
        'author',
        'group',
    )
    list_editable = ('group',)
    list_filter = ('created',)
    search_fields = ('text',)


admin.site.register(Post, PostAdmin)
admin.site.register(Group)
