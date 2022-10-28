import requests
import json

url = "http://127.0.0.1:8002/hook?token=XKzyrx-MFvvWs-6xP8mn-TYy3Z5"

from_number = int(input("seu numero> "))

if from_number == 0:
    from_number = 17254658634

while True:

    content = input("enviar> ")

    payload = json.dumps({
      "session": "8edd300255c1534d4679844632e87e96",
      "device": "633413431",
      "event": "on-message",
      "type": "text",
      "isMedia": False,
      "pushName": "mateus",
      "myContact": False,
      "id": "3EB01DF9FEBAD09BD49A",
      "from": str(from_number),
      "content": content,
      "isgroup": False,
      "participant": "",
      "timestamp": 1636669709
    })

    headers = {
      'Content-Type': 'application/json'
    }

    try:
        response = requests.request(
            "POST",
            url,
            headers=headers,
            data=payload
        )
    except Exception:
        continue

    try:
        retorno = response.json()
    except json.decoder.JSONDecodeError as e:
        print("error>", e)
        continue

    try:
        print("recebido> ", retorno["text"])
    except KeyError as e:
        print("Error>", e)
    except TypeError as e:
        print("Error>", e)

    try:
        if "inputs" in retorno:
            if "buttons" in retorno["inputs"]:
                for bt in str(retorno["inputs"]["buttons"]).split(","):
                    print("-" + bt)
    except TypeError as e:
        print(retorno)
        print("Error>", e)

    print("\n")
