from django.test import SimpleTestCase
from ortools.sat.python import cp_model

from .constraints import (
    add_consecutive_forbidden_constraint,
    add_teacher_exclusion_constraint,
)


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
