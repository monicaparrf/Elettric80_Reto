import mesa
from model import Warehouse, Robot, Charger, ConveyorBelt, Shelf, Box, Cell

MAX_NUMBER_ROBOTS = 20


def agent_portrayal(agent):
    if isinstance(agent, Robot):
        if agent.box is not None:
            color = "brown"

        else:
            color = "black"

        return {
            "Shape": "circle",
            "Filled": "false",
            "Color": color,
            "Layer": 1, "r": 0.9,
            "text": f"{agent.battery}",
            "text_color": "white"
        }
    elif isinstance(agent, ConveyorBelt):
        return {
            "Shape": "rect",
            "Filled": "true",
            "Color": "black",
            "Layer": 0,
            "w": 0.9,
            "h": 0.9
        }
    elif isinstance(agent, Box):
        return {
            "Shape": "rect",
            "Filled": "true",
            "Color": "brown",
            "Layer": 0,
            "w": 0.9,
            "h": 0.9,
            "text": ""
        }
    elif isinstance(agent, Shelf):
        if agent.stored_box is not None:
            color = "brown"
        else:
            color = "gray"

        return {
            "Shape": "rect",
            "Filled": "true",
            "Color": color,
            "Layer": 0,
            "w": 0.9,
            "h": 0.9,
            "text": ""
        }
    elif isinstance(agent, Charger):
        return {
            "Shape": "rect",
            "Filled": "true",
            "Color": "blue",
            "Layer": 0,
            "w": 0.9,
            "h": 0.9,
            "text": "🔋"
        }


grid = mesa.visualization.CanvasGrid(
    agent_portrayal, 14, 13, 400, 400)
    
model_params = {
    "num_robots": mesa.visualization.Slider(
        "Número de Robots",
        5,
        1,
        MAX_NUMBER_ROBOTS,
        1,
        description="Escoge cuántos robots deseas implementar en el modelo",
    ),
    "box_percentage": mesa.visualization.Slider(
        "Porcentaje de Aparicion de cajas",
        0.34,
        0.0,
        1,
        0.01,
        description="Selecciona el porcentaje de aparición de cajas",
    )
}

server = mesa.visualization.ModularServer(Warehouse, [grid], "Bot_Cleaners", model_params, 8521)



