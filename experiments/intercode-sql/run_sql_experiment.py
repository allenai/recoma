import readline
from intercode.assets import sql_build_docker, sql_image_name, sql_test_data
from intercode.envs import SqlEnv

from typing import Dict

def preprocess(record: Dict) -> str:
    db = record["extra"]["db"]
    return f"use {db}"

if __name__ == '__main__':
    sql_build_docker()
    data_path = "data/sql/spider/ic_spider_dev.json"
    # data_path = "data/sql/wikisql/ic_wikisql_dev.json" # DOES NOT WORK
    env = SqlEnv(sql_image_name, data_path=data_path, preprocess=preprocess,
                 traj_dir="logs/", verbose=True)

    try:
        for idx in range(3):
            env.reset()
            obs, done = env.observation, False
            while not done:
                action = input('> ')
                obs, reward, done, info = env.step(action)
    except KeyboardInterrupt:
        print("Keyboard interrupt detected")
    finally:
        env.close()
