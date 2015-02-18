# I wrote this file to convert json savefiles for corbit-2
# to a format better suited to corbit-3.
# usage: python (this file)
# yeah, that means OCESS.json is the hardcoded read file
# deal with it (shades drop down)
# I didn't code this for reusability.

import json
import webcolors

json_root = []
with open("OCESS.json", "r") as loadfile:
    json_root = json.load(loadfile)

new_json_root = {}
new_json_root["entities"] = []
new_json_root["habitats"] = []
line = 0

for entity in json_root["entities"]:
    line += 1
    print(line*21+2)
    new_entity = {}
    new_entity["name"] = entity["name"]
    new_entity["velocity"] = [entity["v"]["x"],
                              entity["v"]["y"]]
    new_entity["displacement"] = [entity["pos"]["x"],
                                  entity["pos"]["y"]]
    new_entity["acceleration"] = [entity["acc"]["x"],
                                  entity["acc"]["y"]]
    new_entity["color"] = webcolors.name_to_rgb(entity["color"])
    new_entity["radius"] = entity["radius"]
    new_entity["mass"] = entity["mass"]
    try:
        new_entity["angular position"] = entity["ang_pos"]
        new_entity["angular speed"] = entity["ang_v"]
        new_entity["angular acceleration"] = entity["ang_acc"]
    except KeyError:
        new_entity["angular position"] = 0
        new_entity["angular speed"] = 0
        new_entity["angular acceleration"] = 0
    new_json_root["entities"].append(new_entity)

for habitat in json_root["habs"]:
    line += 1
    print(line*21+4)
    new_habitat = {}
    new_habitat["name"] = habitat["name"]
    new_habitat["velocity"] = [habitat["v"]["x"],
                              habitat["v"]["y"]]
    new_habitat["displacement"] = [habitat["pos"]["x"],
                                  habitat["pos"]["y"]]
    new_habitat["acceleration"] = [habitat["acc"]["x"],
                                  habitat["acc"]["y"]]
    new_habitat["color"] = webcolors.name_to_rgb(habitat["color"])
    new_habitat["radius"] = habitat["radius"]
    new_habitat["mass"] = habitat["mass"]
    try:
        new_habitat["angular position"] = habitat["ang_pos"]
        new_habitat["angular speed"] = habitat["ang_v"]
        new_habitat["angular acceleration"] = habitat["ang_acc"]
    except KeyError:
        new_habitat["angular position"] = 0
        new_habitat["angular speed"] = 0
        new_habitat["angular acceleration"] = 0
    new_habitat["engine systems"] = [
        {"class": "rcs",
         "fuel": 100,
         "rated fuel flow": 5,
         "specific impulse": 3000,
         "placements": [[0.00, [-1, 0]],
                        [1.57, [0, -1]],
                        [3.14, [1, 0]],
                        [4.71, [0, 1]]]},
        { "class": "main engines",
         "fuel": 1000,
         "rated fuel flow": 100,
         "specific impulse": 100,
         "placements": [[3.28, [1, 0]],
                        [3.00, [1,0]]]} ]
    new_json_root["habitats"].append(new_habitat)

json.dump(new_json_root, open("OCESS-converted.json", "w"),
          indent=4, separators=(',', ': '))
