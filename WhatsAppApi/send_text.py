from util import settings
from requests import session
from ujson import loads
from ujson import JSONDecodeError

api = settings.Settings().getApi()


def return_error(msg: str = "") -> dict:
    return {
        "success": False,
        "msg": msg
    }


def return_success(data: dict = None) -> dict:
    return {
        "success": True,
        "data": data
    }


def call(chatId: str = "", text: str = "", instance: dict = None) -> dict:

    if not instance:
        return return_error(msg="Instance not defined.")

    url = "%s/%s" % (instance["host"], api["wpp_api_send_text"])

    headers = {
        "apikey": instance["apikey"],
        "session": instance["id"]
    }

    if chatId == "":
        return return_error(msg="ChatId not defined.")

    rq_session = session()
    send = rq_session.post(
        url=url,
        headers=headers,
        data={
            "chatId": chatId,
            "text": text
        }
    )

    if send.status_code != 200:
        return return_error(msg=str(send.status_code) + " Error")

    try:
        return return_success(data=loads(send.text))
    except JSONDecodeError as e:
        return return_error(msg=str(e))
