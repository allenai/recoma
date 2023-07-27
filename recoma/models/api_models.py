import json
import logging

import requests

from recoma.models.base_models import BaseModel
from recoma.models.generator import GenerationOutputs
from recoma.search.state import SearchState

logger = logging.getLogger(__name__)


class ClientAPIModel(BaseModel):

    def __init__(self, host: str, port: int, path: str, **kwargs):
        super().__init__(**kwargs)
        self.host = host
        self.port = port
        self.path = path

    def get_request_output(self, input_params):
        r = requests.get('http://{}:{}/{}'.format(self.host, self.port, self.path),
                         params=input_params)
        logger.debug("Requesting: {}".format(r.url))
        print(r.text)
        return r.text


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
        question = json_data["obs"]
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
        output_observation = json_data["obs"][0]
        return GenerationOutputs(outputs=[output_observation], metadata=[json_data])
