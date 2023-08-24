def try_parse(obj, possible_int):

    try:
        return obj(possible_int)
    except:
        return possible_int


class ProgressBar:
    def __init__(self, bar) -> None:
        self.Bar = bar

    def Update(self, value):
        if self.Bar is None:
            print(value)
        else:
            self.Bar.title(value)

    def Advance(self):
        if self.Bar is None:
            return
        else:
            self.Bar()
