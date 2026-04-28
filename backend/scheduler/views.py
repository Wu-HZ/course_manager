from collections import Counter, defaultdict

from django.db import transaction
from django.db.models import Count, Q
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import api_view, action
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from core.models import (
    ClassSubjectTeacher, Location, ScheduleLock, SchedulerSettings,
    SchoolClass, Subject, Teacher, TeacherBlockedTime, TeacherQualification
)
from .models import ScheduleResult, ScheduleEntry
from .serializers import (
    ScheduleResultSerializer, ScheduleResultListSerializer,
    ScheduleResultUpdateSerializer, ScheduleEntrySerializer
)
from .engine import run_scheduler


class ScheduleResultPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 200


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


def _preview_names(names, limit=3):
    names = [name for name in names if name]
    if not names:
        return ''
    if len(names) <= limit:
        return '、'.join(names)
    return f"{'、'.join(names[:limit])} 等{len(names)}项"


def _make_actions(*items):
    return [{'label': label, 'route': route} for label, route in items]


def _make_issue(key, title, detail, actions):
    return {
        'key': key,
        'title': title,
        'detail': detail,
        'actions': actions,
    }


def _make_step(key, title, description, status_value, detail, actions):
    return {
        'key': key,
        'title': title,
        'description': description,
        'status': status_value,
        'detail': detail,
        'actions': actions,
    }


def _build_precheck_payload():
    settings = SchedulerSettings.get_settings()
    class_meeting_name = settings.class_meeting_name

    teachers = list(Teacher.objects.all())
    classes = list(SchoolClass.objects.all())
    subjects = list(Subject.objects.all())
    locations = list(Location.objects.all())
    assignments = list(
        ClassSubjectTeacher.objects.select_related('school_class', 'subject', 'teacher').all()
    )
    qualifications = list(TeacherQualification.objects.all())
    locks = list(ScheduleLock.objects.select_related('school_class', 'subject').all())

    blocked_times_count = TeacherBlockedTime.objects.count()
    successful_results_count = ScheduleResult.objects.filter(
        solve_status__in=['OPTIMAL', 'FEASIBLE']
    ).count()

    subject_by_id = {subject.id: subject for subject in subjects}
    class_by_id = {school_class.id: school_class for school_class in classes}
    location_labels = dict(Location._meta.get_field('location_type').choices)

    regular_subjects = [
        subject for subject in subjects
        if not subject.is_combined_class and subject.name != class_meeting_name
    ]
    required_subjects = [
        subject for subject in regular_subjects
        if any(subject.is_applicable_for_grade(school_class.grade) for school_class in classes)
    ]

    qualification_map = defaultdict(set)
    for qualification in qualifications:
        qualification_map[qualification.subject_id].add(qualification.teacher_id)

    applicable_pairs = []
    applicable_pair_keys = set()
    for school_class in classes:
        for subject in regular_subjects:
            if not subject.is_applicable_for_grade(school_class.grade):
                continue
            applicable_pairs.append((school_class, subject))
            applicable_pair_keys.add((school_class.id, subject.id))

    total_school_hours = 0
    for school_class in classes:
        for subject in subjects:
            if not subject.is_applicable_for_grade(school_class.grade):
                continue
            total_school_hours += subject.weekly_hours

    average_teacher_hours = None
    if teachers:
        average_teacher_hours = round(total_school_hours / len(teachers), 1)

    assignment_map = {}
    for assignment in assignments:
        key = (assignment.school_class_id, assignment.subject_id)
        if key in applicable_pair_keys:
            assignment_map[key] = assignment

    expected_assignment_pairs_count = len(applicable_pairs)
    assignment_count = len(assignment_map)
    manual_assignment_count = sum(1 for assignment in assignment_map.values() if assignment.is_manual)
    auto_assignment_count = assignment_count - manual_assignment_count

    missing_assignment_pairs = [
        (school_class, subject)
        for school_class, subject in applicable_pairs
        if (school_class.id, subject.id) not in assignment_map
    ]
    invalid_assignments = [
        assignment for assignment in assignment_map.values()
        if assignment.teacher_id not in qualification_map.get(assignment.subject_id, set())
    ]
    subjects_without_qualification = [
        subject for subject in required_subjects
        if not qualification_map.get(subject.id)
    ]

    location_capacity = defaultdict(int)
    for location in locations:
        location_capacity[location.location_type] += max(location.capacity, 0)

    missing_location_types = sorted({
        subject.location_type
        for subject in required_subjects
        if subject.location_type != 'NORMAL' and location_capacity.get(subject.location_type, 0) <= 0
    })
    missing_location_labels = [location_labels.get(code, code) for code in missing_location_types]

    lock_counts = Counter((lock.school_class_id, lock.subject_id) for lock in locks)
    lock_overflows = []
    for (class_id, subject_id), count in lock_counts.items():
        subject = subject_by_id.get(subject_id)
        school_class = class_by_id.get(class_id)
        if not subject or not school_class:
            continue
        if count > subject.weekly_hours:
            lock_overflows.append({
                'class_name': school_class.name,
                'subject_name': subject.name,
                'lock_count': count,
                'weekly_hours': subject.weekly_hours,
            })

    blocking_issues = []
    if not teachers:
        blocking_issues.append(_make_issue(
            'missing_teachers',
            '未录入教师数据，无法排课',
            '请先录入至少 1 位任课教师或班主任。',
            _make_actions(('去教师管理', '/teachers')),
        ))
    if not classes:
        blocking_issues.append(_make_issue(
            'missing_classes',
            '未录入班级数据，无法排课',
            '请先录入需要参与排课的班级。',
            _make_actions(('去班级管理', '/classes')),
        ))
    if not subjects:
        blocking_issues.append(_make_issue(
            'missing_subjects',
            '未录入课程数据，无法排课',
            '请先录入课程周课时和适用年级。',
            _make_actions(('去课程管理', '/subjects')),
        ))
    if missing_location_labels:
        blocking_issues.append(_make_issue(
            'missing_locations',
            '存在课程需要专用场地，但场地容量未配置',
            f"以下场地类型尚未配置容量：{_preview_names(missing_location_labels)}。",
            _make_actions(('去课程管理', '/subjects'), ('去场地管理', '/locations')),
        ))
    if subjects_without_qualification:
        blocking_issues.append(_make_issue(
            'missing_qualifications',
            '仍有课程没有可授课教师',
            f"未设置可授课教师的课程：{_preview_names([subject.name for subject in subjects_without_qualification])}。",
            _make_actions(('去教师资质', '/qualifications')),
        ))
    if invalid_assignments:
        blocking_issues.append(_make_issue(
            'invalid_assignments',
            '存在授课分配与教师资质不一致',
            (
                '以下分配需要调整：'
                f"{_preview_names([f'{item.school_class.name}-{item.subject.name}-{item.teacher.name}' for item in invalid_assignments])}。"
            ),
            _make_actions(('去授课分配', '/assignments'), ('去教师资质', '/qualifications')),
        ))
    if lock_overflows:
        lock_overflow_preview = _preview_names([
            f"{item['class_name']}-{item['subject_name']} {item['lock_count']}/{item['weekly_hours']}"
            for item in lock_overflows
        ])
        blocking_issues.append(_make_issue(
            'lock_overflow',
            '存在课表锁定超过课程周课时上限',
            f'以下锁定需要调整：{lock_overflow_preview}。',
            _make_actions(('去课表锁定', '/schedule-locks')),
        ))

    warning_issues = []
    if expected_assignment_pairs_count and missing_assignment_pairs:
        warning_issues.append(_make_issue(
            'missing_assignments',
            f'仍有 {len(missing_assignment_pairs)} 个班级课程未手动指定教师',
            '系统会在排课时自动分配教师，但建议先确认主科、重点班级和需要固定教师的课程。',
            _make_actions(('去授课分配', '/assignments')),
        ))
    if blocked_times_count == 0:
        warning_issues.append(_make_issue(
            'missing_blocked_times',
            '尚未设置教师禁排时段',
            '如有外出、教研、跨校或固定不排课安排，建议先补充教师禁排时段。',
            _make_actions(('去教师禁排', '/blocked-times')),
        ))
    if len(locks) == 0:
        warning_issues.append(_make_issue(
            'missing_locks',
            '尚未设置课表锁定',
            '如有班会、固定活动或必须落在指定时间的课程，建议先做课表锁定。',
            _make_actions(('去课表锁定', '/schedule-locks')),
        ))

    can_run = len(blocking_issues) == 0

    steps = []
    steps.append(_make_step(
        'teachers',
        '教师管理',
        '录入任课教师、班主任和教师基础信息。',
        'completed' if teachers else 'pending',
        f"已录入 {len(teachers)} 位教师。" if teachers else '请先录入教师信息。',
        _make_actions(('去教师管理', '/teachers')),
    ))
    steps.append(_make_step(
        'classes',
        '班级管理',
        '录入班级、年级和班主任对应关系。',
        'completed' if classes else 'pending',
        f"已录入 {len(classes)} 个班级。" if classes else '请先录入班级信息。',
        _make_actions(('去班级管理', '/classes')),
    ))

    if not subjects:
        course_step_status = 'pending'
        course_step_detail = '请先录入课程信息。'
    elif missing_location_labels:
        course_step_status = 'blocked'
        course_step_detail = f"以下专用场地尚未配置：{_preview_names(missing_location_labels)}。"
    elif locations:
        course_step_status = 'completed'
        course_step_detail = f"已录入 {len(subjects)} 门课程，{len(locations)} 个场地。"
    else:
        course_step_status = 'completed'
        course_step_detail = f"已录入 {len(subjects)} 门课程；当前课程均可使用普通教室。"
    steps.append(_make_step(
        'subjects_locations',
        '课程与场地',
        '录入课程周课时、适用年级和专用场地容量。',
        course_step_status,
        course_step_detail,
        _make_actions(('去课程管理', '/subjects'), ('去场地管理', '/locations')),
    ))

    if not subjects or not classes:
        qualification_step_status = 'pending'
        qualification_step_detail = '请先录入班级和课程，再设置可授课教师。'
    elif subjects_without_qualification:
        qualification_step_status = 'blocked'
        qualification_step_detail = f"仍有 {len(subjects_without_qualification)} 门课程没有可授课教师。"
    else:
        qualification_step_status = 'completed'
        qualification_step_detail = '所有待排课程都已设置可授课教师。'
    steps.append(_make_step(
        'qualifications',
        '教师资质',
        '为每门待排课程设置可授课教师。',
        qualification_step_status,
        qualification_step_detail,
        _make_actions(('去教师资质', '/qualifications')),
    ))

    if invalid_assignments:
        assignment_step_status = 'blocked'
        assignment_step_detail = f"有 {len(invalid_assignments)} 条授课分配与教师资质不一致。"
    elif not expected_assignment_pairs_count:
        assignment_step_status = 'pending'
        assignment_step_detail = '当前还没有需要参与常规排课的班级课程。'
    elif not missing_assignment_pairs:
        assignment_step_status = 'completed'
        assignment_step_detail = f"已为全部 {expected_assignment_pairs_count} 个班级课程设置教师。"
    elif assignment_count == 0:
        assignment_step_status = 'warning'
        assignment_step_detail = '尚未手动指定教师，系统会在排课时按资质自动分配。'
    else:
        assignment_step_status = 'warning'
        assignment_step_detail = (
            f"已设置 {assignment_count}/{expected_assignment_pairs_count} 个班级课程教师，"
            '其余将由系统自动分配。'
        )
    steps.append(_make_step(
        'assignments',
        '授课分配',
        '为关键班级和课程指定任课教师，固定分配会优先保留。',
        assignment_step_status,
        assignment_step_detail,
        _make_actions(('去授课分配', '/assignments')),
    ))

    if blocked_times_count == 0 and len(locks) == 0:
        constraint_step_status = 'warning'
        constraint_step_detail = '尚未设置教师禁排或课表锁定，如有固定安排建议先补充。'
    else:
        constraint_step_status = 'completed'
        constraint_step_detail = f"已设置 {blocked_times_count} 条禁排时段，{len(locks)} 条课表锁定。"
    steps.append(_make_step(
        'constraints',
        '禁排与锁定',
        '设置教师禁排时段、固定活动和必须落位的课程。',
        constraint_step_status,
        constraint_step_detail,
        _make_actions(('去教师禁排', '/blocked-times'), ('去课表锁定', '/schedule-locks')),
    ))

    if successful_results_count > 0:
        run_step_status = 'completed'
        run_step_detail = f"已有 {successful_results_count} 个可用排课结果，可继续试排或查看历史。"
        run_actions = _make_actions(('查看课表', '/schedule-view'), ('去执行排课', '/schedule-run'))
    elif can_run:
        run_step_status = 'ready'
        run_step_detail = '基础检查已通过，可以开始排课。'
        run_actions = _make_actions(('去执行排课', '/schedule-run'))
    else:
        run_step_status = 'blocked'
        run_step_detail = f"仍有 {len(blocking_issues)} 个必须处理的问题，暂时不能开始排课。"
        run_actions = _make_actions(('查看排课检查', '/schedule-run'))
    steps.append(_make_step(
        'run',
        '执行排课',
        '检查关键数据后开始试排，并查看排课结果。',
        run_step_status,
        run_step_detail,
        run_actions,
    ))

    passed_checks = []
    if teachers:
        passed_checks.append({
            'key': 'teachers',
            'title': '教师数据已录入',
            'detail': f'当前共有 {len(teachers)} 位教师。',
        })
    if classes:
        passed_checks.append({
            'key': 'classes',
            'title': '班级数据已录入',
            'detail': f'当前共有 {len(classes)} 个班级。',
        })
    if subjects:
        passed_checks.append({
            'key': 'subjects',
            'title': '课程数据已录入',
            'detail': f'当前共有 {len(subjects)} 门课程。',
        })
    if required_subjects and not subjects_without_qualification:
        passed_checks.append({
            'key': 'qualifications',
            'title': '待排课程资质已覆盖',
            'detail': '所有待排课程都已配置可授课教师。',
        })
    if expected_assignment_pairs_count and not invalid_assignments:
        passed_checks.append({
            'key': 'assignments',
            'title': '现有授课分配与教师资质一致',
            'detail': '当前授课分配未发现资质冲突。',
        })
    if not lock_overflows:
        passed_checks.append({
            'key': 'locks',
            'title': '课表锁定未超出周课时',
            'detail': '当前锁定数据没有超过课程周课时上限。',
        })

    summary = {
        'teachers_count': len(teachers),
        'classes_count': len(classes),
        'subjects_count': len(subjects),
        'locations_count': len(locations),
        'assignments_count': assignment_count,
        'manual_assignments_count': manual_assignment_count,
        'auto_assignments_count': auto_assignment_count,
        'qualifications_count': len(qualifications),
        'blocked_times_count': blocked_times_count,
        'locks_count': len(locks),
        'successful_results_count': successful_results_count,
        'expected_assignment_pairs_count': expected_assignment_pairs_count,
        'missing_assignment_pairs_count': len(missing_assignment_pairs),
        'blocking_issue_count': len(blocking_issues),
        'warning_issue_count': len(warning_issues),
        'can_run': can_run,
        'completed_steps': sum(1 for step in steps if step['status'] == 'completed'),
        'total_steps': len(steps),
        'total_school_hours': total_school_hours,
        'average_teacher_hours': average_teacher_hours,
    }

    return {
        'summary': summary,
        'steps': steps,
        'blocking_issues': blocking_issues,
        'warning_issues': warning_issues,
        'passed_checks': passed_checks,
    }


@api_view(['GET'])
def schedule_precheck(request):
    """返回首页和排课页共用的排课前检查信息"""
    return Response(_build_precheck_payload())


class ScheduleResultViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet
):
    queryset = ScheduleResult.objects.all()
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']
    pagination_class = ScheduleResultPagination

    def get_queryset(self):
        qs = ScheduleResult.objects.annotate(entry_count=Count('entries'))
        params = self.request.query_params

        is_favorite = params.get('is_favorite')
        if is_favorite in ('true', '1'):
            qs = qs.filter(is_favorite=True)
        elif is_favorite in ('false', '0'):
            qs = qs.filter(is_favorite=False)

        solve_status = params.get('solve_status')
        if solve_status:
            qs = qs.filter(solve_status=solve_status)

        search = params.get('search')
        if search:
            qs = qs.filter(name__icontains=search.strip())

        return qs.order_by('-is_favorite', '-created_at')

    def get_serializer_class(self):
        if self.action == 'list':
            return ScheduleResultListSerializer
        if self.action in ['partial_update', 'update']:
            return ScheduleResultUpdateSerializer
        return ScheduleResultSerializer

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        save_kwargs = {}
        if 'name' in serializer.validated_data:
            save_kwargs['name'] = serializer.validated_data['name'].strip()
        if 'is_favorite' in serializer.validated_data:
            save_kwargs['is_favorite'] = serializer.validated_data['is_favorite']
        serializer.save(**save_kwargs)
        return Response(ScheduleResultListSerializer(instance).data)

    def perform_destroy(self, instance):
        with transaction.atomic():
            was_active = instance.is_active
            instance.delete()
            self._ensure_active_fallback(was_active)

    @action(detail=False, methods=['post'], url_path='bulk_delete')
    def bulk_delete(self, request):
        ids = request.data.get('ids') or []
        if not isinstance(ids, list) or not ids:
            return Response(
                {'error': '需要提供 ids 数组'},
                status=status.HTTP_400_BAD_REQUEST
            )

        with transaction.atomic():
            qs = ScheduleResult.objects.filter(pk__in=ids)
            had_active = qs.filter(is_active=True).exists()
            deleted_count, _ = qs.delete()
            self._ensure_active_fallback(had_active)

        return Response({'deleted': deleted_count})

    @staticmethod
    def _ensure_active_fallback(was_active):
        if not was_active:
            return
        fallback = ScheduleResult.objects.filter(
            solve_status__in=['OPTIMAL', 'FEASIBLE']
        ).order_by('-is_favorite', '-created_at').first()
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
