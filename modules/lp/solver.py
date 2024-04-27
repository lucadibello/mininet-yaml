from abc import abstractmethod
from enum import Enum

from ortools.init.python import init
from ortools.linear_solver import pywraplp

from modules.util.exceptions import UnavailableSolverError

class SolverStatus(Enum):
    OPTIMAL = 0
    FEASIBLE = 1
    INFEASIBLE = 2

class LpSolver():
    INFINITY = pywraplp.Solver.infinity()

    @abstractmethod
    def solve(self):
        pass

    def init_solver(self):
        init.CppBridge.init_logging("solver.py")
        cpp_flags = init.CppFlags()
        cpp_flags.stderrthreshold = True
        cpp_flags.log_prefix = False
        init.CppBridge.set_flags(cpp_flags)
    
class GLOPSolver(LpSolver):
    """
    This class represents a Linear Programming solver that uses the GLOP backend from Google OR-Tools.
    """
    
    class LPResult():
        def __init__(self, status: SolverStatus, objective_value: float, variables: dict[str, float]) -> None:
            self.status = status
            self.objective_value = objective_value
            self.variables = variables

    def __init__(self) -> None:
        super().__init__()
        # Create the solver
        solver = pywraplp.Solver.CreateSolver("GLOP")
        if not solver:
            raise UnavailableSolverError("GLOB solver unavailable.")
        # Save parameters
        self._solver = solver

    @property
    def solver(self):
        return self._solver

    def solve(self) -> LPResult:
        # Initialize the solver by setting the necessary CPP flags
        super().init_solver() 

        # FIXME: setup the LP problem from the LPTask
        result = self.solver.Solve()
        
        # FIXME: This must be implemented
        if result != pywraplp.Solver.OPTIMAL:
            if result == pywraplp.Solver.FEASIBLE:
                return GLOPSolver.LPResult(SolverStatus.FEASIBLE, 0, {})
            else:
                return GLOPSolver.LPResult(SolverStatus.INFEASIBLE, 0, {})
        return GLOPSolver.LPResult(SolverStatus.OPTIMAL, 0, {})