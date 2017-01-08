import json

from NameTable import NameTable
from Model.Identifier import Identifier
from Utils import Constants


class TreeBuilder(object):

    __file_path = ""

    def __init__(self, file_path):
        self.__file_path = file_path

    def build_name_table(self):
        with open(self.__file_path) as data_file:
            raw_identifiers = json.load(data_file)
            identifiers = []
            for raw_identifier in raw_identifiers:
                identifier = Identifier(name=raw_identifier[Constants.Name],
                                        type=raw_identifier[Constants.Type],
                                        scope=raw_identifier[Constants.Scope])
                identifiers.append(identifier)
            name_table = NameTable(identifiers)
            return name_table
