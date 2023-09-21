# ReComA: A Library for *Re*asoning via *Com*municating *A*gents
ReComA is a library designed to enable easy development of solutions for reasoning problems via
communicating agents. It is a generalization of the codebase for
[Decomposed Prompting](https://github.com/allenai/DecomP). The key features of the library:
- A general-purpose framework that implements many existing approaches for reasoning
via mutliple agents --
  [DecomP](https://www.semanticscholar.org/paper/Decomposed-Prompting%3A-A-Modular-Approach-for-Tasks-Khot-Trivedi/07955e96cbd778d0ae2a68f09d073b866dd84c2a),
  [ReACT](https://www.semanticscholar.org/paper/ReAct%3A-Synergizing-Reasoning-and-Acting-in-Language-Yao-Zhao/2d2ca2e54c54748557b8aac7d328ce32ebfe8944),
  [Least-to-Most](https://www.semanticscholar.org/paper/Least-to-Most-Prompting-Enables-Complex-Reasoning-Zhou-Scharli/5437e8adab596d7294124c0e798708e050e25321),
  [Faithful CoT](https://www.semanticscholar.org/paper/Faithful-Chain-of-Thought-Reasoning-LYU-Havaldar/ea0688f9e7dfb0d3c2249486af65209c25809544)
- Can be easily extended to use other control flows (e.g.,
  [Self-Ask](https://www.semanticscholar.org/paper/Measuring-and-Narrowing-the-Compositionality-Gap-in-Press-Zhang/53c20f7bf3fabc88e1403e00241eec009cc01ed8),
  [IRCoT](https://www.semanticscholar.org/paper/Interleaving-Retrieval-with-Chain-of-Thought-for-Trivedi-Balasubramanian/f208ea909fa7f54fea82def9a92fd81dfc758c39))
- Provides an interactive GUI which includes the entire reasoning trace (with underlying prompts) for easy debugging
- Built-in Best-First Search to explore multiple reasoning traces
- Can be used as a pip-installable library in your own codebase
- Configurable via JSONNET files -- no code change needed for many use cases

Table of Contents
===============

* [Setup](#Setup)
* [Running ReComA](#Running-ReComA)
* [Using ReComA](#Using-ReComA-in-your-work)


## Setup

If you want to directly make changes in this library, set it up using conda
```shell
  conda create -n recoma python=3.9
  conda activate recoma
  pip install -r requirements.txt
```


To install it as a dependency in your own conda environment
```shell
  pip install -e .
```

**OpenAI Setup**
This library relies on the `OPENAI_API_KEY` environment variable to call GPT3+ models. Make sure
to set this env. variable
```shell
  export OPENAI_API_KEY=<key>
```

## Running ReComA
The library can be used to solve complex reasoning tasks in two modes:

### Demo/Interactive Mode

```shell
 python -m recoma.run_inference \
  --config configs/inference/letter_cat/decomp.jsonnet \
  --output_dir output/letter_cat_decomp/ \
  --gradio_demo
```
This will start an interactive server on http://localhost:7860 for the k<sup>th</sup> letter
concatenation task. Try the following question (no QID/Context needed):

> Take the letters at position 3 of the words in "Reasoning via Communicating Agents" and concatenate them using a space.

The library will use `text-davinci-002` model with Decomposed Prompting (specified via the input
config file) to answer this question. You can open the collapsed nodes (indicated with ▶) to see
the full execution trace (along with the prompts).

### Batch Inference Mode

To use the library to produce predictions for an input file (e.g. [the 3rd letter concatenation
dataset with 4 words](https://github.com/allenai/DecomP/blob/main/datasets/letter_cat/n4_eg100_pos2_space.json)):
```shell
 python -m recoma.run_inference \
  --config configs/inference/letter_cat/decomp.jsonnet \
  --output_dir output/letter_cat_decomp/ \
  --input datasets/letter_cat/n4_eg100_pos2_space.json
```

Running this script will populate the output directory with :
- `predictions.json`: qid-to-prediction map
- `all_data.jsonl`: Input examples with model predictions and correctness label (using exact match)
- `html_dump/`: Dump of the execution traces for all the examples in HTML format
- `source_config.json`: JSON config used to run this experiment (for future reproducibility)

## Using ReComA in your work

### Using existing agents
If the provided agents are sufficient for your work, you can use this library by just defining the
configuration files and prompts. See examples in the `configs/` folder.


### Defining a new agent
If you define a new agent (see the models [README](recoma/models/README.md)), you need to load
them when running inference. Assuming your agents are defined under the package `my_new_agents_pkg`
```shell
python -m recoma.run_inference \
  --config configs/inference/letter_cat/decomp.jsonnet \
  --output_dir output/letter_cat_decomp/ \
  --input datasets/letter_cat/n4_eg100_pos2_space.json \
  --include_package my_new_agents_pkg
```

Please reach out if there are any questions or issues.
