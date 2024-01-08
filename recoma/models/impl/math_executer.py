import logging
import math
import json

from sympy import solve

from recoma.models.core.base_model import BaseModel
from recoma.models.core.generator import GenerationOutputs
from recoma.search.state import SearchState

logger = logging.getLogger(__name__)


def lcm(a, b):  # for backwards compatibility with Python<3.9
    return (a * b) // math.gcd(a, b)


def solve_it(equation, variable):
    solution = solve(equation, variable, dict=True)
    if not solution:
        if isinstance(variable, list):
            solution = {v: None for v in variable}
        else:
            solution = {variable: None}
        return solution
    else:
        solution = solution[0]
        return solution


@BaseModel.register("math_exec")
class MathProgramExecuter(BaseModel):

    def generate_output(self, state: SearchState) -> GenerationOutputs:
        curr_node = state.get_open_node()
        if curr_node is None:
            raise ValueError("Model called without any open node!!")
        input_prog = curr_node.input_str
        output = self.eval_program(input_prog)
        curr_node.input_str = "```\n" + curr_node.input_str + "\n```"
        return GenerationOutputs(outputs=[output])

    def eval_program(self, input_prog):
        input_locals = {}
        input_prog = input_prog.replace("\\n", "\n")
        try:
            compiled_prog = compile(input_prog, 'temp', 'exec')
            exec(compiled_prog, globals(), input_locals)
            return json.dumps(input_locals["answer"])
        except Exception:
            logger.error("could not execute code: {}".format(input_prog))
            return ""
