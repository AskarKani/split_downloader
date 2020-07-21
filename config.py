
import json
from collections import OrderedDict

# Data to be written
dictionary = OrderedDict()

dictionary ={
    "file_name": "sathiyajith",
    "parts": 56,
    "2": "file_size",
    "1": [("1",15),(2,16)],

}


dictionary2={
    "askar":56
}
# Serializing json
json_object = json.dumps(dictionary, indent=4)
# my_object_2 = json.dumps(dictionary2, indent=4)
# Writing to sample.json
with open("sample.config", "w") as outfile:
    outfile.write(json_object)
    # outfile.write(my_object_2)

# Opening JSON file
with open('sample.config', 'r') as openfile:
    # Reading from json file
    json_object = json.load(openfile)

print(json_object)
print(type(json_object))
if None:
    print("None")
else:
    print("not none")