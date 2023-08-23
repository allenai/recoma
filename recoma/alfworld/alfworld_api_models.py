import json

from recoma.alfworld.alf_utils import get_observation
from recoma.models.core.api_models import ClientAPIModel
from recoma.models.core.base_model import BaseModel
from recoma.models.core.generator import GenerationOutputs
from recoma.search.state import SearchState


@BaseModel.register("alf_loader")
class AlfWorldGameLoaderModel(ClientAPIModel):

    def load_new_game(self, game_file):
        params = {
            "output_only": "true",
            "game_file":  game_file
        }
        return self.get_request_output(params)

    def generate_output(self, state: SearchState) -> GenerationOutputs:
        game_output = self.load_new_game(state.example.qid)
        json_data = json.loads(game_output)
        question = get_observation(json_data)
        state.example.question = question
        return GenerationOutputs(outputs=[question], metadata=[json_data])


@BaseModel.register("alf_action")
class AlfWorldActionModel(ClientAPIModel):

    def generate_output(self, state: SearchState) -> GenerationOutputs:
        api_params = {
            "action": state.get_open_node().input_str,
            "output_only": "true"
        }
        api_output = self.get_request_output(input_params=api_params)
        json_data = json.loads(api_output)
        output_observation = get_observation(json_data)
        return GenerationOutputs(outputs=[output_observation], metadata=[json_data])
