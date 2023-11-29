import flask
from flask.json import jsonify
import uuid

from model import Warehouse

robotsSimulations = {}
model = None

app = flask.Flask(__name__)


@app.route("/warehouseSimulations", methods=["POST"])
def create():
    global robotsSimulations

    warehouse_id = str(uuid.uuid4())
    robotsSimulations[warehouse_id] = Warehouse(box_percentage=0.37, num_robots=5)

    return {"warehouseId": warehouse_id}, 200, {'Location': f"/warehouseSimulations/{warehouse_id}"}


@app.route("/warehouseSimulations/<warehouse_id>", methods=["GET"])
def query_state(warehouse_id):
    steps = flask.request.args.get('steps', default=1, type=int)

    warehouse = robotsSimulations.get(warehouse_id)
    if not warehouse:
        return jsonify({"error": "Warehouse simulation not found"}), 404

    detailed_data = []
    for _ in range(steps):
        warehouse.step()
        detailed_data.append(warehouse.collect_detailed_data())

    return jsonify(detailed_data), 200


app.run(port=5024)
