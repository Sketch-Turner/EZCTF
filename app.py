from flask import Flask, render_template, request, jsonify
from target import Target
from workflow import Workflow
from module import Module
from filter import Filter
from node import TargetNode
import os

def load_module_configs() -> list[Module]:
    """
    Load all module configurations from YAML files.

    Inputs:
        None.

    Outputs:
        list[Module]: List of initialized modules loaded from configuration files.
    """
    modules: list[Module] = []

    for filename in os.listdir("modules/config"):
        if filename.endswith(".yaml"):
            path = os.path.join("modules/config", filename)
            modules.append(Module(path))

    return modules

def get_src_by_id(id: str, type: str) -> object:
    """
    Retrieve an object from a source collection by ID.

    Inputs:
        id (str): Unique identifier of the object to retrieve.
        type (str): Source collection type. Supported values are TARGET, FILTER, and MODULE.

    Outputs:
        object: Object matching the provided ID.

    Raises:
        ValueError: If no object with the given ID exists or the source type is invalid.
    """
    source = None

    match type:
        case "TARGET":
            source = targets
            if id == "ALL":
                return Target(list(target_pool))
        case "FILTER":
            source = filters
        case "MODULE":
            source = modules

    if source:
        for obj in source:
            if obj.id == id:
                return obj

    raise ValueError(f"No {type} object was found with id {id}")

targets = [] # target objects
target_pool = set() # list of all target ips
filters = [Filter(expression="")] # filter templates
modules = load_module_configs() # module templates
workflow = Workflow()

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html", targets=targets, modules=modules, filters=filters)


@app.route("/targets", methods=["POST"])
def add_target():
    data = request.get_json()

    print(data)
    ip = data.get("tgt_ip")

    if not ip:
        return jsonify({"error": "Missing IP"}), 400

    target = Target(ip)
    target_pool.add(ip)
    targets.append(target)

    workflow.update_targets(list(target_pool))

    return jsonify(target.to_dict())

@app.route("/targets/<target_id>", methods=["DELETE"])
def remove_target(target_id):
    global targets, target_pool

    targets = [t for t in targets if t.id != target_id]
    target_pool = set([t.tgt_ip for t in targets])

    return jsonify({"success": True})

@app.route("/workflow/nodes", methods=["POST"])
def add_workflow_node():
    data = request.json

    node_type = data["type"]
    node_source = get_src_by_id(id=data["source_id"], type=node_type)
    node_x = data.get("x", 0)
    node_y = data.get("y", 0)

    node = workflow.add_node(
        type=node_type,
        source=node_source,
        x=node_x,
        y=node_y
    )

    return jsonify(node.to_dict())

@app.route("/workflow/nodes/<node_id>", methods=["PUT"])
def update_workflow_node(node_id):
    data = request.json

    for node in workflow.nodes:
        if node.id == node_id:
            node.x = data["x"]
            node.y = data["y"]
            break

    return jsonify({"success": True})

@app.route("/workflow/nodes/<node_id>", methods=["DELETE"])
def delete_workflow_node(node_id):
    workflow.remove_node(node_id)

    return jsonify({
        "success": True
    })

@app.route("/workflow/nodes")
def get_workflow_nodes():
    return jsonify(workflow.get_nodes())

@app.route("/workflow/edges", methods=["POST"])
def add_workflow_edge():
    data = request.json

    edge = workflow.add_edge(
        source_id=data["source"],
        destination_id=data["destination"]
    )

    return jsonify(edge.to_dict())


@app.route("/workflow/edges/<edge_id>", methods=["DELETE"])
def remove_workflow_edge(edge_id):
    workflow.remove_edge(edge_id)

    return jsonify({
        "success": True
    })

@app.route("/workflow", methods=["GET"])
def get_workflow():
    return jsonify(workflow.to_dict())

@app.route("/workflow/nodes/<node_id>/config")
def get_node_config(node_id):
    return workflow.get_node(node_id).render_config()

@app.route("/workflow/nodes/<node_id>/config", methods=["PUT"])
def update_node_config(node_id):
    node = workflow.get_node(node_id)

    if not isinstance(node, TargetNode):
        node.update_config(request.json)

    return jsonify({
        **node.to_dict(),
        "html": node.render()
    })

@app.route("/workflow/run")
def run_workflow():
    return workflow.run()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)