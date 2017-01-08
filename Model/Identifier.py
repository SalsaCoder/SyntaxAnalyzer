class Identifier(object):
    name = ""
    type = ""
    scope = 0

    def __init__(self, name, type, scope):
        self.name = name
        self.type = type
        self.scope = scope