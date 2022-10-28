from WhatsAppApi import send_text
from WhatsAppApi import send_button
from WhatsAppApi import send_list
from WhatsAppApi import get_image_profile
from util import settings, databases


def return_error(msg="") -> dict:
    return {
        "success": False,
        "msg": msg
    }


class Wpp:
    def __init__(self, chatId="", session="0"):
        self.chatId = chatId
        self.api = settings.Settings().getApi()
        self.session = session
        self.config = settings.Settings().getConfig()

    def set_chatid(self, chatId: str = ""):
        self.chatId = chatId

    def set_session(self, session: str = ""):
        self.session = session

    def getInstance(self) -> dict:

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
                return return_error(msg='bot not exists.')

            botCached = botPersistent

            systemCache.set(name='bot-{}'.format(self.session), values=botPersistent)

        return dict(
            host=':'.join((self.config.get('direct_bot'), str(botCached.get('port')))),
            id=botCached.get('session'),
            apikey=botCached.get('token_system')
        )

    def sendText(self, text: str = ""):
        return send_text.call(
            chatId=self.chatId,
            text=text,
            instance=self.getInstance()
        )

    def sendList(self, title: str = "", description: str = "", buttons: dict = None):
        return send_list.call(
            chatId=self.chatId,
            title=title,
            description=description,
            buttons=buttons,
            instance=self.getInstance()
        )

    def getProfilePic(self):
        return get_image_profile.call(
            chatId=self.chatId,
            instance=self.getInstance()
        )

    def sendButtons(self, title: str = "", description: str = "", buttons: str = None):
        return send_button.call(
            chatId=self.chatId,
            title=title,
            description=description,
            buttons=buttons,
            instance=self.getInstance()
        )
