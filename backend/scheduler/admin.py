from django.contrib import admin
from .models import ScheduleResult, ScheduleEntry


class ScheduleEntryInline(admin.TabularInline):
    model = ScheduleEntry
    extra = 0
    readonly_fields = ('school_class', 'subject', 'teacher', 'day', 'period', 'is_locked')
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(ScheduleResult)
class ScheduleResultAdmin(admin.ModelAdmin):
    list_display = ('id', 'created_at', 'solve_status', 'solve_time_ms', 'is_active')
    list_filter = ('solve_status', 'is_active')
    readonly_fields = ('created_at', 'solve_status', 'solve_time_ms')
    inlines = [ScheduleEntryInline]


@admin.register(ScheduleEntry)
class ScheduleEntryAdmin(admin.ModelAdmin):
    list_display = ('result', 'school_class', 'subject', 'teacher', 'day', 'period', 'is_locked')
    list_filter = ('result', 'school_class', 'teacher', 'day', 'is_locked')
    search_fields = ('school_class__name', 'subject__name', 'teacher__name')
