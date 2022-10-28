import redis
import json


def getConfig():
    with open("config.json", encoding="utf-8") as rf:
        r = rf.read()
        rf.close()
    return json.loads(r)


config = getConfig()

db = redis.client.Redis(
    host=config["redis_host"],
    port=config["redis_port"],
    db=config["redis_db"],
    password=config["redis_password"]
)

print(db.flushall())
