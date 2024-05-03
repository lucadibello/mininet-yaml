from abc import abstractmethod
from enum import Enum
from typing import Union

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
    
class CBCMIPSolver(LpSolver):
    """
    This class represents a Linear Programming solver that uses the GLOP backend from Google OR-Tools.
    """
    
    class LPResult():
        def __init__(self, status: SolverStatus, objective_value: float, variables: dict[str, Union[int,float]], constraints: dict[str, Union[int,float]]) -> None:
            self.status = status
            self.objective_value = objective_value
            self.variables = variables
            self.constraints = constraints

    def __init__(self) -> None:
        super().__init__()
        # Create the solver
        solver = pywraplp.Solver.CreateSolver("CBC_MIXED_INTEGER_PROGRAMMING")
        if not solver:
            raise UnavailableSolverError("CBC_MIXED_INTEGER_PROGRAMMING solver unavailable.")
        # Save parameters
        self._solver = solver

    @property
    def solver(self):
        return self._solver

    def solve(self) -> LPResult:
        result = self.solver.Solve()
 
        # Extract all variables and their values
        variables = dict[str, Union[int,float]]()
        for variable in self.solver.variables():
            variables[variable.name()] = variable.solution_value()

        # Get objective value
        objective_value = self.solver.Objective().Value()
        if result == pywraplp.Solver.OPTIMAL or result == pywraplp.Solver.FEASIBLE:
            # compute constraint activities
            activities = self.solver.ComputeConstraintActivities()
            constraints = dict[str, Union[int,float]]()
            for constraint in self.solver.constraints():
                constraints[constraint.name()] = activities[constraint.index()]

            actual_result = SolverStatus.OPTIMAL if result == pywraplp.Solver.OPTIMAL else SolverStatus.FEASIBLE
            return CBCMIPSolver.LPResult(actual_result, objective_value, variables, constraints)
        else:
            return CBCMIPSolver.LPResult(SolverStatus.INFEASIBLE, objective_value, variables, {})

    def set_verbose(self, verbose: bool):
        if verbose:
            self.solver.EnableOutput()
        else:
            self.solver.DisableOutput()
        