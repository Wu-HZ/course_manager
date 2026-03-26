from django.db import transaction
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import ScheduleResult, ScheduleEntry
from .serializers import (
    ScheduleResultSerializer, ScheduleResultListSerializer,
    ScheduleResultRenameSerializer, ScheduleEntrySerializer
)
from .engine import run_scheduler


@api_view(['POST'])
def run_schedule(request):
    """触发排课（支持自动重试）"""
    time_limit = request.data.get('time_limit_seconds', 300)
    max_attempts = request.data.get('max_attempts', 50)
    total_timeout = request.data.get('total_timeout_seconds', 600)

    result = run_scheduler(
        time_limit_seconds=time_limit,
        max_attempts=max_attempts,
        total_timeout_seconds=total_timeout
    )

    retry_stats = result.get('retry_stats', {})

    if result['success']:
        serializer = ScheduleResultSerializer(result['result'])
        return Response({
            'success': True,
            'status': result['status'],
            'solve_time_ms': result['solve_time_ms'],
            'auto_assigned_count': result.get('auto_assigned_count', 0),
            'result': serializer.data,
            'retry_stats': retry_stats,
        })
    else:
        data = {
            'success': False,
            'errors': result['errors'],
            'diagnostics': result.get('diagnostics', []),
            'status': result.get('status', 'UNKNOWN'),
            'solve_time_ms': result.get('solve_time_ms', 0),
            'auto_assigned_count': result.get('auto_assigned_count', 0),
            'retry_stats': retry_stats,
        }
        if result.get('result'):
            data['result_id'] = result['result'].id
        return Response(data, status=status.HTTP_400_BAD_REQUEST)


class ScheduleResultViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet
):
    queryset = ScheduleResult.objects.all()
    http_method_names = ['get', 'patch', 'delete', 'head', 'options']

    def get_serializer_class(self):
        if self.action == 'list':
            return ScheduleResultListSerializer
        if self.action in ['partial_update', 'update']:
            return ScheduleResultRenameSerializer
        return ScheduleResultSerializer

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save(name=serializer.validated_data.get('name', '').strip())
        return Response(ScheduleResultListSerializer(instance).data)

    def perform_destroy(self, instance):
        with transaction.atomic():
            was_active = instance.is_active
            instance.delete()

            if not was_active:
                return

            fallback = ScheduleResult.objects.filter(
                solve_status__in=['OPTIMAL', 'FEASIBLE']
            ).order_by('-created_at').first()
            if fallback:
                fallback.is_active = True
                fallback.save(update_fields=['is_active'])


@api_view(['POST'])
def activate_result(request, pk):
    """设置某个排课结果为当前使用"""
    try:
        result = ScheduleResult.objects.get(pk=pk)
    except ScheduleResult.DoesNotExist:
        return Response({'error': '结果不存在'}, status=status.HTTP_404_NOT_FOUND)

    result.is_active = True
    result.save()
    return Response({'success': True})


@api_view(['GET'])
def active_schedule(request):
    """获取当前激活的排课结果"""
    result = ScheduleResult.objects.filter(is_active=True).first()
    if not result:
        return Response({'error': '没有激活的排课结果'}, status=status.HTTP_404_NOT_FOUND)

    serializer = ScheduleResultSerializer(result)
    return Response(serializer.data)


@api_view(['GET'])
def class_timetable(request, result_id, class_id):
    """获取某班级的课表"""
    entries = ScheduleEntry.objects.filter(
        result_id=result_id, school_class_id=class_id
    ).select_related('subject', 'teacher').order_by('day', 'period')
    serializer = ScheduleEntrySerializer(entries, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def teacher_timetable(request, result_id, teacher_id):
    """获取某教师的课表"""
    from core.models import Teacher, SchedulerSettings

    entries = ScheduleEntry.objects.filter(
        result_id=result_id, teacher_id=teacher_id
    ).select_related('school_class', 'subject').order_by('day', 'period')
    serializer = ScheduleEntrySerializer(entries, many=True)
    data = serializer.data

    # 检查该教师是否参与校本课程
    try:
        teacher = Teacher.objects.get(pk=teacher_id)
        result = ScheduleResult.objects.get(pk=result_id)

        if not teacher.exclude_from_combined:
            # 从排课结果中获取分组信息
            # 格式: {"分组名": {"周二": ["教师名"], "周四": ["教师名"]}, ...}
            combined_assignments = result.combined_class_assignments or {}
            teacher_name = teacher.name

            # 查找教师在哪个分组的哪个日期
            assigned_day = None
            assigned_group = None
            for group_name, day_data in combined_assignments.items():
                if isinstance(day_data, dict):
                    if teacher_name in day_data.get("周二", []):
                        assigned_day = 1  # 周二
                        assigned_group = group_name
                        break
                    elif teacher_name in day_data.get("周四", []):
                        assigned_day = 3  # 周四
                        assigned_group = group_name
                        break

            if assigned_day is not None:
                # 获取校本课程时段
                settings = SchedulerSettings.objects.first()
                if settings:
                    combined_slots = settings.get_combined_class_slots_list()

                    # 只添加该教师分配日期的校本课程时段
                    for day, period in combined_slots:
                        if day == assigned_day:
                            data.append({
                                'id': None,
                                'day': day,
                                'period': period,
                                'subject_name': '校本课程',
                                'school_class_name': f'({assigned_group})',
                                'teacher_name': teacher_name,
                                'is_locked': True,
                            })
    except (Teacher.DoesNotExist, ScheduleResult.DoesNotExist):
        pass

    # 按 day, period 排序
    data.sort(key=lambda x: (x['day'], x['period']))
    return Response(data)
