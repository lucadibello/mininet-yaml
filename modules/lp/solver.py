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
        solver = pywraplp.Solver.CreateSolver("SCIP_MIXED_INTEGER_PROGRAMMING")
        if not solver:
            raise UnavailableSolverError("GLOP solver unavailable.")
        # Save parameters
        self._solver = solver

    @property
    def solver(self):
        return self._solver

    def solve(self) -> LPResult:
        result = self.solver.Solve()

        # Extract all variables and their values
        variables = {}
        for variable in self.solver.variables():
            variables[variable.name()] = variable.solution_value()

        print("INTERNAL RESULT:", result)
        if result != pywraplp.Solver.OPTIMAL:
            if result == pywraplp.Solver.FEASIBLE:
                return GLOPSolver.LPResult(SolverStatus.FEASIBLE, 0, variables)
            else:
                return GLOPSolver.LPResult(SolverStatus.INFEASIBLE, 0, variables)
        return GLOPSolver.LPResult(SolverStatus.OPTIMAL, 0, variables)

    def set_verbose(self, verbose: bool):
        if verbose:
            self.solver.EnableOutput()
        else:
            self.solver.DisableOutput()
        