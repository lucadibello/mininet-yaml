from enum import Enum

from ortools.init.python import init
from ortools.linear_solver import pywraplp

from modules.lp.lp_models import LPTask
from modules.util.exceptions import UnavailableSolverError

def setup_solver(func):
    # Setup CPP flags
    def setup():
        init.CppBridge.init_logging("solver.py")
        cpp_flags = init.CppFlags()
        cpp_flags.stderrthreshold = True
        cpp_flags.log_prefix = False
        init.CppBridge.set_flags(cpp_flags)
        return func()
    return setup

class SolverStatus(Enum):
    OPTIMAL = 0
    FEASIBLE = 1
    INFEASIBLE = 2
    
class GLOPSolver():
    """
    This class represents a Linear Programming solver that uses the GLOP backend from Google OR-Tools.
    """
    
    class LPResult():
        def __init__(self, status: SolverStatus, objective_value: float, variables: dict[str, float]) -> None:
            self.status = status
            self.objective_value = objective_value
            self.variables = variables

    def __init__(self, lp_task: LPTask) -> None:
        solver = pywraplp.Solver.CreateSolver("GLOP")
        if not solver:
            raise UnavailableSolverError("GLOB solver unavailable.")
        
        # Save parameters
        self._solver = solver
        self._lp_task = lp_task

    @property
    def solver(self):
        return self._solver

    @setup_solver
    def solve(self) -> LPResult:
        # FIXME: setup the LP problem from the LPTask
        raise NotImplementedError("Still in development!")
        result = self.solver.Solve()
        
        # FIXME: This must be implemented
        if result != pywraplp.Solver.OPTIMAL:
            if result == pywraplp.Solver.FEASIBLE:
                return GLOPSolver.LPResult(SolverStatus.FEASIBLE, 0, {})
            else:
                return GLOPSolver.LPResult(SolverStatus.INFEASIBLE, 0, {})
        return GLOPSolver.LPResult(SolverStatus.OPTIMAL, 0, {})