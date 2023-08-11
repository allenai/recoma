import json
import logging
import os
from json import JSONDecodeError

import requests

from recoma.models.base_models import BaseModel
from recoma.models.generator import GenerationOutputs
from recoma.search.state import SearchState

logger = logging.getLogger(__name__)


@BaseModel.register("skylight_api")
class SkylightAPIModel(BaseModel):

    def __init__(self, host: str, **kwargs):
        super().__init__(**kwargs)
        self.host = host
        self.token = os.environ['SKYLIGHT_TOKEN']
        self.ignore_keys = ["_index", "_id", "_score", "fishing_score"]

    def generate_output(self, state: SearchState) -> GenerationOutputs:
        current_node = state.get_open_node()
        api_path = current_node.input_str
        print(api_path)
        r = requests.get('http://{}/{}'.format(self.host, api_path),
                         headers={"Authorization": "Bearer {}".format(self.token)})
        logger.debug("Requesting: {}".format(r.url))
        logger.debug("Output: {}".format(r.text))
        try:
            output_json = json.loads(r.text)
        except JSONDecodeError:
            logger.error("Could not parse the response: {}".format(r.text))
            return GenerationOutputs(outputs=[])

        output_json = self.clean_json(output_json)
        return GenerationOutputs(outputs=[json.dumps(output_json)])

    def clean_json(self, output_json):
        # Remove unnecessary fields to save token budget
        while "hits" in output_json:
            output_json = output_json["hits"]
        return output_json
