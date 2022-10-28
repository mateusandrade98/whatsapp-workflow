"""
definicao das variaveis:

{
    "Nome do parametro {name_param}": "valor do parametro {value_param}"
}
"""


def setParamsContext(context=None):
    if "params" in context:
        try:
            build_params = BuildParams(
                params=context["params"],
                values=context["params_values"]
            )
            context["text"] = build_params.setFormat(s=context["text"])
        except KeyError:
            return context
    return context


class BuildParams:
    def __init__(self, params, values):
        self.params = params
        self.values = values

    def setText(self):
        text = ""
        if not self.params is None and not self.values is None:
            for p in self.params:
                text += self.values[p] + " "
        return text.rstrip().lstrip()

    def setData(self, data=None):
        b_data = {}
        for d in data:
            b_data.update({d: self.setFormat(s=data[d])})
        return b_data

    def setFormat(self, s="", showError=0):
        text = s
        if text is None:
            text = ""
        for p in self.params:
            try:
                a = self.values[p]
                b = "{" + p + "}"
                if a is None:
                    continue
                if type(a) != str or type(b) != str:
                    a = str(a)
                    b = str(b)
                text = text.replace(b, a)
            except NameError as e:
                if showError:
                    print("error NameError:", e)
                continue
            except KeyError as e:
                if showError:
                    print("error KeyError:", e)
                continue
            except AttributeError as e:
                if showError:
                    print("error AttributeError:", e)
        return text
