import json

import logger

from recoma.models.base_models import BaseModel
from recoma.models.symbolic_models import ProgramExecuter


def get_values(json_data, key):
    values = []
    if isinstance(json_data, list):
        for item in json_data:
            values.extend(get_values(item, key))
    elif isinstance(json_data, dict):
        for k, v in json_data.items():
            if k == key:
                values.append(v)
            values.extend(get_values(json_data=v, key=key))
    return values


@BaseModel.register("skylight_exec")
class SkylightProgramExecuter(ProgramExecuter):

    def eval_program(self, input_prog):
        input_locals = {}
        input_prog = input_prog.replace("\\n", "\n")
        try:
            compiled_prog = compile(input_prog, 'temp', 'exec')
            exec(compiled_prog, globals(), input_locals)
            return json.dumps(input_locals["output"])
        except Exception:
            logger.error("could not execute code: {}".format(input_prog))
            return ""
