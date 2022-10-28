from typing import Optional

import requests
from html import unescape
from ujson import loads, JSONDecodeError
from requests.exceptions import RequestException
from redis import Redis
from util import select
from util import settings
from util import request as util_request
from fastapi import FastAPI, Request
from pydantic import Field, BaseModel
from fastapi.responses import JSONResponse
from uvicorn import run
from WhatsAppApi import Wpp

i_settings = settings.Settings()
config = i_settings.getConfig()
api = i_settings.getApi()

app = FastAPI()
app.debug = True


class HookModel(BaseModel):
    session: str
    device: str
    pushName: str
    event: Optional[str] = 'on-message'
    type: Optional[str] = 'text'
    isMedia: Optional[bool] = False
    id: Optional[str] = ''
    from_: str = Field(default='', alias='from')
    content: Optional[str] = ''
    title: Optional[str] = ''
    isgroup: Optional[bool] = False
    participant: Optional[str] = ''
    timestamp: Optional[float] = 0.0
    selectedId: Optional[str] = '-1'


class Instance:
    def __init__(self, hook):
        self.config = i_settings.getConfig()
        self.db = None
        self.client = {}
        self.hook = hook
        self.wpp = None
        self.isAuth = 0
        self.i_c = 1
        self.flow = select.Flow(session=self.hook["session"])
        self.api = i_settings.getApi(session=self.hook["session"])
        self.debug = select.Debug

    def setParamsValues(self, data: dict = None, context: dict = None):
        if "params_values" in context:
            p_v = context["params_values"]
            for d in data:
                if not d in p_v or (d in p_v and p_v[d] is None):
                    p_v.update({d: data[d]})
            context["params_values"] = p_v
        return context

    def getWppInstance(self) -> Wpp:
        return Wpp(
            session=self.hook["session"]
        )

    def getRedisInstance(self) -> Redis:
        return Redis(
            host=self.config["redis_host"],
            port=self.config["redis_port"],
            db=self.config["redis_db"],
            password=self.config["redis_password"]
        )

    def profilepic(self, chatId: str = "", session: str = "") -> str:
        pic = Wpp(session=session)
        pic.set_chatid(chatId=chatId)

        try:
            response = pic.getProfilePic()
            if response["success"]:
                if not 'data' in response:
                    return ''
                data = response['data']
                if not 'picture' in data:
                    return ''
                picture = data["picture"]
                requests.post(
                    url=self.api["requests"]["api_post_image"],
                    headers=self.api["requests"]["headers"],
                    json={
                        "urlImage": picture,
                        "phone": chatId,
                        "session": session
                    }
                )
                return picture
        except Exception as e:
            return e
        return ''

    def countChats(self) -> int:
        if self.db is None:
            self.db = self.getRedisInstance()
        return self.db.dbsize()

    def getMemory(self, number: int) -> object:
        if number is None:
            return error("Number is not defined")
        if self.db is None:
            self.db = self.getRedisInstance()
        return self.db.get("bot:client_{number}".format(number=number))

    def setMemory(self, number: int = 0, index: int = 0, context: dict = None) -> object:
        if number is None:
            return error("Number is not defined")
        if self.db is None:
            self.db = self.getRedisInstance()
        n_context = select.Context()
        n_context.set_index(index=index)  # set index
        n_context.set(context=context)  # load configs
        n_context.set_args_values(context["args_values"])
        n_context.set_params_values(context["params_values"])
        n_context.set_first(first=0)
        self.debug("set_memory_n_context->", n_context.get())
        self.db.set(
            name="bot:client_{number}".format(number=number),
            value=n_context.json()
        )
        self.expireKey(key="bot:client_{number}".format(number=number))
        return n_context.get()

    def createContext(self, isAuth: int = 0) -> object:
        if not self.client.keys():
            return error("Client is invalid.")
        if self.db is None:
            self.db = self.getRedisInstance()
        n_context = select.Context()
        self.debug("n_context->", n_context.get())
        index = 1
        if isAuth:
            index = self.config["auth_context"]
        i_c, context = self.flow.getContext(index=index)
        self.debug("MemoryContext->", context)
        n_context.set_index(index=i_c)  # set index
        n_context.set(context=context)  # load configs
        # n_context.set_params_values(params_values={})
        n_context.set_first(first=1)
        self.debug("setMemory->", n_context.json())
        if self.db.set(
                name="bot:client_{number}".format(number=self.client['number']),
                value=n_context.json()
        ):
            self.expireKey(key="bot:client_{number}".format(number=self.client['number']))
            if isAuth:
                self.debug("isAuthMemory->", n_context.get())
                return n_context.get()
            return self.getContext()

    def sender(self, context: dict = None, index: int = 0, chatId: str = "") -> object:
        if "plugin" in context and context["plugin"] and "bp_token" in context:
            return self.setMemory(
                number=self.client["number"],
                index=index,
                context=context,
            )

        wpp = self.getWppInstance()
        wpp.set_chatid(chatId=chatId)

        # html parse
        context["text"] = unescape(context["text"])

        if not "inputs" in context:
            send = wpp.sendText(
                text=context["text"]
            )

            if "multi_messages" in context:
                bp = select.params.BuildParams(
                    params=context["params"],
                    values=context['params_values']
                )
                for message in context["multi_messages"]:
                    message = bp.setFormat(s=message)
                    wpp.sendText(
                        text=message
                    )

            self.debug("Sender->", send)
            if "success" in send:
                return self.setMemory(
                    number=self.client["number"],
                    index=index,
                    context=context,
                )
            else:
                return context
        else:
            inputs = context["inputs"]
            inputs["title"] = context["text"]
            if str(inputs["buttons"]).count(",") <= 3:
                #send buttons, limit 3
                send = wpp.sendButtons(
                    title=inputs["title"],
                    description=inputs["description"],
                    buttons=inputs["buttons"]
                )
            else:
                #send lists
                send = wpp.sendList(
                    title=inputs["title"],
                    description=inputs["description"],
                    buttons=inputs["buttons"]
                )
            self.debug("Sender->", send)
            if "success" in send:
                return self.setMemory(
                    number=self.client["number"],
                    index=index,
                    context=context
                )
            else:
                return context

    def expireKey(self, key: str = "") -> bool:
        return self.db.expire(name=key, time=self.config["timeExpire"] * 60)

    def getContext(self, auth: dict = None):
        if not auth is None:
            self.isAuth = auth["is"]

        auth = {} if auth is None else auth

        memory = self.getMemory(number=self.client["number"])

        if not memory is None:
            try:
                memory = loads(memory)
            except JSONDecodeError:
                return {}
        else:
            memory = self.createContext(isAuth=self.isAuth)
            self.debug("0-Memory->", memory)

        self.debug("Flow->", self.flow)

        try:
            # public api values
            if not "public" in memory:
                memory["params_values"].update(self.api["public"])
                memory.update({"public": "ok"})

            # set client params
            memory["params_values"].update(self.client)

            self.debug("1-Memory->", memory)

            n_context = self.flow.getNewContext(
                indexContext=memory["context"],
                context=memory,
                content=self.client["content"]
            )

            self.debug("NContext->", n_context)

            isFirst = ("first" in memory) and (memory["first"] == 1)

            if not auth is None:
                if "is" in auth and auth["is"]:
                    self.debug("isAuth")

                    if isFirst:
                        self.i_c = self.config["auth_context"]
                        self.i_c, memory = self.flow.getContext(
                            index=self.i_c
                        )

                    memory = self.setParamsValues(
                        data=auth["data"],
                        context=memory
                    )

                    self.debug("2-Memory", memory)

                    if "params" in memory:
                        memory = select.params.setParamsContext(
                            context=memory
                        )

                    if not 'image' in auth["data"] and not 'pic' in memory["params_values"]:
                        pic = self.profilepic(
                            chatId=self.client["number"],
                            session=self.hook["session"]
                        )

                        memory["params_values"].update({
                            "pic": pic
                        })

            # load api requests
            if not "requests_api_modBetaOK" in memory:
                rq_api = api["requests"]
                n_values = {}
                n_values.update(rq_api)
                n_values.update({"requests_api_modBetaOK": 1})
                if not "params_values" in memory:
                    memory["params_values"] = {}
                memory["params_values"].update(n_values)

            if isFirst:
                self.i_c, memory = self.flow.getContext(
                    index=self.i_c
                )

                return self.sender(
                    context=self.client["context"],
                    index=self.i_c,
                    chatId=self.client["number"]
                )

            if self.config["debug"] and self.config["debug_context"] != 0:
                n_context = self.flow.getNewContext(
                    indexContext=self.config["debug_context"],
                    context=memory,
                    content=self.client["content"]
                )

            newContext = None
            if type(n_context) == tuple:
                self.i_c, newContext = n_context

            # modBeta
            modBeta = ("modBeta" in newContext and newContext["modBeta"])

            if not "args_values" in newContext:
                newContext["args_values"] = memory["args_values"]

            if not "params_values" in newContext:
                newContext["params_values"] = memory["params_values"]

            self.debug("{start}ModBeta", modBeta)
            if modBeta:
                self.debug("{start} ContextModBeta", newContext)
                if "modBeta" in newContext:
                    if "list" in newContext:
                        self.debug("{start} modBeta")
                        newContext["context"]["args_values"]["itemSelected"] = str(newContext["index"])
                        newContext["context"]["args_values"]["itemChanged"] = 1

                        normalContent = ""
                        if newContext["arg"]["type"] == "number":
                            normalContent = self.flow.getNumber(i=self.client["content"])
                        elif newContext["arg"]["type"] == "text":
                            normalContent = self.flow.getText(i=self.client["content"]).upper()

                        arg_hash = self.flow.getHashArg(
                            arg=newContext["context"]["args_values"]["itemSelected"],
                            indexContext=newContext["index"]
                        )

                        act_navs = self.flow.makeButtons(
                            TypeInteraction="navs",
                            qntElements=len(newContext["arg"]["navs"]),
                            data={
                                "navs": newContext["arg"]["navs"]
                            }
                        )

                        #  Req List
                        newContext["context"] = self.flow.reqList(
                            context=newContext["context"],
                            arg=newContext["index"],
                            content=self.client["content"],
                            indexContext=self.i_c,
                            normalContent=normalContent,
                            arg_hash=arg_hash,
                            act_navs=act_navs
                        )
                        ###

                        self.debug("modBeta->", modBeta)

                        return self.sender(
                            context=newContext["context"],
                            index=self.i_c,
                            chatId=self.client["number"]
                        )

            if not newContext is None:
                if newContext["text"] is None and "args" in newContext:
                    if len(newContext["args"]) > 0:
                        newContext["text"] = newContext["args"]["1"]["empty"]
                        if "lists" in newContext:
                            newContext = self.flow.getBackMenu(
                                context=newContext,
                                lists=newContext["lists"],
                                values=newContext["params_values"],
                                key="",
                                showEnd=0
                            )

                            if modBeta:
                                context = newContext["context"]

                                if config["debug_args"] != 0:
                                    newContext["index"] = config["debug_args"]

                                try:

                                    arg_hash = self.flow.getHashArg(
                                        arg=newContext["index"],
                                        indexContext=self.i_c
                                    )

                                    act_navs = self.flow.makeButtons(
                                        TypeInteraction="navs",
                                        qntElements=len(context["args"][newContext["index"]]["navs"]),
                                        data={
                                            "navs": context["args"][newContext["index"]]["navs"]
                                        }
                                    )

                                    i_c = newContext["index"]

                                    newContext = self.flow.reqList(
                                        context=context,
                                        arg=newContext["index"],
                                        content=self.client["content"],
                                        indexContext=self.i_c,
                                        normalContent="",
                                        arg_hash=arg_hash,
                                        act_navs=act_navs
                                    )

                                    newContext["args_values"]["itemSelected"] = i_c
                                    newContext["args_values"]["itemInConfirmation"] = "0"

                                    return self.sender(
                                        context=newContext,
                                        index=self.i_c,
                                        chatId=self.client["number"]
                                    )

                                except Exception as e:
                                    print(e)
                                    exit()

                            newContext["text"] += "\nEscolha um número da lista para ser preenchido"

                if "params" in newContext:
                    newContext = select.params.setParamsContext(context=newContext)

                self.debug("exit->", newContext)

                return self.sender(
                    context=newContext,
                    index=self.i_c,
                    chatId=self.client["number"]
                )

        except KeyError:
            error("Context not found.")

    def run(self):
        if self.hook is None:
            return error("Data hook not defined.")

        self.debug('hook->', self.hook)

        try:
            isValidUser = (
                    (
                            self.hook["type"] == "text" or
                            self.hook["type"] == "buttons-response" or
                            self.hook["type"] == "forwarding" or
                            self.hook["type"] == "list-response" or
                            self.hook["type"] == "link-preview"
                    ) and
                    self.hook["isgroup"] == False)
            if not isValidUser:
                return error("Invalid request type.")
        except KeyError as e:
            return error("Invalid request: KeyError {e}".format(e=e))

        try:
            number = self.hook["from"]
            content = ""
            pushName = ""

            if "title" in self.hook:
                content = self.hook["title"]

            if "content" in self.hook and not self.hook["content"] == "":
                content = self.hook["content"]

            if "body" in self.hook:
                content = self.hook["body"]["link"]

            if "pushName" in self.hook and not self.hook["pushName"] == "":
                pushName = str(self.hook["pushName"]).title()

            self.client.update({
                "number": number,
                "content": content,
                "pushName": pushName,
                "session": self.hook.get("session")
            })
        except KeyError as e:
            return error("Invalid request: KeyError {e}.".format(e=e))

        if content == "":
            return error("content empty")

        url_api_get_user = str(self.api["requests"]["api_get_user"]).format(
            number=number,
            session=self.hook.get("session")
        )

        try:
            request_call = util_request.Request(
                body_request={
                    "url": url_api_get_user,
                    "method": "GET",
                    "headers": self.api["requests"]["headers"],
                    "data": {}
                }
            ).execute()
            self.debug("1request_call->", request_call)

            if "status" in request_call and not request_call["status"]:
                # get image
                image = self.profilepic(
                    chatId=number,
                    session=self.hook.get("session")
                )
                #

                # create user
                util_request.Request(
                    body_request={
                        "url": api["requests"]["api_create_user"],
                        "method": "POST",
                        "headers": self.api["requests"]["headers"],
                        "data": {
                            "name": pushName,
                            "phone": number,
                            "session": self.hook.get("session"),
                            "image": image
                        }
                    }
                ).execute()
                #

                #get user
                request_call = util_request.Request(
                    body_request={
                        "url": url_api_get_user,
                        "method": "GET",
                        "headers": self.api["requests"]["headers"],
                        "data": {}
                    }
                ).execute()
                #

                # conversations
                util_request.Request(
                    body_request={
                        "url": self.api["requests"]["api_conversations"],
                        "method": "POST",
                        "headers": self.api["requests"]["headers"],
                        "data": {
                            "phone": number,
                            "session": self.hook.get("session")
                        }
                    }
                ).execute()
                #

            n_data = {}

            if not "data" in request_call:
                return error("Data not defined.")

            n_data.update(request_call["data"])
            n_data.update(self.client)
            self.debug("n_data->", n_data)
            self.debug("2request_call->", request_call["data"])

            if "office" in n_data and str(n_data["office"]).lower() == "blocked":
                return error("User blocked.")

            if "conversation_id" in n_data:
                # forward message to support
                util_request.Request(
                    body_request={
                        "url": self.api["requests"]["api_user_response"],
                        "method": "POST",
                        "headers": self.api["requests"]["headers"],
                        "data": {
                            "session": self.hook.get("session"),
                            "phone": number,
                            "content": content
                        }
                    }
                ).execute()
                #

            if "office" in n_data and str(n_data["office"]).lower() == "in_support":
                return error("User in_support.")

            return self.getContext(auth={"is": 1, "data": n_data})

        except RequestException as e:
            return error("Query API problem: {e}".format(e=e))


def error(msg: str = '', code: int = 404) -> JSONResponse:
    return JSONResponse(content={"status": False, "data": {"error": msg, "version": config["version"]}},
                        status_code=code)


def chkAccessDenied(rules=None, level: str = "token") -> dict:
    if level == "token":
        if not "token" in rules:
            return dict(success=False, msg="token not defined.")
        if rules["token"] != api.get("token"):
            return dict(success=False, msg="token is invalid.")
    return {}


@app.post("/hook")
async def hook(request: Request, data: HookModel):
    accessDenied = chkAccessDenied(rules=request.query_params, level="token")
    if accessDenied:
        return error(msg=accessDenied.get("msg"), code=403)

    try:
        if request.query_params["token"] != api["token"]:
            return error("Token is invalid.")
    except KeyError as e:
        return error("KeyError {e}".format(e=e))

    instance = Instance(hook=data.dict(by_alias=True))
    return instance.run()


if __name__ == "__main__":
    print("Service started...")
    run(
        app,
        host=config.get("service_host"),
        port=int(config.get("service_port"))
    )
