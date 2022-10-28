from util import request
from util import databases
from html import unescape
import WhatsAppApi


class BotPress:
    def __init__(self, context: dict = None, config: dict = None):
        self.instance = None
        self.session = None
        self.context = context
        self.config = config
        self.token = None

    def erro(self, msg: str = "") -> dict:
        return {
            "success": False,
            "msg": msg
        }

    def getInstance(self) -> dict:

        self.session = self.context["params_values"]["session"] if "session" in self.context["params_values"] else ""

        systemCache = databases.Cache(Env=self.config)

        botCached = systemCache.get(name='bot-{}'.format(self.session))

        mongodb = systemCache.getMongoDB()

        if not botCached:

            botPersistent = mongodb.findOne(
                filter=dict(
                    session=self.session
                ),
                collection='Bots'
            )

            if not botPersistent:
                return self.erro(msg='bot not exists.')

            botCached = botPersistent

            systemCache.set(name='bot-{}'.format(self.session), values=botPersistent)

        return botCached

    def getToken(self) -> str:
        if "bp_token" in self.context:
            return self.context["bp_token"]
        return ''

    def setToken(self):
        authURL = '/'.join((self.config.get("botpress_url"), "api/v1/auth/login/basic/default"))

        token_response = request.Request(
            dict(
                url=authURL,
                method="POST",
                data=dict(
                    email=self.config.get("botpress_email"),
                    password=self.config.get("botpress_password")
                ),
                headers=dict()
            )
        ).execute()

        if token_response["status"] == 'success':
            self.context["bp_token"] = token_response["payload"]["jwt"]
            return self.context["bp_token"]

        return ''

    def active(self) -> dict:
        source = dict()
        self.instance = self.getInstance()
        if "botpress_active" in self.instance:
            source = dict(
                bot_id=self.instance.get("botpress_id"),
                bot_active=self.instance.get("botpress_active")
            )
        return source

    def getContent(self) -> str:
        return self.context["params_values"]["content"] if "content" in self.context["params_values"] else ""

    def getIndex(self) -> int:
        return self.context["context"] if "context" in self.context["context"] else 0

    def sender(self, _s: dict, Wpp: WhatsAppApi.Wpp = None) -> bool:
        if not "type" in _s:
            return False

        print(_s)

        # html parse
        _s["text"] = str(_s["text"]).replace("&amp;", "&")
        _s["text"] = unescape(_s["text"])

        if _s["type"] == "text":
            print("send_text->", Wpp.sendText(
                text=_s["text"]
            ))
            return True

        if _s["type"] == "single-choice":
            if "choices" in _s:
                _l = len(_s["choices"])
                _q = "," . join(([x['title'] for x in _s["choices"]]))
                if _l <= 3:
                    print("send_buttons->", Wpp.sendButtons(
                        title=_s["text"],
                        description=_s["dropdownPlaceholder"],
                        buttons=_q
                    ))
                    return True
                else:
                    print("send_list->", Wpp.sendList(
                        title=_s["text"],
                        description=_s["dropdownPlaceholder"],
                        buttons=_q
                    ))
                    return True

        return False

    def getContext(self, source: dict = None, idUser: str = '') -> dict:
        converseURL = '/'.join((self.config.get("botpress_url"), "api/v1/bots", source.get("bot_id"), "converse", idUser, "secured"))

        token = self.getToken()

        if token == '':
            token = self.setToken()

        try_RQ = 0
        RQ_OK = 0

        while RQ_OK == 0 and try_RQ <= 2:
            response = request.Request(
                dict(
                    url=converseURL,
                    method="POST",
                    data=dict(
                        type="text",
                        text=self.getContent()
                    ),
                    headers={
                        "Authorization": "Bearer %s" % token
                    }
                )
            ).execute()

            if "statusCode" in response and response["statusCode"] == 401:
                token = self.setToken()
                RQ_OK = 0
                continue

            if "responses" in response and response["responses"]:
                RQ_OK = 1
                responses = response["responses"]
                wpp = WhatsAppApi.Wpp(chatId=idUser, session=self.instance["session"])
                for _ in responses:
                    self.sender(_s=_, Wpp=wpp)

                if len(responses) == 0:
                    self.sender(_s={'type': 'text', 'text': 'Resposta inválida, tente novamente.'}, Wpp=wpp)

                self.context["inputs"] = dict()
                self.context["text"] = "[+] Plugin -> botpress: ok"

            try_RQ += 1

        i_c = self.getIndex()
        return i_c, self.context