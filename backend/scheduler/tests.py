from django.test import SimpleTestCase, TestCase
from ortools.sat.python import cp_model

from core.models import (
    SchedulerSettings, SchoolClass, Subject, Teacher, TeacherQualification,
)

from .constraints import (
    add_consecutive_forbidden_constraint,
    add_teacher_exclusion_constraint,
)
from .engine import ScheduleEngine


class ConsecutiveForbiddenConstraintTests(SimpleTestCase):
    def find_linear_constraints(self, model, vars_set):
        matched = []
        for constraint in model.Proto().constraints:
            if not constraint.has_linear():
                continue
            linear = constraint.linear
            if set(linear.vars) != vars_set:
                continue
            if any(coeff != 1 for coeff in linear.coeffs):
                continue
            matched.append(linear)
        return matched

    def test_h9_blocks_teacher_consecutive_classes_across_forbidden_boundary(self):
        model = cp_model.CpModel()
        class_a_period_2 = model.NewBoolVar('class_a_period_2')
        class_b_period_3 = model.NewBoolVar('class_b_period_3')

        schedule_vars = {
            (1, 101): {(0, 1): class_a_period_2},
            (2, 102): {(0, 2): class_b_period_3},
        }
        teacher_assignments = {
            10: [(1, 101), (2, 102)],
        }

        add_teacher_exclusion_constraint(model, schedule_vars, teacher_assignments)
        add_consecutive_forbidden_constraint(
            model,
            schedule_vars,
            teacher_assignments,
            forbidden_pairs=[(1, 2)],
        )

        matched = self.find_linear_constraints(
            model,
            {class_a_period_2.Index(), class_b_period_3.Index()},
        )
        self.assertEqual(len(matched), 1)

    def test_h9_does_not_block_non_forbidden_adjacent_periods(self):
        model = cp_model.CpModel()
        class_a_period_1 = model.NewBoolVar('class_a_period_1')
        class_b_period_2 = model.NewBoolVar('class_b_period_2')

        schedule_vars = {
            (1, 101): {(0, 0): class_a_period_1},
            (2, 102): {(0, 1): class_b_period_2},
        }
        teacher_assignments = {
            10: [(1, 101), (2, 102)],
        }

        add_teacher_exclusion_constraint(model, schedule_vars, teacher_assignments)
        add_consecutive_forbidden_constraint(
            model,
            schedule_vars,
            teacher_assignments,
            forbidden_pairs=[(1, 2)],
        )

        matched = self.find_linear_constraints(
            model,
            {class_a_period_1.Index(), class_b_period_2.Index()},
        )
        self.assertEqual(matched, [])


class HomeroomMainSubjectAssignmentTests(TestCase):
    """H14: 班主任必须担任主课开关在教师自动分配阶段的行为。"""

    def setUp(self):
        self.settings = SchedulerSettings.get_settings()
        # 一门主课 + 一门副课
        self.chinese = Subject.objects.create(
            name='语文', weekly_hours=1, is_main_subject=True
        )
        self.pe = Subject.objects.create(
            name='体育', weekly_hours=1, max_teacher_classes=5
        )
        # 班主任只有副课资质，另一位教师才有主课资质
        self.homeroom = Teacher.objects.create(name='班主任')
        self.other = Teacher.objects.create(name='主课老师')
        self.klass = SchoolClass.objects.create(
            name='一年级1班', grade=1, homeroom_teacher=self.homeroom
        )
        TeacherQualification.objects.create(teacher=self.homeroom, subject=self.pe)
        TeacherQualification.objects.create(teacher=self.other, subject=self.chinese)

    def _assign(self):
        engine = ScheduleEngine()
        engine.load_data()
        ok = engine.auto_assign_teachers()
        return engine, ok

    def test_enabled_blocks_homeroom_without_main_subject(self):
        self.settings.h14_homeroom_main_subject = True
        self.settings.save()

        engine, ok = self._assign()

        self.assertFalse(ok)
        self.assertTrue(
            any('必须' in e and '主课' in e for e in engine.errors),
            engine.errors,
        )

    def test_disabled_allows_homeroom_without_main_subject(self):
        self.settings.h14_homeroom_main_subject = False
        self.settings.save()

        engine, ok = self._assign()

        self.assertTrue(ok, engine.errors)
        self.assertFalse(any('主课' in e for e in engine.errors), engine.errors)

    def test_enabled_assigns_main_subject_to_qualified_homeroom(self):
        # 班主任同时具备主课资质时，应被优先分配主课
        TeacherQualification.objects.create(teacher=self.homeroom, subject=self.chinese)
        self.settings.h14_homeroom_main_subject = True
        self.settings.save()

        engine, ok = self._assign()

        self.assertTrue(ok, engine.errors)
        self.assertEqual(
            engine.class_subject_teacher[(self.klass.id, self.chinese.id)],
            self.homeroom.id,
        )
