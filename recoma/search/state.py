from typing import Optional, Any

from treelib import Tree, Node

from recoma.datasets.reader import Example
from recoma.models.generator import GenerationOutputs


class SearchNode(Node):
    def __init__(self, input_str: str, target_model: str, input_str_for_display=None,
                 is_open: bool = True, output: str = None, data={}):
        """
        Node in the SearchState tree
        :param input_str: Input string provided by the parent
        :param is_open: Is this node still to be resolved (i.e. execution not complete yet)?
        :param target_model: Which model should be assigned?
        :param output: Generated output using the target_model
        """
        super().__init__(data=data)
        self._is_open = is_open
        self.target = target_model
        self.output = output
        self.input_str = input_str
        self.input_str_for_display = input_str_for_display
        self._tag = None

    def is_open(self):
        return self._is_open

    def target_model(self):
        return self.target

    def close(self, output):
        # print("CLOSING!!" + str(self.tag) + "\n" + str(output))
        # input("Wait")
        self._is_open = False
        self.output = output

    def set_tag(self, tag):
        self._tag = tag

    @property
    def tag(self):
        if self._tag:
            return self._tag
        label = ""
        if self.is_open():
            label += "*"
        display_str = self.input_str_for_display or self.input_str
        if self.output:
            label += "[" + self.target + "] " + self.output
        else:
            label += "[" + self.target + "] " + display_str + " => ... "
        return label

    def to_html_node(self):
        summary = ""
        if self._tag:
            summary = self._tag
        else:
            if self.is_open():
                summary += "<u>[" + self.target + "]</u> "
            else:
                summary += "[" + self.target + "] "
            display_str = self.input_str_for_display or self.input_str
            if self.output:
                summary += display_str + " => " + self.output
            else:
                summary += display_str + " => ... "
        details = ""
        if "prompts" in self.data:
            for input_str, output_strs in self.data["prompts"]:
                details += "<b>Input:</b>\n<br>\n" + input_str.replace("\n", "<br>") + "\n<br>\n"
                for output_str in output_strs:
                    details += "&nbsp;<b>Output:</b>\n<br>\n" + output_str.replace("\n", "<br>") + "\n<br>\n"
                details += "\n<hr>\n"
        if details == "":
            return summary
        else:
            return """{}
                      <details style="margin-left: 5em;font-size: 75%;">
                         <summary>Prompts</summary>
                         {}
                      </details>
            """.format(summary, details)

    def add_input_output_prompt(self, input_str: str, output: GenerationOutputs):
        if "prompts" not in self.data:
            self.data["prompts"] = []
        # else:
        #     print("Current metadata: " + str(self.metadata["prompts"][0][1]))
        # print("Adding " + str([x for x in output.outputs]))
        self.data["prompts"].append((
            input_str,
            [x for x in output.outputs]
        ))

    def get_input_output_prompts(self):
        output = ""
        if "prompts" in self.data:
            for input_str, output_strs in self.data["prompts"]:
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
            # print(self[node_id].tag)
            if node_id is not None and self[node_id].is_open():
                # print("Found node_id: " + str(node_id))
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

    def to_html_tree(self, parent=None) -> str:
        header = ""
        footer = ""
        if parent is None:
            parent = self.get_node(self.root)
            header = """<style type="text/css">
                          details > *:not(summary){
                          margin-left: 2em;
                         }
                        </style>
                        <html>
            """
            footer = "</html>"
        children_repr = ""
        for child in self.get_children(parent):
            children_repr += self.to_html_tree(child) + "\n"

        tree_repr = """<details>
                      <summary>{}</summary>
                      {}
                   </details>
               """.format(parent.to_html_node(),
                          children_repr)
        return header + tree_repr + footer

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

    def get_children(self, parent_node: SearchNode):
        return [self.get_node(nid) for nid in self.get_children_ids(parent_node.identifier)]

    def add_next_step(self, next_step_input: str,
                      next_step_model: str,
                      current_step_node: SearchNode,
                      next_step_input_for_display: str = None,
                      metadata: dict[str, Any] = {}):
        new_node = SearchNode(input_str=next_step_input,
                              target_model=next_step_model,
                              input_str_for_display=next_step_input_for_display,
                              data=metadata)
        self.add_node(new_node, parent=current_step_node)
        return new_node

    def postorder_traversal(self):
        node_stack = [self.root]
        # for debugging, to remove
        popped_nids = set()
        while len(node_stack):
            popped_id = node_stack.pop()
            children_ids = self.get_children_ids(popped_id)
            # print(children_ids)
            if children_ids:
                assert popped_id not in popped_nids, self.nodes[popped_id].tag
                node_stack.append(popped_id)
                for child in children_ids:
                    assert child not in popped_nids, self.nodes[child].tag
                node_stack.extend(reversed(children_ids))
            else:
                # print("Popped! " + popped_id)
                yield popped_id
                popped_nids.add(popped_id)
                if len(node_stack) == 0:
                    break
                curr_children = self.get_children_ids(node_stack[-1])
                if len(curr_children) == 0:
                    continue
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
