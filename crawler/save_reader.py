import shelve

with shelve.open("frontier.shelve") as save, open("links.txt", "w") as file:
    links = sorted([item[0] for item in save.values()])
    for link in links:
        file.write(f"{link}\n")

with shelve.open("frequencies.shelve") as save, open("frequencies.txt", "w") as file:
    links = sorted([(word, frequency) for word, frequency in save.items()], key = lambda x: x[1], reverse=True)
    count = 0
    for word, frequency in links:
        file.write(f"{word} => {frequency}\n")
        count += frequency
    print(count)