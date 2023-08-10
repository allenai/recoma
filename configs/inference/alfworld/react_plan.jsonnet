local generator_params = import "../common/default_gpt_davinci003.libsonnet";
{
    "models": {
        "init": {
            "type": "alf_loader",
            "host": "localhost",
            "port": 5001,
            "path": "play",
            "next_model": "exec_ifnot_plan"
        },
        "exec_ifnot_plan": {
            "type": "alf_conditional_exec",
            "executer_model": "exec",
            "planner_model": "plan",
            "alf_client_model": {
                 "host": "localhost",
                 "port": 5001,
                 "path": "play",
             }
        },
        "plan": {
            "type": "alf_planner",
            "prompt_file": "configs/prompts/alfworld/planner.txt",
            "next_model": "exec_ifnot_plan",
            "generator_params": generator_params + {"stop": ["\n\n"], "max_tokens": 300},
        },
        "exec": {
            "type": "alf_executer",
            "react_model": "react",
            "action_model": "alfworld",
            "max_steps": 20,
            "max_no_progress_steps": 3
        },
        "react": {
            "type": "prompted_lm",
            "prompt_file": "configs/prompts/alfworld/atomic_executer.txt",
            "generator_params": generator_params,
        },
        "alfworld": {
            "type": "alf_action",
            "host": "localhost",
            "port": 5001,
            "path": "play"
        },
    },
    "search": {
        "type": "best_first",
        "max_search_iters": 200,
        "max_search_depth": 6,
        "start_model": "init",
        "answerer": {
            "type": "alf_reward"
        }
    },
    "reader": {
      "type": "drop",
      "add_paras": true
    }
}