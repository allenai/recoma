from typing import Optional

from treelib import Tree, Node

from recoma.datasets.reader import Example
from recoma.models.generator import GenerationOutputs


class SearchNode(Node):
    def __init__(self, input_str: str, target_model: str,
                 is_open: bool = True, output: str = None, metadata={}):
        """
        Node in the SearchState tree
        :param input_str: Input string provided by the parent
        :param is_open: Is this node still to be resolved (i.e. execution not complete yet)?
        :param target_model: Which model should be assigned?
        :param output: Generated output using the target_model
        """
        super().__init__()
        self._is_open = is_open
        self.target = target_model
        self.output = output
        self.input_str = input_str
        self._tag = None
        # print("Metadata for " + input_str + " reset to " + str(metadata))
        self.metadata = metadata

    def is_open(self):
        return self._is_open

    def target_model(self):
        return self.target

    def close(self, output):
        self._is_open = False
        self.output = output

    @property
    def tag(self):
        if self._tag:
            return self._tag
        label = ""
        if self.is_open():
            label += "*"
        label += "[" + self.target + "] " + self.input_str + " ➡ " + \
                 (self.output if self.output is not None else "...")
        return label

    def add_input_output_prompt(self, input_str: str, output: GenerationOutputs):
        if "prompts" not in self.metadata:
            self.metadata["prompts"] = []
        # else:
        #     print("Current metadata: " + str(self.metadata["prompts"][0][1]))
        # print("Adding " + str([x for x in output.outputs]))
        self.metadata["prompts"].append((
            input_str,
            [x for x in output.outputs]
        ))

    def get_input_output_prompts(self):
        output = ""
        if "prompts" in self.metadata:
            for input_str, output_strs in self.metadata["prompts"]:
                output += "Input:\n" + input_str + "\n     ==>\n"
                for output_str in output_strs:
                    output += "\tOutput: " + output_str + "\n"
                output += "_" * 40 + "\n"
        return output


class SearchState(Tree):

    def __init__(self, example: Example = None, score=0,
                 **kwargs):
        super().__init__(node_class=SearchNode, **kwargs)
        self.example = example
        self.score = score

    def clone(self, identifier=None, with_tree=True, deep=True):
        # Reset the open node as the cloning might reset the identifiers
        return SearchState(example=self.example, score=self.score,
                           identifier=identifier, deep=deep, tree=self if with_tree else None)

    def get_open_node(self) -> SearchNode:
        # TODO Cache the depth first open node value. This is tricky because any non-local change
        # can change the first open node
        return self.get_depth_first_open_node()

    def get_depth_first_open_node(self) -> Optional[SearchNode]:
        for node_id in self.postorder_traversal():
            if node_id is not None and self[node_id].is_open():
                return self[node_id]
        return None

    def has_open_node(self):
        return self.get_open_node() is not None

    def get_depth_nth_node(self, nth: int):
        return self[list(self.expand_tree(mode=self.DEPTH, sorting=False))[nth]]

    def update_score(self, score):
        self.score += score

    def to_str_tree(self) -> str:
        return self.show(stdout=False, sorting=False) or ""

    def to_json_tree(self) -> str:
        return self.to_json(sort=False)

    def all_input_output_prompts(self) -> str:
        output_str = ""
        for nid in self.postorder_traversal():
            output_str += "Node: " + self[nid].tag + "\n"
            output_str += self[nid].get_input_output_prompts() + "\n"
            output_str += "=" * 40 + "\n"
        return output_str

    def get_children_ids(self, parent_id):
        """
        A wrapper around the non-intuitive is_branch function to get children
        :param parent_id: parent node id
        :return: list of children node ids (ordered left-to-right)
        """
        return self.is_branch(parent_id)

    def postorder_traversal(self):
        node_stack = [self.root]
        # for debugging, to remove
        popped_nids = set()
        while len(node_stack):
            popped_id = node_stack.pop()
            children_ids = self.get_children_ids(popped_id)
            if children_ids:
                assert popped_id not in popped_nids, self.nodes[popped_id].tag
                node_stack.append(popped_id)
                for child in children_ids:
                    assert child not in popped_nids, self.nodes[child].tag
                node_stack.extend(reversed(children_ids))
            else:
                yield popped_id
                popped_nids.add(popped_id)
                if len(node_stack) == 0:
                    break
                curr_children = self.get_children_ids(node_stack[-1])
                if len(curr_children) == 0:
                    break
                right_most_child = curr_children[-1]
                while right_most_child == popped_id:
                    popped_id = node_stack.pop()
                    yield popped_id
                    popped_nids.add(popped_id)
                    if len(node_stack) == 0:
                        break
                    curr_children = self.get_children_ids(node_stack[-1])
                    if len(curr_children) == 0:
                        break
                    right_most_child = curr_children[-1]

    # For heapq
    def __lt__(self, other):
        if self.score < other.score:
            return True
        return False
