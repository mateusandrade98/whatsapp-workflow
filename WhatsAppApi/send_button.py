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


def call(chatId: str = "", title: str = "", description: str = "", buttons: str = None, instance: dict = None) -> dict:

    if not instance:
        return return_error(msg="Instance not defined.")

    url = "%s/%s" % (instance["host"], api["wpp_api_send_buttons"])

    headers = {
        "apikey": instance["apikey"],
        "session": instance["id"]
    }

    if chatId == "" or not buttons:
        return return_error(msg="ChatId or Buttons not defined.")

    if description == "" and title == "":
        title = "Escolha uma opção"
        description = "Escolha uma opção"

    rq_session = session()

    bts = {}
    buttons = str(buttons).split(",")
    for i, bt in enumerate(buttons):
        bts.update({
            "button" + str(i+1): bt + "," + str(i) + ",reply"
        })

    data = {
        "chatId": chatId,
        "title": title,
        "description": description
    }

    data.update(bts)

    send = rq_session.post(
        url=url,
        headers=headers,
        data=data
    )

    if send.status_code != 200:
        return return_error(msg=str(send.status_code) + " Error")

    try:
        return return_success(data=loads(send.text))
    except JSONDecodeError as e:
        return return_error(msg=str(e))
