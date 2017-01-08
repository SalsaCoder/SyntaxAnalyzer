from treelib import Node, Tree
from Utils import Lexem


class Token(object):
    lexem_class = ""
    lexem = ""
    line_number = 0
    position_number = 0

    def __init__(self, lexem_class, lexem, line_number, position_number):
        self.lexem_class = lexem_class
        self.lexem = lexem
        self.line_number = line_number
        self.position_number = position_number


class SyntaxAnalyzer(object):

    __tokens = []
    __tree = Tree()

    __inc = 0

    def __init__(self, tokens):
        self.__tokens = tokens
        self.__tree.create_node("root", "root")

    def parse_tokens(self):
        while len(self.__tokens) != 0:
            self.__handle_common_block(self.__tokens[:])
        self.__tree.show()

    def __handle_common_block(self, tokens_list):

        tree, new_tokens = self.__handle_expression(tokens_list[:])
        if tree is not None:
            self.__tree.paste(self.__tree.root, tree)
            self.__tokens = new_tokens
            return

        tree, new_tokens = self.__handle_logical_expression(tokens_list[:])
        if tree is not None:
            self.__tree.paste(self.__tree.root, tree)
            self.__tokens = new_tokens
            return

        tree, new_tokens = self.__handle_identifier(tokens_list[:])
        if tree is not None:
            self.__tree.paste(self.__tree.root, tree)
            self.__tokens = new_tokens
            return


    def __handle_expression(self, tokens_list):
        if len(tokens_list) > 0:

            current_token = tokens_list[0]

            if current_token.lexem_class == Lexem.identifier or \
                            current_token.lexem_class == Lexem.string or \
                            current_token.lexem_class == Lexem.number:

                current_tokens = self.__get_tokens_for_line(tokens_list, current_token.line_number)

                tree = Tree()
                tree.create_node(tag=Lexem.expression)

                lexem_class_node = tree.create_node(tag=current_token.lexem_class, parent=tree.root)

                tree.create_node(tag=current_token.lexem, parent=lexem_class_node.identifier)

                if len(current_tokens) > 1:
                    next_token = current_tokens[1]

                    if next_token.lexem_class == Lexem.arithmetic_operation:

                        arithmetic_class_node = tree.create_node(tag=Lexem.arithmetic_operation,
                                                                 parent=tree.root)

                        tree.create_node(tag=next_token.lexem, parent=arithmetic_class_node.identifier)

                        subtree, new_tokens = self.__handle_expression(tokens_list[2:])

                        if subtree is not None:
                            tree.paste(tree.root, subtree)
                            return tree, new_tokens

                    return None, tokens_list

                return tree, tokens_list[1:]
        return None, tokens_list

    def __handle_logical_expression(self, tokens_list):
        if len(tokens_list) >= 3:

            current_line_number = tokens_list[0].line_number

            current_tokens = self.__get_tokens_for_line(tokens_list, current_line_number)

            logical_tokens = list(filter(lambda token: token.lexem_class == Lexem.logical_operation, current_tokens))

            if len(logical_tokens) == 1 and len(current_tokens) >= 3:

                tree = Tree()
                tree.create_node(tag=Lexem.logical_expression)

                logical_index = current_tokens.index(logical_tokens[0])

                expr1 = current_tokens[:logical_index]
                expr2 = current_tokens[logical_index + 1:]

                tree1, _ = self.__handle_expression(expr1)
                tree2, _ = self.__handle_expression(expr2)

                if tree1 is None or tree2 is None:
                    return None, tokens_list

                tree.paste(tree.root, tree1)

                op_node = tree.create_node(tag=Lexem.logical_operation, parent=tree.root)
                tree.create_node(tag=logical_tokens[0].lexem, parent=op_node.identifier)

                tree.paste(tree.root, tree2)

                return tree, tokens_list[len(current_tokens):]

        return None, tokens_list

    def __handle_identifier(self, tokens_list):
        if len(tokens_list) > 0:
            first_token = tokens_list[0]
            if first_token.lexem_class == Lexem.identifier:

                tree = Tree()
                tree.create_node(tag=Lexem.identifier_expression)

                id_node = tree.create_node(tag=Lexem.identifier, parent=tree.root)
                tree.create_node(tag=first_token.lexem, parent=id_node.identifier)

                current_tokens = self.__get_tokens_for_line(tokens_list, first_token.line_number)

                if len(current_tokens) == 1:
                    return tree, tokens_list[1:]

                if len(current_tokens) >= 3:

                    second_token = current_tokens[1]
                    if second_token.lexem_class == Lexem.assign:

                        sub_tokens = current_tokens[2:]

                        expr_tree, _ = self.__handle_expression(sub_tokens)
                        if expr_tree is not None:
                            assign_node = tree.create_node(tag=Lexem.assign, parent=tree.root)
                            tree.create_node(tag="=", parent=assign_node.identifier)
                            tree.paste(tree.root, expr_tree)

                            return tree, tokens_list[len(current_tokens):]

                        expr_tree, _ = self.__handle_logical_expression(sub_tokens)
                        if expr_tree is not None:
                            assign_node = tree.create_node(tag=Lexem.assign, parent=tree.root)
                            tree.create_node(tag="=", parent=assign_node.identifier)
                            tree.paste(tree.root, expr_tree)

                            return tree, tokens_list[len(current_tokens):]

        return None, tokens_list

    def __get_tokens_for_line(self, tokens, line):
        return list(filter(lambda token: token.line_number == line, tokens))

"""
token_1 = Token(lexem_class=Lexem.number, lexem="1", line_number=0, position_number=0)
token_2 = Token(lexem_class=Lexem.arithmetic_operation, lexem="+", line_number=0, position_number=0)
token_3 = Token(lexem_class=Lexem.number, lexem="3", line_number=0, position_number=0)
token_4 = Token(lexem_class=Lexem.number, lexem="3", line_number=1, position_number=0)
token_5 = Token(lexem_class=Lexem.arithmetic_operation, lexem="-", line_number=1, position_number=0)
token_6 = Token(lexem_class=Lexem.number, lexem="4", line_number=1, position_number=0)


token_4 = Token(lexem_class=Lexem.logical_operation, lexem="<", line_number=0, position_number=0)

token_5 = Token(lexem_class=Lexem.number, lexem="3", line_number=0, position_number=0)
token_6 = Token(lexem_class=Lexem.arithmetic_operation, lexem="-", line_number=0, position_number=0)
token_7 = Token(lexem_class=Lexem.number, lexem="4", line_number=0, position_number=0)

tokens = [token_1, token_2, token_3, token_4, token_5, token_6]
"""

token_1 = Token(lexem_class=Lexem.identifier, lexem="i", line_number=0, position_number=0)
token_2 = Token(lexem_class=Lexem.assign, lexem="=", line_number=0, position_number=0)
token_3 = Token(lexem_class=Lexem.number, lexem="3", line_number=0, position_number=0)

token_4 = Token(lexem_class=Lexem.logical_operation, lexem="<", line_number=0, position_number=0)

token_5 = Token(lexem_class=Lexem.number, lexem="3", line_number=0, position_number=0)
token_6 = Token(lexem_class=Lexem.arithmetic_operation, lexem="-", line_number=0, position_number=0)
token_7 = Token(lexem_class=Lexem.number, lexem="4", line_number=0, position_number=0)


tokens = [token_1, token_2, token_3,token_4,token_5]
syntaxAnalyzer = SyntaxAnalyzer(tokens)
syntaxAnalyzer.parse_tokens()


# 1 + 1 + 2
# 2
# 3
# <1, NUM> <+, arithmetic_op>, <1, NUM>, <+, arithmetic_op>, <2, ...>
# <id> | <NUM> <ath_op>
