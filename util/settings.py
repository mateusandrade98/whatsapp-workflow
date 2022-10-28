from ujson import loads
from util import databases


class externalData:
    def __init__(self, Env: dict = None):
        self.mongodb = databases.MongoDB(Env=Env)

    def get(self, session: str = '') -> dict:
        return self.mongodb.findOne(
            filter={
                "session": session
            },
            collection="Contexts"
        )

    def set(self, session: str, context: dict) -> bool:
        context["session"] = session
        try:
            self.mongodb.set(
                data=context,
                collection="Contexts"
            )
            return True
        except Exception:
            return False


class Settings:
    def __init__(self):
        pass

    def getConfig(self) -> dict:
        with open("config.json", encoding="utf-8") as rf:
            r = rf.read()
            rf.close()
        return loads(r)

    def getPosts(self, session: str = '') -> dict:
        config = self.getConfig()
        external = externalData(Env=config)
        ext_context = external.get(session=session)
        if not ext_context:
            with open("contexts.json", encoding="utf-8") as rf:
                r = rf.read()
                rf.close()
            result = loads(r)
            external.set(
                session=session,
                context=result
            )
            return result
        return ext_context

    def getApi(self, session: str = '') -> dict:
        with open("api.json", encoding="utf-8") as rf:
            r = rf.read()
            rf.close()
        data = loads(r)
        if session != "":
            posts = self.getPosts(session=session)
            if "api" in posts and type(posts["api"]) == dict:
                data["public"].update(posts["api"])
        return data
