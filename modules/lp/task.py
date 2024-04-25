class LPTask():
    """
    This class describes a Linear Programming problem with useful methods to interact with external tools/libraries.
    """
    
    def __init__(self, objective: str, is_maximization: bool = True, subject_to: list = [], variables: dict[str, float] = {}) -> None:
        self.objective = objective
        self.is_maximization = is_maximization
        self.subject_to = subject_to
        self.variables = variables
    
    def to_cplex(self) -> str:
        """
        This method returns a string with the Linear Programming problem in CPLEX format.
        """

        raise NotImplementedError("Still in development!")
