class NameTable(object):
    __identifiers = []

    def __init__(self, identifiers):
        self.__identifiers = identifiers

    def add_token(self, identifier):
        self.__identifiers.append(identifier)

    def get_identfier_by_name(self, name):
        return list(filter(lambda x: x.name == name, self.__identifiers))[0]
