import re
from simhash import Simhash, SimhashIndex
from urllib.robotparser import RobotFileParser
def get_features(s):
    width = 1
    s = s.lower()
    s = re.sub(r'[^\w]+', '', s)
    return [s[i:i + width] for i in range(max(len(s) - width + 1, 1))]

data = {
    1: u'How are you? I Am fine. blar blar blar blar blar Thanks.',
    2: u'How are you i am fine. blar blar blar blar blar than',
    3: u'This is simhash test.',
}
objs = [(str(k), Simhash(get_features(v))) for k, v in data.items()]
index = SimhashIndex(objs, k=3)

print(index.bucket_size())

s1 = Simhash(get_features(u'How are you i am fine. blar blar blar blar blar thank'))
print(index.get_near_dups(s1))

index.add('4', s1)
print(index.get_near_dups(s1))



print(index.get_near_dups(Simhash(get_features(u'How are you i  . blar blar blar blar blar thank'))))

robot = RobotFileParser()
robot.modified()
print(robot.can_fetch("*", "test"))
print(robot.crawl_delay("*"))