local generator_params = import "../common/default_gpt_gpt3.5.libsonnet";
{
    "models": {
        "qtoapi": {
            "type": "prompted_lm",
            "prompt_file": "configs/prompts/skylight/api_prompt.txt",
            "generator_params": generator_params,
        },
        "api": {
            "type": "skylight_api",
            "host": "sc-integration.skylight.earth",
        },
        "json_ext": {
            "type": "prompted_lm",
            "prompt_file": "configs/prompts/skylight/no_json_ext.txt",
            "generator_params": generator_params,
        },
        "executer": {
            "type": "skylight_exec"
        },
        "decomp": {
            "type": "decomp_lm",
            "prompt_file": "configs/prompts/skylight/basic_decomp.txt",
            "generator_params": generator_params,
            "use_number_format": true,
            "next_model": "router"
        },
         "router": {
            "type": "router"
        }
    },
    "search": {
        "type": "best_first",
        "start_model": "decomp"
    },
    "reader": {
      "type": "drop",
      "add_paras": true
    }
}