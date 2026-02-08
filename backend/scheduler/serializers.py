from rest_framework import serializers
from .models import ScheduleResult, ScheduleEntry


class ScheduleEntrySerializer(serializers.ModelSerializer):
    school_class_name = serializers.CharField(source='school_class.name', read_only=True)
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    teacher_name = serializers.CharField(source='teacher.name', read_only=True)

    class Meta:
        model = ScheduleEntry
        fields = [
            'id', 'school_class', 'school_class_name',
            'subject', 'subject_name',
            'teacher', 'teacher_name',
            'day', 'period', 'is_locked'
        ]


class ScheduleResultSerializer(serializers.ModelSerializer):
    entries = ScheduleEntrySerializer(many=True, read_only=True)
    entry_count = serializers.IntegerField(source='entries.count', read_only=True)

    class Meta:
        model = ScheduleResult
        fields = [
            'id', 'created_at', 'is_active', 'solve_status',
            'solve_time_ms', 'notes', 'entries', 'entry_count'
        ]


class ScheduleResultListSerializer(serializers.ModelSerializer):
    entry_count = serializers.IntegerField(source='entries.count', read_only=True)

    class Meta:
        model = ScheduleResult
        fields = [
            'id', 'created_at', 'is_active', 'solve_status',
            'solve_time_ms', 'notes', 'entry_count'
        ]
