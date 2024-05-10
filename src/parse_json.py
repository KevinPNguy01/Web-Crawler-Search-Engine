import json
with open('crawled.txt', 'r') as f:
     pages = len(f.readlines())

# sort via lenght of Posting obj 
# grab the lenght of the list 

with open('index.json', 'r') as f: 
     
     data = json.load(f)

     # returns a list of tuples 
     # within the tupels first element is token
     # second is the list 

     # items is a tuple 
     common_words = sorted(data.items(), key = lambda x:len(x[1]), reverse= True )[:50]
     length = len(data.keys())


print(f"number of pages {pages}")
print(f"number of tokens {length}")

for eachWord in common_words:
     print(f"{eachWord}")






     