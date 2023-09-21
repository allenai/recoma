import logging

import requests

from recoma.models.core.base_model import BaseModel

logger = logging.getLogger(__name__)


class ClientAPIModel(BaseModel):
    """
    Simple Base Model that connects to a client at host:port/path
    """
    def __init__(self, host: str, port: int, path: str, **kwargs):
        super().__init__(**kwargs)
        self.host = host
        self.port = port
        self.path = path

    def get_request_output(self, input_params):
        r = requests.get('http://{}:{}/{}'.format(self.host, self.port, self.path),
                         params=input_params)
        logger.debug("Requesting: {}".format(r.url))
        return r.text

