local generator_params = import "../common/default_gpt_gpt3.5.libsonnet";
{
    "models": {
        "qtoapi": {
            "type": "prompted_lm",
            "prompt_file": "configs/prompts/skylight/api_prompt.txt",
            "generator_params": generator_params,
            "next_model": "apitojson"
        },
        "apitojson": {
            "type": "skylight_api",
            "host": "sc-integration.skylight.earth",
        }
    },
    "search": {
        "type": "best_first",
        "start_model": "qtoapi"
    },
    "reader": {
      "type": "drop",
      "add_paras": true
    }
}