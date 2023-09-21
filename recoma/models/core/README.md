## Core Models

* [BaseModel](/recoma/models/core/base_model.py): This is the base model that every other model needs
to inherit and register (e.g. `@BaseModel.register("prompted_lm")`). The key function to implement
is the `__call__` method that takes a search state and generates new search state(s) to explore. The
controller will call this method of a target model when the current node in the search state is
assigned to that model.

* [Generator](/recoma/models/core/generator.py): This is the base text-in text-out model. Every text
generator must inherit from this model and register as `@Generator.register(...)`.

* [PromptedLMModel](/recoma/models/core/prompted_lm_model.py): This is an implementation of BaseModel
for prompted LMs. The model constructor takes two arguments:
  - `prompt_file`: A Jinja2 template file used to build the input prompt for the generator. Available
parameters by default: input_str, question, paras
  - `generator_params`: A dict of named parameters used to construct a `Generator` object. This
generator is run against the input prompt and the generated output is added to the current node.

* Two utility models in [utility_models.py](/recoma/models/core/utility_models.py)
  - *RegexExtractor*: Extracts a string from input_str and passes it on as the output.
  - *RouterModel*: Extracts a target model name from input_str and passes the remaining question to this
target model.