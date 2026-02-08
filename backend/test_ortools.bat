@echo off
cd /d "%~dp0"
call venv\Scripts\activate
python -c "from ortools.sat.python import cp_model; model = cp_model.CpModel(); x = model.NewBoolVar('x'); y = model.NewBoolVar('y'); model.Add(x + y == 1); solver = cp_model.CpSolver(); status = solver.Solve(model); print('Status:', status); print('x=', solver.Value(x), 'y=', solver.Value(y)); print('OR-Tools works!')"
