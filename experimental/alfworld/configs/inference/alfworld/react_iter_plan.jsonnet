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
            "type": "react_controller",
            "react_model": "plan_gen",
            "action_model": "exec_ifnot_plan",
            "action_prefix": "Step:",
            "thought_prefix": "# Think:",
            "obs_prefix": "Result:",
            "eoq_re": "(.*Task completed!)"
        },
        "plan_gen": {
            "type": "prompted_lm",
            "prompt_file": "configs/prompts/alfworld/iter_planner.txt",
            "generator_params": generator_params,
        },
        "exec": {
            "type": "alf_react",
            "react_model": "alf_react_exec",
            "action_model": "alfworld",
            "max_steps": 15,
            "max_no_progress_steps": 3
        },
        "alf_react_exec": {
            "type": "prompted_lm",
            "prompt_file": "configs/prompts/alfworld/executerv2.1.txt",
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
        "max_search_iters": 400,
        "max_search_depth": 12,
        "start_model": "init",
        "answerer": {
            "type": "alf_reward"
        }
    },
    "reader": {
      "type": "alf"
    }
}