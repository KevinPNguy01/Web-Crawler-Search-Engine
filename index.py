import json

index_dictionary = {}

with open("indices/index_of_index.txt", "r") as f:
    for line in f:
        token, index = line.strip().split(',')

        if token[0] in index_dictionary:
            index_dictionary[token[0]].append(token)
        else:
            index_dictionary[token[0]] = [token]

with open("indices/index_dictionary.json", "w") as json_file:
    json.dump(index_dictionary, json_file, indent=4)

print("Dictionary has been saved to index_dictionary.json")
