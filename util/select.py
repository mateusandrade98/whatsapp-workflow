from typing import Optional
from ujson import dumps
from util import normal
from util import params
from util import settings
from util import request
from plugings import botpress

i_settings = settings.Settings()

config = i_settings.getConfig()
api = i_settings.getApi()


class Context:
    def __init__(self):
        self.index = 1
        self.first = 0
        self.params_values = {}
        self.args_values = {}
        self.last = {}
        self.me = None

    def get(self) -> dict:
        if not self.me is None:
            return self.me
        return {
            "context": self.index,
            "params_values": self.params_values,
            "args_values": self.args_values,
            "first": self.first
        }

    def set(self, context: dict = None) -> dict:
        self.me = self.get()
        if not "context" in self.me:
            self.me["context"] = self.get_index()
        for key in context:
            self.me.update({key: context[key]})
        return self.me

    def json(self) -> str:
        return dumps(self.get())

    def get_index(self) -> int:
        return self.index

    def get_first(self) -> int:
        return self.first

    def get_params_values(self) -> dict:
        return self.params_values

    def get_args_values(self) -> dict:
        return self.args_values

    def get_last(self) -> dict:
        return self.last

    def set_index(self, index: int = 0) -> bool:
        self.index = index
        return True

    def set_first(self, first: int = 0) -> bool:
        self.first = first
        return True

    def set_params_values(self, params_values: dict = None) -> bool:
        if params_values is None:
            params_values = {}
        self.params_values = params_values
        return True

    def set_args_values(self, args_values: dict = None) -> bool:
        if args_values is None:
            args_values = {}
        self.args_values = args_values
        return True

    def set_last(self, last: dict = None) -> bool:
        if not last is None:
            self.last = last
        return True


class Debug:
    def __init__(self, *args):
        if config["debug"]:
            print(args)


class Flow:
    def __init__(self, session: str = ''):
        self.debug = Debug
        self.posts = i_settings.getPosts(session=session)

    def error(self, msg: str = '') -> dict:
        return {"status": False, "data": {"error": msg, "version": config["version"]}}

    def getText(self, i: str = '') -> str:
        x = str(i).lower().lstrip().rstrip()
        return normal.normalizaTextNormal(x)

    def getTextMSG(self, i: str = '') -> str:
        x = str(i).lower().lstrip().rstrip()
        return normal.TextMSG(x)

    def getNumber(self, i: str = '') -> str:
        x = str(i).lower()
        return normal.normalizeNumbers(i=x)

    def getLogic(self, i: str = '') -> Optional[str]:
        x = str(i).lower()
        onlyText = normal.selectOnlyText(x)
        for l in self.posts["logic"]:
            if l in onlyText:
                return self.posts["logic"][l]
        return None

    def getLogicNav(self, i: str = '', context: dict = None, indexArgs: int = 0, navs: list = None) -> Optional[dict]:
        x = str(i).lower()
        textMachine = normal.normalizaTextNormal(i=x)
        NavsIsNone = False
        if navs is None:
            NavsIsNone = True
            navs = context["args"][indexArgs]["navs"]
        for q, n in enumerate(navs):
            self.debug("Nav->", str(n).lower() in textMachine or str(q + 1) == textMachine)
            if normal.normalizaTextNormal(i=n) == textMachine or str(q + 1) == textMachine:
                if NavsIsNone:
                    try:
                        return context["navigation"][indexArgs][navs[n]]
                    except KeyError:
                        return context["navigation"]["1"][navs[n]]
                else:
                    return navs[n]
        return None

    def getHashArg(self, arg: int = 0, indexContext: int = 0) -> str:
        return str(arg) + "-" + str(indexContext)

    def getType(self, index: str = '') -> str:
        Type = "confirm"
        try:
            return self.posts["types"][index]
        except KeyError:
            return Type
        except NameError:
            return Type

    def getChoices(self, indexContext: int = 0, i: str = '') -> Optional[dict]:
        for ch in self.posts["choices"][str(indexContext)]:
            textMachine = normal.normalizaTextNormal(i=str(i).lower())
            if ch == textMachine or str(normal.normalizaTextNormal(
                    self.posts["choices"][str(indexContext)][ch]["name"])).lower() in textMachine:
                return self.posts["choices"][str(indexContext)][ch]
        return None

    def logicToText(self) -> str:
        text = "\n\nENVIE SOMENTE O VALOR CORRESPONDENTE!\n\n"
        for log in self.posts["logic"]:
            text += "*" + log + "*\n"
        return text

    def requirements(self, lists: dict = None, context: dict = None) -> Optional[dict]:
        if "requirements" in lists:
            for r in lists["requirements"]:
                if r in context["params_values"]:
                    if context["params_values"][r] is None:
                        return lists["requirements"][r]
                else:
                    return lists["requirements"][r]
        return None

    def fillListItem(self, values: dict = None, key: str = "", label: str = "") -> str:
        k = "{" + key + "}"
        if key in values:
            v = values[key]
            if v and k:
                v = "*" + v + "*"
                return label.replace(k, v)
        return label.replace(k, "")

    def getList(self, lists: dict = None, key: str = "", values: dict = None, showEnd: int = 1) -> tuple:
        text = ""
        end = ""
        i = ""
        for k in lists:
            ek = ""
            if key == k:
                ek = "*"
                if showEnd:
                    end = "\n" + lists[k]["fill"]
                i = k
            t = ek + k + " - " + self.fillListItem(
                values=values,
                key=lists[k]["name"],
                label=lists[k]["label"]
            ).lstrip().rstrip() + ek
            text += t
            if "required" in lists[k]:
                if lists[k]["required"]:
                    text += " [Obrigatório]\n"
                else:
                    text += "\n"
            else:
                text += "\n"
        return i, text + end

    def choicesToText(self, choices: int = 0) -> str:
        text = "\n\nENVIE SOMENTE O VALOR CORRESPONDENTE!\n\n"
        for ch in self.posts["choices"][str(choices)]:
            text += "*" + str(ch) + " - " + str(self.posts["choices"][str(choices)][ch]["name"]) + "*\n"
        return text

    def getNavsToText(self, navs: dict = None) -> str:
        text = "\n\nENVIE SOMENTE O VALOR CORRESPONDENTE!\n\n"
        for i, nv in enumerate(navs):
            text += "*" + str(i + 1) + " - " + str(nv) + "*\n"
        return text

    def getArgs(self, context: int = 0) -> Optional[dict]:
        c = self.posts["contexts"][str(context)]
        if "args" in c:
            return c["args"]
        return None

    def buildActions(self, output: dict = None, context: dict = None) -> dict:
        if output["isbtn"] == 0:
            if not output in context["text"]:
                context["text"] += output["text"]
        else:
            context["inputs"] = output
        return context

    def makeButtons(self, TypeInteraction: str = "", qntElements: int = 0, data: dict = None) -> dict:
        canButtons = qntElements <= 3
        inputs = {}
        if TypeInteraction == "logic":
            text_logic = self.logicToText()
            inputs = {
                "isbtn": 0,
                "text": text_logic
            }
            if canButtons:
                logics = []
                for log in self.posts["logic"]:
                    logics.append(log)
                inputs = {
                    "isbtn": 1,
                    "title": "",
                    "description": "Escolha uma opção",
                    "buttons": ",".join(logics)
                }
            return inputs
        elif TypeInteraction == "choices":
            text_choices = self.choicesToText(choices=data["choices"])
            inputs = {
                "isbtn": 0,
                "text": text_choices
            }
            if canButtons:
                choices = []
                for ch in self.posts["choices"][str(data["choices"])]:
                    choices.append(self.posts["choices"][str(data["choices"])][ch]["name"])
                inputs = {
                    "isbtn": 1,
                    "title": "",
                    "description": "Escolha uma opção",
                    "buttons": ",".join(choices)
                }
            return inputs
        elif TypeInteraction == "navs":
            text_navs = self.getNavsToText(navs=data["navs"])
            inputs = {
                "isbtn": 0,
                "text": text_navs
            }
            if canButtons:
                navs = []
                for i, nv in enumerate(data["navs"]):
                    navs.append(nv)
                inputs = {
                    "isbtn": 1,
                    "title": "",
                    "description": "Escolha uma opção",
                    "buttons": ",".join(navs)
                }
            return inputs
        elif TypeInteraction == "custom":
            if "buttons" in data and canButtons:
                inputs = {
                    "isbtn": 1,
                    "title": "",
                    "description": "",
                    "buttons": ",".join(data["buttons"])
                }
        return inputs

    def addParams(self, _params: dict = None, this_params: dict = None, keys: str = None, value: str = None) -> dict:
        new_params = this_params
        if type(keys) == str:
            if type(value) == str:
                value = {
                    keys: value
                }
            keys = [keys]
        self.debug("addParam:keys->", keys)
        for n, param in enumerate(_params):
            if param in keys and param in value and not value[param] is None:
                new_params.update({param: value[param]})
                self.debug("addParam:[{0}]updateParam->".format(param), value[param])
            if not param in this_params:
                new_params.update({param: None})
        return new_params

    def removeParamsValues(self, data: dict = None, context: dict = None) -> dict:
        if "params_values" in context:
            p_v = context["params_values"]
            for d in data:
                if d in p_v:
                    if d == "number" or d == "name":  # constants (name, number)
                        continue
                    p_v.update({d: None})
            context["params_values"] = p_v
        return context

    def getContext(self, index: int = 0) -> tuple:
        index = str(index)
        # isBoolean
        if self.posts["contexts"][index]["isBoolean"]:
            act_boolean = self.makeButtons(
                TypeInteraction="logic",
                qntElements=len(self.posts["logic"]),
                data={}
            )

            self.posts["contexts"][index] = self.buildActions(
                output=act_boolean,
                context=self.posts["contexts"][index]
            )

        # isChoices
        if self.posts["contexts"][index]["isChoice"]:
            act_choices = self.makeButtons(
                TypeInteraction="choices",
                qntElements=len(self.posts["choices"][str(self.posts["contexts"][index]["choices"])]),
                data={
                    "choices": self.posts["contexts"][index]["choices"]
                }
            )

            self.posts["contexts"][index] = self.buildActions(
                output=act_choices,
                context=self.posts["contexts"][index]
            )
        self.debug("posts->", self.posts["contexts"][index])
        return index, self.posts["contexts"][index]

    def generateLogicList(self, data: dict = None, key: str = "", isArray: int = 1) -> str:
        text = ""
        if isArray:
            try:
                key = key[0]
            except IndexError:
                return text
            for i, d in enumerate(data):
                text += str(i + 1) + " - " + d[key] + "\n"

        if not isArray:
            for i, d in enumerate(data):
                text += str(i + 1) + " - " + data[d][key] + "\n"
        return text

    def LogicList(self, data: dict = None, params: list = None, key: str = "", content: str = "") -> Optional[tuple]:
        try:
            key = params[params.index(key)]
        except IndexError:
            return None
        except ValueError:
            return None
        if not content.isnumeric():
            return None
        for i, d in enumerate(data):
            if (i + 1) == int(content) or (len(content) > 2 and d[key] == content):
                return data[i], d[key]
        return None

    def isArgInList(self, key: str = "", lists: dict = None) -> bool:
        if key in lists:
            return True
        return False

    def isFullList(self, lists: dict = None, index: int = 0, args_values: dict = None) -> bool:
        for d in lists:
            arg_hash = self.getHashArg(
                arg=d,
                indexContext=index
            )
            if "required" in lists[d] and not lists[d]["required"]:
                continue
            if arg_hash in args_values and "confirmed" in args_values[arg_hash] and args_values[arg_hash]["confirmed"]:
                continue
            return False
        return True

    def resetItens(self, resets: dict = None, context: dict = None) -> Context:
        for reset in resets:
            if reset in context["params_values"]:
                context["params_values"].update({reset: None})
            for values in context["args_values"]:
                if type(context["args_values"][values]) == dict and reset in context["args_values"][values]:
                    context["args_values"][values] = {}
        return context

    def isKey(self, args: dict = None, content: str = "") -> bool:
        for arg in args:
            if arg in content:
                return True
        return False

    def isFilledArgs(self, args: dict = None, context: dict = None, indexContext: int = 0) -> bool:
        for arg in args:
            arg_hash = self.getHashArg(
                arg=arg,
                indexContext=indexContext
            )
            try:
                if "confirmed" in context and context["args_values"][arg_hash]["confirmed"]:
                    continue
                else:
                    return False
            except KeyError:
                return False
        return True

    def getNextItemList(self, index: int = 0, lists: dict = None, args_values: dict = None) -> Optional[tuple]:
        for d in lists:
            arg_hash = self.getHashArg(
                arg=d,
                indexContext=index
            )
            if "required" in lists[d] and not lists[d]["required"]:
                continue
            if arg_hash in args_values and "confirmed" in args_values[arg_hash] and args_values[arg_hash]["confirmed"]:
                continue
            return d, lists[d]
        return None

    def Sender(self, context: dict = None, content: str = "", indexContext: int = 0) -> Optional[tuple]:
        if "request" in context:
            rq = context["request"]
            if "navs" in rq:
                if "sender" in context and not "fast" in context["sender"]:
                    act_request = self.makeButtons(
                        TypeInteraction="navs",
                        qntElements=len(rq["navs"]),
                        data={
                            "navs": rq["navs"]
                        }
                    )

                    context = self.buildActions(
                        output=act_request,
                        context=context
                    )

                rq_navs = self.getLogicNav(
                    i=content,
                    context=context,
                    indexArgs=0,
                    navs=rq["navs"]
                )

                if rq_navs:
                    if "type" in rq_navs:
                        rq_action = self.posts["types"][rq_navs["type"]]
                        if rq_action == "send" or rq_action == "confirm":
                            if "sender" in context and not "fast" in context["sender"]:
                                del context["inputs"]
                            pass
                        elif rq_action == "clear":
                            if "args_values" in context:
                                context["args_values"] = {}
                                context["text"] = rq["cleaned"]
                                del context["inputs"]
                                context = self.removeParamsValues(
                                    data=rq["params"],
                                    context=context
                                )
                            return indexContext, context
                        elif rq_action == "exit":
                            pass
                        else:
                            return indexContext, context
                    # confirm shipment
                    rq_api = api["requests"]
                    n_values = {}
                    n_values.update(rq_api)
                    n_values.update(context["params_values"])
                    b_params = params.BuildParams(
                        params=rq["params"],
                        values=n_values
                    )
                    url = b_params.setFormat(s=rq["url"])
                    self.debug("url->", url)
                    rq_data = b_params.setData(data=rq["data"])
                    body_request = {
                        "url": url,
                        "method": rq["method"],
                        "headers": rq_api["headers"],
                        "data": rq_data
                    }
                    self.debug("body_request->", body_request)
                    call_request = request.Request(
                        body_request=body_request
                    ).execute()
                    self.debug("call_request->", call_request)
                    if call_request:
                        context_response = rq["response"]
                        if call_request["status"]:
                            if "clear_params" in context_response:
                                context = self.removeParamsValues(
                                    data=rq["params"],
                                    context=context
                                )
                                context["args_values"] = {}
                            if context_response["show"]:
                                if rq["success"] is None:
                                    text_success = params.BuildParams(
                                        params=context_response["params"],
                                        values=call_request
                                    ).setText()
                                else:
                                    text_success = rq["success"]
                                context["text"] = text_success
                                if context_response["changeContext"]:
                                    i_c, context = self.getContext(index=context_response["context"])
                                    return i_c, context
                            else:
                                if context_response["changeContext"]:
                                    i, c = self.getContext(index=context_response["context"])
                                    try:
                                        c["params_values"] = self.addParams(
                                            _params=context["sender"]["response"]["params"],
                                            this_params=context["params_values"],
                                            keys=context["sender"]["param_data"],
                                            value=call_request["pix_pj"]
                                        )
                                    except KeyError:
                                        pass
                                    return i, c
                                else:
                                    return self.getContext(index=context["positiveContext"])
                        else:
                            f_error = str(rq["error"])
                            if "msg" in call_request:
                                if "{error_request}" in f_error:
                                    f_error = f_error.format(error_request=call_request["msg"])
                            context["args_values"] = {}
                            context["text"] = f_error
                return indexContext, context

    def reqList(self, context: dict = None, arg: str = "", content: str = None, indexContext: int = 0,
                normalContent: str = "", arg_hash: str = "", act_navs: dict = None) -> dict:
        modBeta = (("modBeta" in context) and (context["modBeta"]))

        if "filter" in context["args"][arg] and modBeta:
            context["text"] = context["lists"][arg]["fill"]
            context["args_values"]["itemSelected"] = arg
            context["args_values"]["itemChanged"] = 1
            return context

        if "request" in context["args"][arg]:
            rq = context["args"][arg]["request"]

            rq_api = api["requests"]
            n_values = {}
            n_values.update(rq_api)

            # set params not defined
            for p in context["params"]:
                if not p in n_values:
                    n_values.update({p: None})

            # seleciona nova página
            n_page = False
            if not content.isnumeric():
                # button next page
                if content == self.posts["buttons"]["more"]:
                    if "page" in context["params_values"] and \
                            not context["params_values"]["page"] is None:
                        context["params_values"]["page"] += 1
                        n_page = True
                        if "limitPages" in context["params_values"]:
                            if context["params_values"]["page"] > \
                                    context["params_values"]["limitPages"]:
                                context["params_values"]["page"] = \
                                    context["params_values"]["limitPages"]
                    else:
                        context["params_values"]["page"] = 1

                # button turn back page
                if content == self.posts["buttons"]["back"]:
                    if "page" in context["params_values"] and \
                            not context["params_values"]["page"] is None:
                        if context["params_values"]["page"] > 1:
                            context["params_values"]["page"] -= 1
                            n_page = True

                # button back to menu
                if content == self.posts["buttons"]["menu"] and modBeta:
                    context["params_values"]["page"] = None
                    context["args_values"]["itemSelected"] = "0"
                    context["args_values"]["itemInConfirmation"] = "0"
                    context = self.getBackMenu(
                        context=context,
                        lists=context["lists"],
                        values=context["params_values"],
                        key="0",
                        showEnd=0,
                        indexContext=indexContext
                    )
                    return context

            # update params_values in n_values
            n_values.update(context["params_values"])

            # default params
            if "defaults_params" in rq:
                for dp in n_values:
                    if dp in rq["defaults_params"] and n_values[dp] is None:
                        n_values[dp] = rq["defaults_params"][dp]

            if "page" in context["params_values"]:
                self.debug("page->", context["params_values"]["page"])

            self.debug("n_values->", n_values)
            context["params_values"] = n_values

            b_params = params.BuildParams(
                params=rq["params"],
                values=n_values
            )
            url = b_params.setFormat(s=rq["url"])
            rq_data = b_params.setData(data=rq["data"])

            body_request = {
                "url": url,
                "method": rq["method"],
                "headers": rq_api["headers"],
                "data": rq_data
            }
            self.debug("body requests->", body_request)

            call_request = request.Request(
                body_request=body_request
            ).execute()
            self.debug("Response-> ", call_request)

            if call_request:
                if call_request["status"]:
                    if rq["response"]["isArray"]:
                        logicList = self.generateLogicList(
                            data=call_request["data"],
                            key=rq["response"]["params"]
                        )

                        if not modBeta:
                            context["text"] += "\n\nEnvie \"0\" para voltar a lista de seleção."

                        if call_request["pages"] > 1:
                            context["text"] = context["lists"][arg]["fill"] + "\n" + logicList + "\n" + \
                                              context["lists"][arg]["fill"]
                        else:
                            context["text"] = context["lists"][arg]["fill"] + "\n\n" + logicList + "\n" + \
                                              context["lists"][arg]["fill"]

                        # define o limite da paginacao
                        if "pages" in call_request:
                            context["params_values"]["limitPages"] = call_request["pages"]

                        if "page" in context["params_values"] and \
                                "limitPages" in context["params_values"]:

                            if context["params_values"]["page"] is None:
                                context["params_values"]["page"] = 1

                            context["text"] += "\n" + str(context["params_values"]["page"]) \
                                               + " de " + str(
                                context["params_values"]["limitPages"]) + " páginas"

                            if context["params_values"]["limitPages"] >= \
                                    context["params_values"]["page"]:

                                n_buttons = []

                                if context["params_values"]["page"] < \
                                        context["params_values"]["limitPages"]:
                                    n_buttons.append(self.posts["buttons"]["more"])

                                if context["params_values"]["page"] > 1:
                                    n_buttons.append(self.posts["buttons"]["back"])

                                if not modBeta:
                                    n_buttons.append(self.posts["buttons"]["menu"])

                                if n_buttons:
                                    act_more = self.makeButtons(
                                        TypeInteraction="custom",
                                        data={
                                            "buttons": n_buttons
                                        }
                                    )
                                    context = self.buildActions(
                                        output=act_more,
                                        context=context
                                    )

                                self.debug("n_buttons->", n_buttons)

                        # checa se houve uma mundação de opção
                        if "itemChanged" in context["args_values"]:
                            if context["args_values"]["itemChanged"]:
                                context["args_values"]["itemChanged"] = 0
                                return context

                        sl = self.LogicList(
                            data=call_request["data"],
                            params=rq["response"]["params"],
                            key=context["args"][arg]["param_data"],
                            content=normalContent
                        )

                        s_param, s_data = None, None
                        if sl:
                            s_data, s_param = sl
                            self.debug("s_param->", s_param)
                            self.debug("s_data->", s_data)

                        if not s_param is None:
                            # valida a opção selecionada
                            context["args_values"]["itemChanged"] = 0
                            context["args_values"]["itemInConfirmation"] = arg_hash
                            context["text"] = context["args"][arg]["filled"]
                            context["args_values"][arg_hash] = {
                                "confirmed": 0,
                                context["args"][arg]["param_data"]: s_param
                            }
                            context = self.buildActions(
                                output=act_navs,
                                context=context
                            )
                            try:
                                # set reset params
                                if "reset" in rq["response"]:
                                    context["args_values"]["reset"] = rq["response"]["reset"]

                                # add params
                                context["params_values"] = self.addParams(
                                    _params=context["params"],
                                    this_params=context["params_values"],
                                    keys=rq["response"]["params"],
                                    value=s_data
                                )
                            except KeyError:
                                pass
                        else:
                            # option invalid
                            if not n_page and not modBeta:
                                context["text"] += "\n*Opção escolhida é inválida*."
                        return context
                else:
                    f_error = str(rq["error"])
                    if "msg" in call_request:
                        if "{error_request}" in f_error:
                            f_error = f_error.format(error_request=call_request["msg"])
                    context["text"] = f_error
                    context["args_values"] = {}
                    if modBeta:
                        n_hash = str(int(arg) - 1)
                        n_hash_arg = "-".join((n_hash, indexContext))
                        context["args_values"]["itemChanged"] = 0
                        context["args_values"]["itemSelected"] = n_hash
                        context["args_values"]["itemInConfirmation"] = "0"
                        context["params_values"][context["args"][n_hash]["param_data"]] = None

                        if "itemSelected" in context["args_values"]:
                            context["args_values"]["itemChanged"] = 0
                            context["text"] = f_error
                            if "lists" in context and context["lists"][context["args_values"]["itemSelected"]]:
                                context["text"] += "\n\n" + context["lists"][context["args_values"]["itemSelected"]][
                                    "fill"]
                                return context

                        act_navs = self.makeButtons(
                            TypeInteraction="custom",
                            qntElements=1,
                            data={
                                "buttons": [
                                    self.posts["buttons"]["restart"]
                                ]
                            }
                        )

                        context = self.buildActions(
                            output=act_navs,
                            context=context
                        )

                        context["args_values"]["error_list"] = 1

                        return context
                    return context

    def getBackMenu(self, context: dict = None, lists: dict = None, values: dict = None, key: str = "", showEnd: int = 0, indexContext: int = 0) -> dict:
        modBeta = (("modBeta" in context) and (context["modBeta"]))
        il, logicList = self.getList(
            lists=lists,
            values=values,
            key=key,
            showEnd=showEnd
        )
        isFullList = self.isFullList(
            lists=context["lists"],
            index=indexContext,
            args_values=context["args_values"]
        )
        self.debug("isFullList->", isFullList)

        # modBeta
        if not isFullList and modBeta:
            next_mod = {"modBeta": True}
            i, nextItem = self.getNextItemList(
                index=indexContext,
                lists=lists,
                args_values=context["args_values"]
            )
            next_args = context["args"][str(i)]
            next_mod["index"] = str(i)
            next_mod["context"] = context
            next_mod["arg"] = next_args
            next_mod["list"] = lists[str(i)]
            return next_mod

        if isFullList:
            bts_sender = self.makeButtons(
                TypeInteraction="custom",
                data={
                    "buttons": [
                        self.posts["buttons"]["sender"]
                    ]
                }
            )
            context = self.buildActions(
                output=bts_sender,
                context=context
            )
        context["text"] = logicList
        return context

    def setArgs(self, context: dict = None, args: dict = None, content: str = "", indexContext: int = 0) -> Optional[dict]:
        # is Beta mod
        betaMod = (("modBeta" in context) and (context["modBeta"]))
        for arg in args:
            if config["debug_args"] != 0:
                arg = config["debug_args"]

            arg_hash = self.getHashArg(
                arg=arg,
                indexContext=indexContext
            )

            context["args_values"]["hashSelected"] = arg_hash

            in_list = False
            if "lists" in context:
                in_list = self.isArgInList(
                    key=arg,
                    lists=context["lists"]
                )

            # checa se lista esta preenchida
            isFullList = False
            if in_list:
                isFullList = self.isFullList(
                    lists=context["lists"],
                    index=indexContext,
                    args_values=context["args_values"]
                )
                self.debug("isFullList->", isFullList)
                if isFullList:
                    # sender
                    if content == self.posts["buttons"]["sender"] or betaMod:
                        if "sender" in context:
                            rq = context["sender"]
                            rq_api = api["requests"]
                            n_values = {}
                            n_values.update(rq_api)
                            n_values.update(context["params_values"])
                            b_params = params.BuildParams(
                                params=rq["params"],
                                values=n_values
                            )
                            url = b_params.setFormat(s=rq["url"])
                            self.debug("url->", url)
                            rq_data = b_params.setData(data=rq["data"])
                            body_request = {
                                "url": url,
                                "method": rq["method"],
                                "headers": rq_api["headers"],
                                "data": rq_data
                            }
                            self.debug("body_request->", body_request)
                            call_request = request.Request(
                                body_request=body_request
                            ).execute()
                            self.debug("call_request->", call_request)
                            if call_request:
                                if "status" in call_request and call_request["status"]:
                                    i_c, context2 = self.getContext(index=rq["response"]["context"])
                                    context2["params_values"] = self.removeParamsValues(
                                        data=rq["params"],
                                        context=context
                                    )
                                    context2["args_values"] = {}
                                    return context2
                        return context

            # não tabular quando item estiver selecionado
            if in_list and ("itemSelected" in context["args_values"] and context["args_values"]["itemSelected"] != "0"
                            and context["args_values"]["itemSelected"] != arg):
                continue

            # não tabular quando é um item comum e não for obrigatório
            if not in_list and not context["args"][arg]["required"]:
                continue

            act_navs = self.makeButtons(
                TypeInteraction="navs",
                qntElements=len(context["args"][arg]["navs"]),
                data={
                    "navs": context["args"][arg]["navs"]
                }
            )

            # volta para o menu de seleção
            if content == "0" and in_list and not betaMod:
                context["args_values"]["itemSelected"] = "0"
                if "page" in context["params_values"]:
                    context["params_values"]["page"] = None
                context = self.getBackMenu(
                    context=context,
                    lists=context["lists"],
                    values=context["params_values"],
                    key="0",
                    showEnd=0,
                    indexContext=indexContext
                )
                return context

            inConfirmation = "itemInConfirmation" in context["args_values"] and \
                             (context["args_values"]["itemInConfirmation"] != "0")

            # seleciona um item da lista para ser preenchido
            if content.isnumeric() and in_list:
                # nova atribuição de seleção
                if not inConfirmation:
                    if "itemSelected" in context["args_values"]:
                        if context["args_values"]["itemSelected"] == "0":
                            if content in context["lists"]:
                                context["args_values"]["itemSelected"] = str(int(content))
                                context["args_values"]["itemChanged"] = 1
                    else:
                        context["args_values"]["itemSelected"] = str(int(content))
                        context["args_values"]["itemChanged"] = 1

                # muda o hash para o arg selecionado
                if not inConfirmation:
                    if "itemSelected" in context["args_values"]:
                        if context["args_values"]["itemSelected"] != "0":
                            arg = context["args_values"]["itemSelected"]
                            arg_hash = self.getHashArg(
                                arg=arg,
                                indexContext=indexContext
                            )

                # renova item da lista
                if not inConfirmation and not betaMod:
                    if arg_hash in context["args_values"]:
                        if "confirmed" in context["args_values"][arg_hash] and \
                                context["args_values"]["itemSelected"] == arg:
                            if context["args_values"][arg_hash]["confirmed"]:
                                context["args_values"][arg_hash]["confirmed"] = 0
                                context["args_values"][arg_hash]["clean_confirmation"] = 1
                                context["args_values"]["itemChanged"] = 1
                                context["text"] = context["args"][arg]["filled"]
                                context = self.buildActions(
                                    output=act_navs,
                                    context=context
                                )
                                return context

            self.debug("Args->", arg)

            if "itemSelected" in context["args_values"]:
                self.debug("S->", context["args_values"]["itemSelected"])

            self.debug("inConfirmation->", inConfirmation)

            if arg_hash in context["args_values"]:
                self.debug("args_values->", context["args_values"][arg_hash])

            # normalize input content
            normalContent = ""
            if context["args"][arg]["type"] == "number":
                normalContent = self.getNumber(i=content)
            elif context["args"][arg]["type"] == "text":
                normalContent = self.getText(i=content).upper()

            try:
                if arg_hash in context["args_values"]:
                    if context["args_values"][arg_hash]:
                        if "confirmed" in context["args_values"][arg_hash]:
                            if context["args_values"][arg_hash]["confirmed"]:
                                continue
                            else:
                                context["text"] = context["args"][arg]["filled"]

                        nav_args = self.getLogicNav(i=content, context=context, indexArgs=arg)
                        if not nav_args is None:
                            nav_type = self.getType(index=str(nav_args["type"]))
                            if nav_type == "confirm":
                                # update confirmation
                                context["args_values"][arg_hash].update({
                                    "confirmed": 1
                                })
                                # checa se houve uma limpeza de dados
                                if "clean_confirmation" in context["args_values"][arg_hash]:
                                    if context["args_values"][arg_hash]["clean_confirmation"]:
                                        context = self.getBackMenu(
                                            context=context,
                                            lists=context["lists"],
                                            values=context["params_values"],
                                            key="0",
                                            showEnd=0,
                                            indexContext=indexContext
                                        )
                                        context["args_values"][arg_hash]["clean_confirmation"] = 0
                                        context["args_values"]["itemSelected"] = "0"
                                        context["args_values"]["itemInConfirmation"] = "0"
                                        context["text"] += context["args"][arg]["confirmed"]
                                        return context

                                # call next args
                                context["text"] = context["args"][arg]["confirmed"]
                                if len(context["args"]) > 1:
                                    try:
                                        next_arg = str(int(arg) + 1)
                                        if context["args"][next_arg]["required"]:
                                            context["text"] += " " + context["args"][next_arg]["empty"]
                                    except KeyError:
                                        pass

                                # item de uma lista preenchido
                                if "itemSelected" in context["args_values"] and in_list:
                                    # reset params
                                    if "reset" in context["args_values"] and not betaMod:
                                        if context["args_values"]["reset"]:
                                            context = self.resetItens(
                                                resets=context["args_values"]["reset"],
                                                context=context
                                            )
                                            self.debug("reset->", context["args_values"]["reset"])
                                            context["args_values"]["reset"] = []

                                    if not betaMod:
                                        context = self.getBackMenu(
                                            context=context,
                                            lists=context["lists"],
                                            values=context["params_values"],
                                            key="0",
                                            showEnd=0,
                                            indexContext=indexContext
                                        )

                                        context["args_values"]["itemSelected"] = "0"
                                        context["args_values"]["itemInConfirmation"] = "0"
                                        context["text"] += context["args"][arg]["confirmed"]
                                        if "page" in context["params_values"]:
                                            context["params_values"]["page"] = None
                                        self.debug("confirmed->", inConfirmation)

                                if betaMod and not isFullList:

                                    if "sender" in context:
                                        if "fast" in context["sender"]:
                                            i, c = self.Sender(context=context, content=content, indexContext=indexContext)
                                            c = dict(c)
                                            c["context"] = i
                                            return c

                                    # seleciona outro item da lista
                                    nextItem = self.getNextItemList(
                                        index=indexContext,
                                        lists=context["lists"],
                                        args_values=context["args_values"]
                                    )

                                    if nextItem:
                                        i, nextItem = nextItem

                                        context["args_values"]["itemSelected"] = arg
                                        context["args_values"]["itemChanged"] = 0
                                        context["args_values"]["itemInConfirmation"] = "0"

                                        self.debug("NextItem->", nextItem)

                                        next_mod = {
                                            "modBeta": True
                                        }

                                        next_args = context["args"][i]
                                        next_mod["index"] = i
                                        next_mod["context"] = context
                                        next_mod["arg"] = next_args
                                        next_mod["list"] = context["lists"][i]

                                        return next_mod

                                if "request" in context:
                                    i, c = self.Sender(
                                        context=context,
                                        content=content,
                                        indexContext=indexContext
                                    )
                                    return c

                                return context
                            elif nav_type == "cancel":
                                # reset args_values while clean_confirmation = 1
                                if "clean_confirmation" in context["args_values"][arg_hash]:
                                    self.debug(
                                        "cancel:clean_confirmation->",
                                        context["args_values"][arg_hash]["clean_confirmation"]
                                    )
                                    if context["args_values"][arg_hash]["clean_confirmation"]:
                                        # reset params
                                        if in_list and "request" in context["args"][arg]:
                                            if "reset" in context["args"][arg]["request"]["response"]:
                                                context = self.resetItens(
                                                    resets=context["args"][arg]["request"]["response"]["reset"],
                                                    context=context
                                                )
                                                self.debug(
                                                    "reset->",
                                                    context["args"][arg]["request"]["response"]["reset"]
                                                )

                                # cancel
                                context["args_values"][arg_hash] = {}
                                context["text"] = context["args"][arg]["canceled"]

                                if "reset" in context:
                                    context = self.removeParamsValues(
                                        data=context["reset"],
                                        context=context
                                    )

                                if "back" in context:
                                    i, c = self.getContext(index=context["back"])
                                    return c

                                # item de uma lista preenchido
                                if "itemSelected" in context["args_values"] and in_list:
                                    # limpa os params_values da lista
                                    if "request" in context["args"][arg]:
                                        if "params" in context["args"][arg]["request"]["response"]:
                                            context = self.removeParamsValues(
                                                data=context["args"][arg]["request"]["response"]["params"],
                                                context=context
                                            )
                                    context = self.getBackMenu(
                                        context=context,
                                        lists=context["lists"],
                                        values=context["params_values"],
                                        key="0",
                                        showEnd=0,
                                        indexContext=indexContext
                                    )

                                    # modBeta
                                    if betaMod:
                                        context = context["context"]
                                        context["args_values"][arg_hash] = {}
                                        context["args_values"]["itemChanged"] = 0
                                        context["args_values"]["itemSelected"] = "0"
                                        context["args_values"]["itemInConfirmation"] = "0"

                                        act_navs = self.makeButtons(
                                            TypeInteraction="navs",
                                            qntElements=len(context["args"][arg]["navs"]),
                                            data={
                                                "navs": context["args"][arg]["navs"]
                                            }
                                        )

                                        return self.reqList(
                                            context=context,
                                            arg=arg,
                                            content="",
                                            indexContext=indexContext,
                                            normalContent="",
                                            arg_hash=arg_hash,
                                            act_navs=act_navs
                                        )
                                    else:
                                        context["args_values"]["itemSelected"] = "0"
                                        context["args_values"]["itemInConfirmation"] = "0"

                                    if "page" in context["params_values"]:
                                        context["params_values"]["page"] = None
                                    context["text"] += context["args"][arg]["canceled"]
                                return context
                            elif nav_type == "restart":

                                context["args_values"] = {}
                                context["params_values"]["page"] = None
                                context["args_values"]["itemSelected"] = "0"
                                context["args_values"]["itemChanged"] = 0
                                context["args_values"]["itemInConfirmation"] = "0"

                                if "params" in context["args"][arg]["request"]["response"]:
                                    context = self.removeParamsValues(
                                        data=context["args"][arg]["request"]["response"]["params"],
                                        context=context
                                    )

                                if "back" in context:
                                    i, c = self.getContext(index=context["back"])
                                    return c

                                if betaMod:
                                    nextItem = self.getNextItemList(
                                        index=indexContext,
                                        lists=context["lists"],
                                        args_values=context["args_values"]
                                    )

                                    if nextItem:
                                        i, nextItem = nextItem

                                        self.debug("NextItem->", nextItem)

                                        next_mod = {
                                            "modBeta": True
                                        }

                                        next_args = context["args"][i]
                                        next_mod["index"] = i
                                        next_mod["context"] = context
                                        next_mod["arg"] = next_args
                                        next_mod["list"] = context["lists"][i]

                                        return next_mod

                                return self.getBackMenu(
                                        context=context,
                                        lists=context["lists"],
                                        values=context["params_values"],
                                        key="0",
                                        showEnd=0,
                                        indexContext=indexContext
                                    )
                        # input logic invalid
                        context = self.buildActions(
                            output=act_navs,
                            context=context
                        )
                        return context

                # Seleção de lista
                if "lists" in context:
                    if in_list:
                        if not "itemSelected" in context["args_values"]:
                            context["args_values"]["itemSelected"] = "0"

                        if context["args_values"]["itemSelected"] == "0":
                            context = self.getBackMenu(
                                context=context,
                                lists=context["lists"],
                                values=context["params_values"],
                                key="0",
                                showEnd=0,
                                indexContext=indexContext
                            )
                            return context

                        arg_hash = self.getHashArg(
                            arg=context["args_values"]["itemSelected"],
                            indexContext=indexContext
                        )

                        if not arg_hash in context["args_values"]:
                            context["args_values"][arg_hash] = {}

                        required = self.requirements(
                            lists=context["lists"][arg],
                            context=context
                        )

                        self.debug("required->", required)

                        # checa se ha parametro requerido
                        if not required is None:
                            context = self.getBackMenu(
                                context=context,
                                lists=context["lists"],
                                values=context["params_values"],
                                key="0",
                                showEnd=0,
                                indexContext=indexContext
                            )
                            context["args_values"]["itemSelected"] = "0"
                            context["text"] += required
                            return context

                        # busca lista de itens
                        if not context["args_values"][arg_hash]:
                            if not "filter" in context["args"][arg]:
                                return self.reqList(
                                    context=context,
                                    arg=arg,
                                    content=content,
                                    indexContext=indexContext,
                                    normalContent=normalContent,
                                    arg_hash=arg_hash,
                                    act_navs=act_navs
                                )

                            # filter
                            if "type" in context["args"][arg]["filter"]:
                                context = self.getBackMenu(
                                    context=context,
                                    lists=context["lists"],
                                    values=context["params_values"],
                                    key="0",
                                    showEnd=0,
                                    indexContext=indexContext
                                )

                                if "context" in context and betaMod:
                                    context = context["context"]

                                if "itemChanged" in context["args_values"] and context["args_values"]["itemChanged"] and not betaMod:
                                    context["args_values"]["itemChanged"] = 0
                                    if not "filter" in context["args"][arg]:
                                        return self.reqList(
                                            context=context,
                                            arg=arg,
                                            content=content,
                                            indexContext=indexContext,
                                            normalContent=normalContent,
                                            arg_hash=arg_hash,
                                            act_navs=act_navs
                                        )

                                    context["text"] = context["lists"][arg]["fill"]

                                    return context

                                if context["args"][arg]["filter"]["type"] == "number":
                                    minInput = 0
                                    maxInput = 3000
                                    if "min" in context["args"][arg]["filter"]["range"]:
                                        minInput = context["args"][arg]["filter"]["range"]["min"]
                                    if "max" in context["args"][arg]["filter"]["range"]:
                                        maxInput = context["args"][arg]["filter"]["range"]["max"]

                                    try:
                                        if not content.isnumeric():
                                            context["text"] = "Você precisa enviar um " \
                                                              "*número* entre {min} e {max}.".format(
                                                min=minInput,
                                                max=maxInput
                                            )
                                            return context

                                        numberContent = int(content)
                                        validNumber = (minInput <= numberContent <= maxInput)
                                        if validNumber:

                                            # choices
                                            if "choices" in context["args"][arg]["filter"]:
                                                try:
                                                    choice = context["args"][arg]["filter"]["choices"][
                                                        str(numberContent)]

                                                    context["args_values"][arg_hash] = {
                                                        "confirmed": 0,
                                                        context["args"][arg]["param_data"]: numberContent
                                                    }

                                                    if "param" in context["args"][arg]["filter"]:
                                                        context["params_values"][
                                                            context["args"][arg]["filter"]["param"]] = choice.upper()

                                                    context = self.buildActions(
                                                        output=act_navs,
                                                        context=context
                                                    )

                                                    context["text"] = context["args"][arg]["filled"]

                                                    context["args_values"]["itemInConfirmation"] = "1"

                                                    try:
                                                        context["params_values"] = self.addParams(
                                                            _params=context["params"],
                                                            this_params=context["params_values"],
                                                            keys=context["args"][arg]["param_data"],
                                                            value=self.getTextMSG(i=content)
                                                        )
                                                    except KeyError:
                                                        pass

                                                    # success: valid
                                                    return context

                                                except KeyError:
                                                    context["text"] = context["lists"][arg]["fill"]
                                                    context["text"] += "Você precisa enviar um " \
                                                                       "*número* entre {min} e {max}.".format(
                                                        min=minInput,
                                                        max=maxInput
                                                    )
                                                    return context

                                            # normal number
                                            context["args_values"][arg_hash] = {
                                                "confirmed": 0,
                                                context["args"][arg]["param_data"]: numberContent
                                            }

                                            context = self.buildActions(
                                                output=act_navs,
                                                context=context
                                            )

                                            context["text"] = context["args"][arg]["filled"]

                                            context["args_values"]["itemInConfirmation"] = "1"

                                            try:
                                                context["params_values"] = self.addParams(
                                                    _params=context["params"],
                                                    this_params=context["params_values"],
                                                    keys=context["args"][arg]["param_data"],
                                                    value=self.getTextMSG(i=content)
                                                )
                                            except KeyError:
                                                pass

                                            # success: valid
                                            return context

                                        else:
                                            context["text"] = "Você precisa enviar um " \
                                                              "*número* entre {min} e {max}.".format(
                                                min=minInput,
                                                max=maxInput
                                            )
                                            return context
                                    except TypeError:
                                        context["text"] = "Você precisa enviar um " \
                                                          "*número* entre {min} e {max}.".format(
                                            min=minInput,
                                            max=maxInput
                                        )
                                        return context

                                if context["args"][arg]["filter"]["type"] == "text":
                                    pass

                # normal args empty
                context["text"] = context["args"][arg]["filled"]
                if not (context["args"][arg]["minLen"] <= len(normalContent) <= context["args"][arg]["maxLen"]):
                    context["text"] = str(context["args"][arg]["invalid"]).format(
                        minLen=context["args"][arg]["minLen"],
                        maxLen=context["args"][arg]["maxLen"]
                    )
                    return context

                context["args_values"][arg_hash] = {
                    "confirmed": 0,
                    context["args"][arg]["param_data"]: self.getTextMSG(i=content)
                }

                # context["args_values"][arg_hash].update({
                #     "confirmed": 1
                # })
                # context["args_values"][arg_hash]["clean_confirmation"] = 0
                # context["args_values"]["itemSelected"] = "0"
                # context["args_values"]["itemInConfirmation"] = "0"
                # context["text"] += context["args"][arg]["confirmed"]

                # if not "noConfirm" in context["args"][arg]:

                context = self.buildActions(
                    output=act_navs,
                    context=context
                )

                try:
                    context["params_values"] = self.addParams(
                        _params=context["params"],
                        this_params=context["params_values"],
                        keys=context["args"][arg]["param_data"],
                        value=self.getTextMSG(i=content)
                    )
                except KeyError:
                    pass
                return context
            except KeyError as e:
                return self.error(msg=e.__str__())
        return None

    def getNewContext(self, indexContext: int = 0, context: dict = None, content: str = "") -> object:
        if context is None:
            return indexContext, context

        if "plugin" in context and context["plugin"]:
            bp = botpress.BotPress(context=context, config=config)
            bp_source = bp.active()
            if "bot_id" in bp_source:
                _phone = context["params_values"]["number"] if "number" in context["params_values"] else ""
                response_bp = bp.getContext(source=bp_source, idUser=_phone)
                return response_bp

        if "inputs" in context:
            del context["inputs"]

        if context["isBoolean"]:
            ch_boolean = self.getLogic(i=content)
            if ch_boolean is None:
                return self.getContext(index=indexContext)
            if ch_boolean:
                return self.getContext(index=context["positiveContext"])
            else:
                return self.getContext(index=context["negativeContext"])

        if context["isChoice"]:
            try:
                ncontext = self.getChoices(indexContext=context["choices"], i=content)
                if not ncontext is None:
                    return self.getContext(index=ncontext["context"])
                return self.getContext(index=indexContext)
            except KeyError as e:
                return self.error(msg=e.__str__())

        if context["isInputText"]:
            args = self.getArgs(context=indexContext)
            if args:
                if "args_values" in context:
                    arg_context = self.setArgs(context=context, args=args, content=content, indexContext=indexContext)
                    if not arg_context is None:
                        if self.isFilledArgs(args=args, context=arg_context, indexContext=indexContext):
                            if "request" in arg_context:
                                act_ready_arg = self.makeButtons(
                                    TypeInteraction="navs",
                                    qntElements=len(arg_context["request"]["navs"]),
                                    data={
                                        "navs": arg_context["request"]["navs"]
                                    }
                                )
                                arg_context["text"] = arg_context["request"]["ready"]
                                arg_context = self.buildActions(
                                    output=act_ready_arg,
                                    context=arg_context
                                )
                                return indexContext, arg_context

                            if "sender" in arg_context:
                                bts_sender = self.makeButtons(
                                    TypeInteraction="custom",
                                    data={
                                        "buttons": [
                                            self.posts["buttons"]["sender"]
                                        ]
                                    }
                                )
                                context = self.buildActions(
                                    output=bts_sender,
                                    context=context
                                )

                                context["text"] = arg_context["sender"]["ready"]

                                return indexContext, context
                        return indexContext, arg_context

            try:
                sender_result = self.Sender(context=context, content=content, indexContext=indexContext)
                if type(sender_result) == tuple:
                    return sender_result
                return self.getContext(index=context["positiveContext"])
            except KeyError as e:
                self.debug("error> ", e)
                return self.getContext(index=context["positiveContext"])

        return self.error("Configuration parameters have not been set")
