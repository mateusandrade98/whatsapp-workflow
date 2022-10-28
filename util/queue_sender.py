from requests import get as RQGet
from requests import session
from ujson import loads
from ujson import JSONDecodeError
from util import settings

api = settings.Settings().getApi()


def getInstance() -> dict:
    url = api["dynamicWpp"]["url_api_random"]
    headers = api["dynamicWpp"]["headers"]
    get = RQGet(
        url=url,
        headers=headers
    )
    try:
        r = loads(get.text)
        return r
    except JSONDecodeError:
        return {}


def return_error(msg: str = '') -> dict:
    return {
        "success": False,
        "msg": msg
    }


def return_success(data: dict = None) -> dict:
    return {
        "success": True,
        "data": data
    }


def sendMessage(data: dict) -> dict:
    instance = getInstance()

    if "data" in instance:
        instance = instance["data"]
    else:
        return return_error(msg="Instância não encontrada")

    # URL Base da Requisição
    wppUrl = "https://" + instance["host"] + "/api-{session}/{route}"

    # Define headers da request
    headers = {
        "apikey": instance["apikey"],
        "session": instance["id"]
    }

    # Define URL da Request
    route = api["wpp_api_send_text"]

    # Define parâmetros da Request
    if data["clientNumber"] == "":
        return return_error(msg="Telefone inválido")

    requestData = {
        "chatId": data["clientNumber"],
        "text": data["message"]
    }

    if data["image"] != "":
        requestData["url"] = data["image"]
        route = api["wpp_api_send_image"]

    # URL
    url = wppUrl.format(
        session=instance["id"],
        route=route
    )

    rq_session = session()
    send = rq_session.post(
        url=url,
        headers=headers,
        data=requestData
    )

    if send.status_code != 200:
        return return_error(msg=str(send.status_code) + " Error")

    try:
        return return_success(data=loads(send.text))
    except JSONDecodeError as e:
        return return_error(msg=str(e))
