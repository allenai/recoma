import json
from sre_parse import State
import re
from recoma.search.state import SearchNode, SearchState
from recoma.utils.class_utils import RegistrableFromDict


class StateRenderer(RegistrableFromDict):

    def __init__(self, output_format="html", special_suffix="") -> None:
        self.output_format = output_format
        self.special_suffix = special_suffix

    def output(self, search_state: SearchState):
        if self.output_format == "html":
            return self.to_html(search_state=search_state)
        elif self.output_format == "json":
            return self.to_json(search_state=search_state)
        else:
            raise ValueError("Output format: {} not supported".format(self.output_format))

    def to_json(self, search_state: SearchState):
        raise NotImplementedError

    def to_html(self, search_state: SearchState, relative_node = None):
        raise NotImplementedError

    def to_html_node(self, node: SearchNode):
        raise NotImplementedError

@StateRenderer.register("block")
class BlockRenderer(StateRenderer):

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.style_header = """<style type="text/css">
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

*, *:after, *:before {
	box-sizing: border-box;
}

:root {
	font-size: 16px;
}

body {
	font-family: "Inter", sans-serif;
	line-height: 1;
	min-height: 100vh;
	font-size: 1.25rem;
}

*:focus {
	outline: none;
}

body > div {
	width: 90%;
	max-width: 600px;
	margin-left: auto;
	margin-right: auto;
	margin-top: 5rem;
	margin-bottom: 5rem;
}

details div {
	border-left: 2px solid #000;
	border-right: 2px solid #000;
	border-bottom: 2px solid #000;
	padding: .5em;
}

details div > * + * {
  margin-top: .5em;
  margin-bottom: .5em;
}

details + details {
  margin-top: .5rem;
  margin-bottom: .5rem;
}

summary::-webkit-details-marker {
	display: none;
}

summary {
	border: 2px solid #000;
    list-style: none;
    margin-top: .5rem;
	padding: 0em 0em;
	cursor: pointer;
	position: relative;
	padding-left: calc(.75rem + .75rem);
}
details.small summary {
	border: 0px;
	padding: 0em 0em;
	cursor: pointer;
	position: relative;
  padding-left: calc(.75rem);
  text-decoration: underline;
}
details.small {
  font-size: 50%;
  width: 50%;
  padding: 0em 0em;
}

p.entry {
 font-size: 75%
}

summary:hover {
  background-color: #8b8680;
}

a {
	color: inherit;
	font-weight: 600;
	text-decoration: none;
	box-shadow: 0 1px 0 0;
}

a:hover {
	box-shadow: 0 3px 0 0;
}

code {
	font-family: monospace;
	font-weight: 600;
}
details > *:not(summary){
    margin-left: 2em;
}
details.small > *:not(summary){
    margin-left: 5em;
}
.model_name {
    font-weight: bold;
    padding-right: 5px;
}
.model_name:before {
  content: "<<";
}
.model_name:after {
  content: ">>";
}
details.small summary:before {
  content: ">"
}
</style>"""


    def to_html(self, search_state: SearchState, relative_node = None):
        parent = search_state.get_node(search_state.root) if relative_node is None else relative_node
        parent_repr = "    " + self.to_html_node(parent)
        children_repr = ""
        for child in search_state.get_children(parent):
            children_repr += "    " + self.to_html(search_state=search_state, relative_node=child) + "\n"
        if children_repr:
            tree_repr = """<details>\n  <summary>\n{}\n</summary>\n  {}\n</details>\n""".format(parent_repr, children_repr)
        else:
            tree_repr = """<details>\n  <summary>\n{}\n</summary>\n</details>\n""".format(parent_repr)
            #"\n{}\n".format(parent_repr)
        if relative_node is None:
            return """{}\n  {}\n""".format(self.style_header, tree_repr)
        else:
            return tree_repr

    def clean_text(self, text):
        text = text.replace("\n", "<br>")
        text = re.sub(r'```(.*?)```', r'<pre><code>\1</code></pre>', text, flags=re.DOTALL)
        return text

    def to_html_node(self, node: SearchNode):
        summary = ""
        if node._tag:
            summary = node._tag
        else:
            if node.is_open():
                summary += "<u>&lt;" + node.target + "&gt;</u> "
            else:
                summary += "<span class=\"model_name\">" + node.target + "</span>"
            if node.input_str_for_display:
                summary += node.input_str_for_display + " => "
            if node.output is not None:
                summary += self.clean_text(node.output)
            else:
                summary += " ... "
        summary = "<p class=\"entry\">" + summary + "</p>"

        summary += """\n<details class="small">\n  <summary>\nInput\n</summary>\n{}</details>\n""".format(self.clean_text(node.input_str))
        if node.output is not None:
            summary += """\n<details class="small">\n  <summary>\nOutput\n</summary>\n{}</details>\n""".format(self.clean_text(node.output))
        if "prompts" in node.data:
            details = ""
            for input_str, output_strs in node.data["prompts"]:
                details += "<b>Input:</b>\n<br>\n" + input_str.replace("\n", "<br>") + "\n<br>\n"
                for output_str in output_strs:
                    details += "&nbsp;<b>Output:</b>\n<br>\n" + output_str.replace("\n",
                                                                                   "<br>") + "\n<br>\n"
                details += "\n<hr>\n"
            summary += """\n<details class="small">\n  <summary>Prompts\n</summary>\n{}</details>\n""".format(details)

        return summary

@StateRenderer.register("tree")
class TreeRenderer(StateRenderer):

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.style_header = """<style type="text/css">
.tree{
  --spacing : 1rem;
  --radius  : 5px;
}

.tree li{
  display      : block;
  position     : relative;
  padding-left : calc(2 * var(--spacing) - var(--radius) - 2px);
}

.tree ul{
  margin-left  : calc(var(--radius) - var(--spacing));
  padding-left : 0;
}

.tree ul li{
  border-left : 2px solid #ddd;
  margin-bottom: calc(var(--radius));
}

.tree ul li:last-child{
  border-color : transparent;
  margin-bottom: 0px;
}

.tree ul li::before{
  content      : '';
  display      : block;
  position     : absolute;
  top          : calc(var(--spacing) / -2);
  left         : -2px;
  width        : calc(var(--spacing) + 2px);
  height       : calc(var(--spacing) + 1px);
  border       : solid #ddd;
  border-width : 0 0 2px 2px;
}


.model_name {
    font-weight: bold;
    padding-right: 5px;
}

.model_name:hover {
    background-color: #cccccc;
}
</style>"""


    def to_html(self, search_state: SearchState, relative_node = None):
        parent = search_state.get_node(search_state.root) if relative_node is None else relative_node
        parent_repr = "    " + self.to_html_node(parent)
        children_repr = ""
        for child in search_state.get_children(parent):
            children_repr += "    " + self.to_html(search_state=search_state, relative_node=child) + "\n"
        if children_repr:
            tree_repr = """<li><details>\n  <summary>\n{}\n</summary>\n  <ul>\n{}</ul>\n</details></li>""".format(parent_repr, children_repr)
        else:
            tree_repr = "<li>\n{}\n</li>".format(parent_repr)
        if relative_node is None:
            return """{}<ul class="tree">\n  {}\n</ul>""".format(self.style_header, tree_repr)
        else:
            return tree_repr

    def to_html_node(self, node: SearchNode):
        summary = ""
        if node._tag:
            summary = node._tag
        else:
            if node.is_open():
                summary += "<u>&lt;" + node.target + "&gt;</u> "
            else:
                summary += "<span class=\"model_name\">" + node.target + "</span>"
            if node.input_str_for_display:
                summary += node.input_str_for_display + " => "
            if node.output is not None:
                summary += node.output.replace("\n", "\n<br>")
            else:
                summary += " ... "
        if "prompts" in node.data:
            details = ""
            for input_str, output_strs in node.data["prompts"]:
                details += "<b>Input:</b>\n<br>\n" + input_str.replace("\n", "<br>") + "\n<br>\n"
                for output_str in output_strs:
                    details += "&nbsp;<b>Output:</b>\n<br>\n" + output_str.replace("\n",
                                                                                   "<br>") + "\n<br>\n"
                details += "\n<hr>\n"
            return '{}\n<details style="margin-left: 5em;font-size: 75%;">\n  <summary>\nPrompts\n</summary>\n  <ul>\n{}</ul>\n</details>'.format(summary, details)
        else:
            return summary

@StateRenderer.register("old")
class OldStateRenderer(StateRenderer):

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.style_header = """<style type="text/css">
                          details > *:not(summary){
                          margin-left: 2em;
                         }
                        .model_name {
                          display: inline-block;
                          padding: 1px 2px;
                          margin-right: 3px;
                          border-radius: 2px;
                          background-color: #85C1E9;
                          color: #000000;
                          border-color: #000000;
                          border: solid;
                          border-radius: 3px;
                          border-width: 1px;
                          text-decoration: none;
                          font-weight: bold;
                          text-align: center;
                          cursor: pointer;
                        }

                        .model_name:hover {
                          background-color: #cccccc;
                        }
                        </style>
            """

    def to_html(self, search_state: SearchState, relative_node = None):
        parent = search_state.get_node(search_state.root) if relative_node is None else relative_node
        parent_repr = self.to_html_node(parent)
        children_repr = ""
        for child in search_state.get_children(parent):
            children_repr += self.to_html(search_state=search_state, relative_node=child) + "\n"
        if children_repr:
            tree_repr = """<p style=\"margin:1px;\"><details>
                        <summary>{}</summary>
                        {}
                    </details></p>
                """.format(parent_repr, children_repr)
        else:
            tree_repr = "<p style=\"margin:1px; margin-left: 3em;\">{}</p>".format(parent_repr)
        return self.style_header + tree_repr

    def to_html_node(self, node: SearchNode):
        summary = ""
        if node._tag:
            summary = node._tag
        else:
            if node.is_open():
                summary += "<u>&lt;" + node.target + "&gt;</u> "
            else:
                summary += "<span class=\"model_name\">" + node.target + "</span>"
            if node.input_str_for_display:
                summary += node.input_str_for_display + " => "
            if node.output is not None:
                summary += node.output.replace("\n", "\n<br>")
            else:
                summary += " ... "
        details = ""
        if "prompts" in node.data:
            for input_str, output_strs in node.data["prompts"]:
                details += "<b>Input:</b>\n<br>\n" + input_str.replace("\n", "<br>") + "\n<br>\n"
                for output_str in output_strs:
                    details += "&nbsp;<b>Output:</b>\n<br>\n" + output_str.replace("\n",
                                                                                   "<br>") + "\n<br>\n"
                details += "\n<hr>\n"
        if details == "":
            return summary + "<br/>"
        else:
            return """{}
                      <details style="margin-left: 5em;font-size: 75%;">
                         <summary>Prompts</summary>
                         {}
                      </details>
            """.format(summary, details)


@StateRenderer.register("full_json")
class FullJsonRenderer(StateRenderer):

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.output_format = "json"
        self.special_suffix = "_full"

    def to_json(self, search_state: SearchState):
        return search_state.to_json()


@StateRenderer.register("simple_json")
class SimpleJsonRenderer(StateRenderer):

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.output_format = "json"

    def to_json(self, search_state: SearchState):
        output_json = []
        for node_id in search_state.postorder_traversal():
            if node_id is not None and not search_state.children(node_id):
                node = search_state.get_node(node_id)
                if node is not None:
                    output_json.append({
                        "input": node.input_str,
                        "output": node.output,
                        "model": node.target
                        })
        return json.dumps(output_json, indent=4)