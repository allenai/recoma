
from typing import Dict
from intercode.assets import sql_build_docker, sql_image_name, sql_test_data
from intercode.assets import bash_build_docker, bash_image_name, bash_test_data
from intercode.envs import SqlEnv, BashEnv


env=None

def preprocess_sql(record: Dict) -> str:
    db = record["extra"]["db"]
    return f"use {db}"

def load_env(env_name, data_path):
    if env_name == 'sql':
        sql_build_docker()
        env = SqlEnv(image_name=sql_image_name,
                data_path=data_path, preprocess=preprocess_sql)
    elif env_name == 'bash':
        bash_build_docker()
        env = BashEnv(image_name=bash_image_name,
                data_path=data_path)
    else:
        raise ValueError(f'Environment {env_name} not recognized')


def reset_example(example_id):
    env.reset(example_id)

