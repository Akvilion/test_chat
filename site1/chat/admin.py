from django.contrib import admin, messages
from .models import Thread, Message


class ThreadAdmin(admin.ModelAdmin):
    list_display = ('id', 'created', 'updated')
    search_fields = ('participants__username',)
    filter_horizontal = ('participants',)
    readonly_fields = ('created', 'updated')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related('participants')

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        if form.instance.participants.count() > 2:
            form.instance.participants.clear()
            form.instance.save()
            messages.error(request, "A thread cannot have more than 2 participants.")

class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'sender', 'thread', 'created', 'is_read')
    list_filter = ('is_read',)
    search_fields = ('sender__username', 'text', 'thread__id')
    readonly_fields = ('created',)


admin.site.register(Thread, ThreadAdmin)
admin.site.register(Message, MessageAdmin)
