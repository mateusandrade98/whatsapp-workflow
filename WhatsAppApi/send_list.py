from util import settings
from requests import session
from ujson import loads
from json import JSONDecodeError

api = settings.Settings().getApi()


def return_error(msg=""):
    return {
        "success": False,
        "msg": msg
    }


def return_success(data=None):
    return {
        "success": True,
        "data": data
    }


def call(chatId: str = "", title: str = "", description: str = "", buttons: str = None, instance: dict = None):

    if not instance:
        return return_error(msg="Instance not defined.")

    if "data" in instance:
        instance = instance["data"]

    url = "%s/%s" % (instance["host"], api["wpp_api_send_list"])

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

    opts = {}
    buttons = str(buttons).split(",")

    for i, bt in enumerate(buttons):
        opts.update({
            "option" + str(i+1): "section1" + "," + bt.title().strip() + ",ID" + str(i) + ","
        })

    data = {
        "chatId": chatId,
        "title": title,
        "description": description,
        "footer": "Selecionar uma opção",
        "btnName": "Selecionar uma opção",
        "section1": "Escolha uma opção..."
    }

    data.update(opts)

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
