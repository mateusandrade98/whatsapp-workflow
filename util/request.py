from ujson import loads
from ujson import JSONDecodeError
from requests import session


class Request:
    def __init__(self, body_request):
        self.body_request = body_request
        self.sess = None

    def execute(self) -> dict:
        self.sess = session()
        if self.body_request["method"] == "POST":
            try:
                r = self.sess.post(
                    url=self.body_request["url"],
                    json=self.body_request["data"],
                    headers=self.body_request["headers"]
                )
            except Exception:
                return {}
            if r.status_code == 200:
                try:
                    return loads(r.text)
                except JSONDecodeError:
                    return {}
            else:
                return {}
        else:
            try:
                r = self.sess.get(
                    url=self.body_request["url"],
                    params=self.body_request["data"],
                    headers=self.body_request["headers"]
                )
            except Exception:
                return {}
            if r.status_code == 200:
                try:
                    return loads(r.text)
                except JSONDecodeError:
                    return {}
            else:
                return {}
