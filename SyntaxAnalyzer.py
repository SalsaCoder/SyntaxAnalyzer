from treelib import Node, Tree
from Utils import Lexem, Constants

class NameTableRecord(object):
    name = ""
    type = ""
    scope = 0

    def __init__(self, name="", type="", scope=0):
        self.name = name
        self.type = type
        self.scope = scope

class Token(object):
    def __init__(self, lexem_class="", lexem="", line_number=0, position_number=0):
        self.lexem_class = lexem_class
        self.lexem = lexem
        self.line_number = line_number
        self.position_number = position_number


class SemanticAnalyzer(object):
    __name_table = []

    def __init__(self, name_table):
        self.__name_table = name_table

    def __get_type(self, name, scope):
        record = next((x for x in self.__name_table if x.name == name and x.scope == scope), None)
        if record is not None:
            self.__name_table.remove(record)
        else:
            raise ValueError("UNDEFINED IDENTIFIER " + name)
        return record

    def __get_tree_paths(self, tree):
        paths = tree.paths_to_leaves()
        tokens_path = []
        for outer in paths:
            token_path = []
            for path in outer:
                token = tree.get_node(path)
                token_path.append(token)
            tokens_path.append(token_path)

        return tokens_path

    def check_tree(self, tree):
        if tree is not None:
            token_paths = self.__get_tree_paths(tree)

            for token_path in token_paths:
                identifier_token = token_path[-2]
                if identifier_token.tag == Lexem.identifier:
                    expr_node = token_path[-3]

                    if expr_node.tag == Constants.arithmetic_expression or \
                                    expr_node.tag == Constants.iterator_start or \
                                    expr_node.tag == Constants.iterator_end:
                        common_tokens = list(filter(lambda token: token.tag == Constants.common_block, token_path))
                        depth_level = len(common_tokens) - 1
                        name = token_path[-1].tag
                        type = self.__get_type(name, depth_level)

                        if type != Lexem.number:
                            token = token_path[-1].data
                            raise ValueError("SEMANTIC ERROR: EXPECTED TYPE " + \
                                  str(Lexem.number) +\
                                  " AT LINE NUMBER: " \
                                  + str(token.line_number) + \
                                  " POSITION NUMBER " + \
                                  str(token.position_number))

                    if expr_node.tag == Constants.logical_expression:
                        common_tokens = list(filter(lambda token: token.tag == Constants.common_block, token_path))
                        depth_level = len(common_tokens) - 1
                        name = token_path[-1].tag
                        type = self.__get_type(name, depth_level)

                        if type != Lexem.bool:
                            token = token_path[-1].data
                            raise ValueError("SEMANTIC ERROR: EXPECTED TYPE " + \
                                  str(Lexem.number) + \
                                  " AT LINE NUMBER: " \
                                  + str(token.line_number) + \
                                  " POSITION NUMBER " + \
                                  str(token.position_number))


class SyntaxAnalyzer(object):

    def parse_tokens(self, tokens):
        tree, _ = self.__handle_common_block(tokens[:], False, False, False)
        return tree

    def __handle_common_block(self, tokens_list, expect_end_token, expect_elseif_token, expect_else_token):
        common_tree = Tree()
        common_tree.create_node(tag=Constants.common_block)

        receive_end_token = False
        receive_else_token = False
        receive_elseif_token = False

        while len(tokens_list) != 0:
            start_tokens_length = len(tokens_list)


            tree, new_tokens = self.__handle_arithmetic_expression(tokens_list[:])
            if tree is not None:
                common_tree.paste(common_tree.root, tree)
                tokens_list = new_tokens
                continue

            tree, new_tokens = self.__handle_logical_expression(tokens_list[:])
            if tree is not None:
                common_tree.paste(common_tree.root, tree)
                tokens_list = new_tokens
                continue

            tree, new_tokens = self.__handle_identifier(tokens_list[:])
            if tree is not None:
                common_tree.paste(common_tree.root, tree)
                tokens_list = new_tokens
                continue

            tree, new_tokens = self.__handle_while_block(tokens_list[:])
            if tree is not None:
                common_tree.paste(common_tree.root, tree)
                tokens_list = new_tokens
                continue

            tree, new_tokens = self.__handle_for_block(tokens_list[:])
            if tree is not None:
                common_tree.paste(common_tree.root, tree)
                tokens_list = new_tokens
                continue

            tree, new_tokens = self.__handle_if_else_block(tokens_list[:])
            if tree is not None:
                common_tree.paste(common_tree.root, tree)
                tokens_list = new_tokens
                continue


            trees, new_tokens = self.__handle_multiple_assignment(tokens_list[:])
            if trees is not None:
                tokens_list = new_tokens
                for tree in trees:
                    common_tree.paste(common_tree.root, tree)
                    continue

            tree, new_tokens =  self.__handle_end_token(tokens_list[:])
            if tree is not None:
                if expect_end_token:
                    receive_end_token = True
                    tokens_list = new_tokens
                    break
                else:
                    return None, tokens_list

            tree, new_tokens = self.__handle_else_token(tokens_list[:])
            if tree is not None:
                if expect_else_token:
                    receive_else_token = True
                    tokens_list = new_tokens
                    break
                else:
                    return None, tokens_list

            tree, new_tokens = self.__handle_elseif_token(tokens_list[:])
            if tree is not None:
                if expect_elseif_token:
                    receive_elseif_token = True
                    tokens_list = new_tokens
                    break
                else:
                    return None, tokens_list

            if start_tokens_length == len(tokens_list):
                raise ValueError("CAN'T RESOLVE SYMBOL AT LINE NUMBER " + str(tokens_list[0].line_number))

        if expect_end_token and not receive_end_token:
            raise ValueError("Expected END token")


        if not (expect_end_token or receive_end_token) and \
            not (expect_else_token or receive_else_token) and \
            not (expect_elseif_token or receive_elseif_token) and \
            len(tokens_list) == 0:
                return common_tree, tokens_list

        if expect_end_token and receive_end_token and not receive_else_token and not receive_elseif_token:
            return common_tree, tokens_list

        if expect_else_token and receive_else_token and not receive_end_token and not receive_elseif_token:
            return common_tree, tokens_list

        if expect_elseif_token and receive_elseif_token and not receive_end_token and not receive_else_token:
            return common_tree, tokens_list

        raise ValueError("DID RECEIVE SYNTAX ERROR")


    def __handle_arithmetic_expression(self, tokens_list):
        if len(tokens_list) > 0:
            first_token = tokens_list[0]
            if first_token.lexem_class == Lexem.identifier or \
                            first_token.lexem_class == Lexem.l_par or \
                            first_token.lexem_class == Lexem.number or \
                            first_token.lexem_class == Lexem.string:

                current_tokens = self.__get_tokens_for_line(tokens_list, first_token.line_number)

                tree, new_tokens = self.__handle_arithmetic_expression_helper(current_tokens, False)
                if tree is not None:
                    return tree, tokens_list[len(current_tokens):]
        return None, tokens_list

    def __handle_arithmetic_expression_helper(self, tokens_list, expecting_close_par):
        if len(tokens_list) > 0:

            first_token = tokens_list[0]

            tree = None
            if first_token.lexem_class == Lexem.l_par:
                expr_tree, new_tokens = self.__handle_arithmetic_expression_helper(tokens_list[1:], True)
                if expr_tree is not None:
                    if len(new_tokens) == 0:
                        raise ValueError("Expected close PAR")

                    tree = Tree()
                    tree.create_node(tag=Constants.arithmetic_expression)
                    tree.create_node(tag="(", parent=tree.root)
                    tree.paste(tree.root, expr_tree)
                    tree.create_node(tag=")", parent=tree.root)
                    tokens_list = new_tokens

            if first_token.lexem_class == Lexem.identifier or \
                first_token.lexem_class == Lexem.number or \
                    first_token.lexem_class == Lexem.string:

                tree = Tree()
                tree.create_node(tag=Constants.arithmetic_expression)

                lexem_class_node = tree.create_node(tag=first_token.lexem_class, parent=tree.root)

                tree.create_node(tag=first_token.lexem, parent=lexem_class_node.identifier, data=first_token)

                if len(tokens_list) == 1 and not expecting_close_par:
                    return tree, tokens_list[1:]

            tokens_list = tokens_list[1:]

            if len(tokens_list) == 0:
                return tree, []

            if len(tokens_list) > 0:

                if tokens_list[0].lexem_class == Lexem.r_par:
                    if expecting_close_par:
                        return tree, tokens_list
                    else:
                        raise ValueError("Unexpected close brace")

                arithmetic_token = tokens_list[0]

                if arithmetic_token.lexem_class == Lexem.arithmetic_operation:
                    arithmetic_class_node = tree.create_node(tag=Lexem.arithmetic_operation,
                                                            parent=tree.root)

                    tree.create_node(tag=arithmetic_token.lexem, parent=arithmetic_class_node.identifier)

                    subtree, new_tokens = self.__handle_arithmetic_expression_helper(tokens_list[1:], expecting_close_par)

                    if subtree is not None:
                        tree.paste(tree.root, subtree)
                        return tree, new_tokens

        return None, tokens_list

    def __handle_comparasion_expression(self, tokens_list):
        if len(tokens_list) >= 3:

            current_line_number = tokens_list[0].line_number

            current_tokens = self.__get_tokens_for_line(tokens_list, current_line_number)

            logical_tokens = list(filter(lambda token: token.lexem_class == Lexem.comparison_operation, current_tokens))

            if len(logical_tokens) == 1 and len(current_tokens) >= 3:

                tree = Tree()
                tree.create_node(tag=Lexem.comparison_expression)


                logical_index = current_tokens.index(logical_tokens[0])

                expr1 = current_tokens[:logical_index]
                expr2 = current_tokens[logical_index + 1:]

                tree1, _ = self.__handle_arithmetic_expression(expr1)
                tree2, _ = self.__handle_arithmetic_expression(expr2)

                if tree1 is None:
                    raise ValueError("CAN'T RESOLVE SYMBOL AS ARITHMETIC EXPRESSION AT LINE NUMBER: " + \
                          expr1[0].line_number + \
                          " POSITION: " + \
                          expr1[0].line_number)

                if tree2 is None:
                    raise ValueError("CAN'T RESOLVE SYMBOL AS ARITHMETIC EXPRESSION AT LINE NUMBER: " + \
                          str(expr2[0].line_number) + \
                          " POSITION: " + \
                          str(expr2[0].line_number))
                '''
                if tree1 is None or tree2 is None:
                    return None, tokens_list
                '''

                tree.paste(tree.root, tree1)

                op_node = tree.create_node(tag=Lexem.comparison_operation, parent=tree.root)

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

                        expr_tree, _ = self.__handle_arithmetic_expression(sub_tokens)
                        if expr_tree is not None:
                            tree.create_node(tag="=", parent=tree.root)

                            tree.paste(tree.root, expr_tree)

                            return tree, tokens_list[len(current_tokens):]

                        expr_tree, _ = self.__handle_logical_expression(sub_tokens)
                        if expr_tree is not None:
                            tree.create_node(tag="=", parent=tree.root)

                            tree.paste(tree.root, expr_tree)

                            return tree, tokens_list[len(current_tokens):]
                        else:
                            raise ValueError("CAN'T RESOLVE LOGICAL OR ARITHMETICAL EXPRESSION AT LINE NUMBER: " \
                                    + str(sub_tokens[0].line_number) \
                                    + " POSITION: " \
                                    + str(sub_tokens[0].position_number))

        return None, tokens_list

    def __handle_while_block(self, tokens_list):

        if len(tokens_list) >= 3:

            first_token = tokens_list[0]

            current_tokens = self.__get_tokens_for_line(tokens_list, first_token.line_number)

            last_token = current_tokens[-1]

            if len(current_tokens) >= 3 and \
                            first_token.lexem_class == Lexem.while_keyword and \
                            last_token.lexem_class == Lexem.do_keyword:

                comp_tokens = current_tokens[1:-1]
                comp_tree, _ = self.__handle_logical_expression(comp_tokens)
                if comp_tree is not None:
                    del tokens_list[:len(current_tokens)]
                    common_tree, new_tokens = self.__handle_common_block(tokens_list, True, False, False)
                    if common_tree is not None:

                        tree = Tree()
                        tree.create_node(tag=Constants.while_block)

                        tree.create_node(tag="WHILE", parent=tree.root)

                        tree.paste(tree.root, comp_tree)

                        tree.create_node(tag="DO", parent=tree.root)

                        tree.paste(tree.root, common_tree)

                        tree.create_node(tag="END", parent=tree.root)

                        return tree, new_tokens
                else:
                    raise ValueError("EXPECTED LOGICAL EXPRESSION AT LINE: " +\
                          str(comp_tokens[0].line_number) +\
                          " POSITION: " +\
                          str(comp_tokens[0].position_number))

        return None, tokens_list

    def __handle_for_block(self, tokens_list):

        if len(tokens_list) > 0:
            first_token = tokens_list[0]
            current_tokens = self.__get_tokens_for_line(tokens_list, first_token.line_number)
            if len(current_tokens) == 7:
                if first_token.lexem_class == Lexem.for_keyword and \
                    current_tokens[1].lexem_class == Lexem.identifier and \
                    current_tokens[2].lexem_class == Lexem.in_keyword:
                    iter_tokens = current_tokens[3:]
                    iter_tree, _ = self.__handle_iterator_block(iter_tokens)
                    if iter_tree is not None:
                        common_tokens = tokens_list[7:]
                        common_tree, new_tokens = self.__handle_common_block(common_tokens, True, False, False)
                        if common_tree is not None:
                            tree = Tree()
                            tree.create_node(tag=Constants.for_block)

                            tree.create_node(tag="FOR", parent=tree.root)

                            id_tree, _ = self.__handle_identifier([current_tokens[1]])

                            if id_tree is None:
                                raise ValueError("Identifier in FOR expression is missing")

                            tree.paste(tree.root, id_tree)

                            tree.create_node(tag="IN", parent=tree.root)

                            tree.paste(tree.root, iter_tree)

                            tree.paste(tree.root, common_tree)

                            tree.create_node(tag="END", parent=tree.root)

                            return tree, new_tokens
                    else:
                        raise ValueError("EXPECTED VALID ITERATION EXPRESSION AT LINE NUMBER: " +\
                              str(iter_tokens[0].line_number) +\
                              " POSITION: " + str(iter_tokens[0].position_number))

        return None, tokens_list

    def __handle_iterator_block(self, tokens_list):
        if len(tokens_list) > 0:
            first_token = tokens_list[0]
            current_tokens = self.__get_tokens_for_line(tokens_list, first_token.line_number)
            if len(current_tokens) == 4:
                if (first_token.lexem_class == Lexem.identifier or
                    first_token.lexem_class == Lexem.number) and \
                    current_tokens[1].lexem_class == Lexem.dot and \
                    current_tokens[2].lexem_class == Lexem.dot and \
                    (current_tokens[3].lexem_class == Lexem.identifier or
                    current_tokens[3].lexem_class == Lexem.number):

                    tree = Tree()
                    tree.create_node(tag=Constants.iterator_block)

                    start_node = tree.create_node(tag=Constants.iterator_start, parent=tree.root)
                    start_lexem_class_node = tree.create_node(tag=first_token.lexem_class, parent=start_node.identifier)
                    tree.create_node(tag=first_token.lexem, parent=start_lexem_class_node.identifier, data=first_token)

                    tree.create_node(tag=Lexem.dot, parent=tree.root)
                    tree.create_node(tag=Lexem.dot, parent=tree.root)

                    end_node = tree.create_node(tag=Constants.iterator_end, parent=tree.root)
                    end_l_c_node = tree.create_node(tag=current_tokens[3].lexem_class, parent=end_node.identifier)
                    tree.create_node(tag=current_tokens[3].lexem, parent=end_l_c_node.identifier, data=current_tokens[3])

                    return tree, tokens_list[4:]
        return None, tokens_list

    def __handle_if_else_block(self, tokens_list):
        if len(tokens_list) > 0:
            if_token = tokens_list[0]
            current_tokens = self.__get_tokens_for_line(tokens_list[:], if_token.line_number)

            logic_tree, _ = self.__handle_logical_expression(current_tokens[1:])

            if if_token.lexem_class == Lexem.if_keyword and logic_tree is not None:
                common_tokens = tokens_list[len(current_tokens):]

                tree = Tree()
                tree.create_node(tag=Constants.if_block)
                tree.create_node(tag="IF", parent=tree.root)
                tree.paste(tree.root, logic_tree)

                common_tree_elseif_token, new_tokens = self.__handle_common_block(tokens_list=common_tokens[:],
                                                                                  expect_else_token=False,
                                                                                  expect_end_token=False,
                                                                                  expect_elseif_token=True)
                while common_tree_elseif_token is not None:
                    if len(new_tokens) > 0:
                        sub_tokens = self.__get_tokens_for_line(new_tokens[0].line_number)

                        l_tree, after_comp_tokens = self.__handle_logical_expression(sub_tokens[:])
                        if l_tree is not None:
                            tree.create_node(tag="ELSEIF", parent=tree.root)
                            tree.paste(tree.root, l_tree)
                            common_tree_elseif_token, new_tokens = self.__handle_common_block(
                                tokens_list=new_tokens[after_comp_tokens[:]],
                                expect_else_token=False,
                                expect_end_token=False,
                                expect_elseif_token=True)

                            continue

                common_tree_else_token, new_tokens = self.__handle_common_block(common_tokens[:], False, False, True)
                if common_tree_else_token is not None:
                    common_tokens = new_tokens
                    tree.paste(tree.root, common_tree_else_token)
                    tree.create_node(tag="ELSE", parent=tree.root)

                common_tree_end_token, new_tokens = self.__handle_common_block(common_tokens[:], True, False, False)
                if common_tree_end_token is not None:
                    tree.paste(tree.root, common_tree_end_token)
                    tree.create_node(tag="END", parent=tree.root)

                    return tree, new_tokens
            elif if_token.lexem_class == Lexem.if_keyword and logic_tree is None:
                raise ValueError("EXPECTED VALID LOGICAL EXPRESSION AT LINE NUMBER: " + \
                      str(current_tokens[1].line_number) + " POSITION: " + \
                      str(current_tokens[1].position_number))

        return None, tokens

    def __handle_elseif_token(self, tokens_list):
        if len(tokens_list) > 0:
            elseif_token = tokens_list[0]
            current_tokens = self.__get_tokens_for_line(tokens_list[:], elseif_token.line_number)
            if len(current_tokens) > 1 and elseif_token.lexem_class == Lexem.elseif_keyword:
                tree = Tree()
                tree.create_node(tag="ELSEIF")
                return tree, tokens_list[1:]
        return None, tokens_list

    def __handle_else_token(self, tokens_list):
        if len(tokens_list) > 0:
            first_token = tokens_list[0]
            current_tokens = self.__get_tokens_for_line(tokens_list, first_token.line_number)
            if len(current_tokens) == 1 and first_token.lexem_class == Lexem.else_keyword:
                tree = Tree()
                tree.create_node(tag="ELSE")
                return tree, tokens_list[1:]
        return None, tokens_list

    def __handle_end_token(self, tokens_list):
        if len(tokens_list) > 0:
            first_token = tokens_list[0]
            current_tokens = self.__get_tokens_for_line(tokens_list, first_token.line_number)
            if len(current_tokens) == 1 and first_token.lexem_class == Lexem.end_keyword:
                tree = Tree()
                tree.create_node(tag="END")
                return tree, tokens_list[1:]
        return None, tokens_list

    def __get_tokens_for_line(self, tokens, line):
        return list(filter(lambda token: token.line_number == line, tokens))

    def __handle_logical_expression(self, tokens_list):
        if len(tokens_list) > 0:
            first_token = tokens_list[0]

            if first_token.lexem_class == Lexem.identifier or \
                            first_token.lexem_class == Lexem.l_par or \
                            first_token.lexem_class == Lexem.bool or \
                            first_token.lexem_class == Lexem.number:

                current_tokens = self.__get_tokens_for_line(tokens_list, first_token.line_number)

                tree, new_tokens = self.__handle_logical_expression_helper(current_tokens, False)
                if tree is not None:
                    return tree, tokens_list[len(current_tokens):]
        return None, tokens_list

    def __handle_logical_expression_helper(self, tokens_list, expecting_close_par):
        if len(tokens_list) > 0:

            tree = None
            first_token = tokens_list[0]
            if first_token.lexem_class == Lexem.l_par:
                expr_tree, new_tokens = self.__handle_logical_expression_helper(tokens_list[1:], True)
                if expr_tree is not None:
                    if len(new_tokens) == 0:
                        raise ValueError("Expected close PAR")

                    tree = Tree()
                    tree.create_node(tag=Constants.logical_expression)
                    tree.create_node(tag="(", parent=tree.root)
                    tree.paste(tree.root, expr_tree)
                    tree.create_node(tag=")", parent=tree.root)
                    tokens_list = new_tokens[1:]

            else:

                stop_token = next((x for x in tokens_list
                                   if x.lexem_class == Lexem.logical_operation or x.lexem_class == Lexem.r_par), None)

                stop_index = len(tokens_list)
                if stop_token is not None:
                    stop_index = tokens_list.index(stop_token)

                if stop_index > 0:
                    subtokens = tokens_list[:stop_index]
                    if len(subtokens) == 1:
                        token = subtokens[0]
                        if token.lexem_class == Lexem.identifier or token.lexem_class == Lexem.bool:
                            tree = Tree()
                            tree.create_node(tag=Constants.logical_expression)

                            lexem_class_node = tree.create_node(tag=token.lexem_class, parent=tree.root)
                            tree.create_node(tag=token.lexem, parent=lexem_class_node.identifier, data=token)

                    else:
                        comp_tree, _ = self.__handle_comparasion_expression(subtokens)
                        if comp_tree is not None:

                            tree = Tree()
                            tree.create_node(tag=Constants.logical_expression)
                            tree.paste(tree.root, comp_tree)

                tokens_list = tokens_list[len(subtokens):]

            if len(tokens_list) == 0:
                return tree, []

            if len(tokens_list) > 0:

                if tokens_list[0].lexem_class == Lexem.r_par:
                    if expecting_close_par:
                        return tree, tokens_list
                    else:
                        raise ValueError("Unexpected close brace")

                logical_token = tokens_list[0]

                if logical_token.lexem_class == Lexem.logical_operation:
                    op_class_node = tree.create_node(tag=Lexem.logical_operation,
                                                            parent=tree.root)

                    tree.create_node(tag=logical_token.lexem, parent=op_class_node.identifier)

                    subtree, new_tokens = self.__handle_logical_expression_helper(tokens_list[1:], expecting_close_par)

                    if subtree is not None:
                        tree.paste(tree.root, subtree)
                        return tree, new_tokens


        return None, tokens_list

    def __handle_multiple_assignment(self, tokens_list):
        if len(tokens_list) > 0:
            current_tokens = self.__get_tokens_for_line(tokens_list, tokens_list[0].line_number)

            assign_token = next((x for x in current_tokens
                                 if x.lexem_class == Lexem.assign), None)

            if assign_token is not None:
                index = current_tokens.index(assign_token)

                identifier_subtokens = current_tokens[:index]
                value_tokens = current_tokens[index+1:]

                valid_id = False
                id_tokens = []
                for i in range(len(identifier_subtokens)):
                    if i % 2 == 1:
                        valid_id = identifier_subtokens[i].lexem_class == Lexem.comma
                    else:
                        valid_id = identifier_subtokens[i].lexem_class == Lexem.identifier
                        if valid_id:
                            id_tokens.append(identifier_subtokens[i])

                expr_tokens = []
                expr_subtokens = []
                for i in range(len(value_tokens)):
                    if value_tokens[i].lexem_class == Lexem.comma:
                        expr_tokens.append(expr_subtokens)
                        expr_subtokens = []
                        continue
                    else:
                        expr_subtokens.append(value_tokens[i])
                expr_tokens.append(expr_subtokens)

                if len(expr_tokens) == len(id_tokens) and valid_id:
                    trees = []
                    for i in range(len(expr_tokens)):
                        line_number = id_tokens[0].line_number
                        single_assign_tokens = [id_tokens[i]] + \
                                               [Token(lexem_class=Lexem.assign, lexem="=", line_number=line_number, position_number=0)] + \
                                                expr_tokens[i]

                        tree, _ = self.__handle_identifier(single_assign_tokens)
                        if tree is not None:
                            trees.append(tree)
                            continue
                        return None, tokens_list

                    return trees, tokens_list[len(current_tokens):]

        return None, tokens_list


"""
token_1 = Token(lexem_class=Lexem.number, lexem="1", line_number=0, position_number=0)
token_2 = Token(lexem_class=Lexem.arithmetic_operation, lexem="+", line_number=0, position_number=0)
token_3 = Token(lexem_class=Lexem.number, lexem="3", line_number=0, position_number=0)
token_4 = Token(lexem_class=Lexem.number, lexem="3", line_number=1, position_number=0)
token_5 = Token(lexem_class=Lexem.arithmetic_operation, lexem="-", line_number=1, position_number=0)
token_6 = Token(lexem_class=Lexem.number, lexem="4", line_number=1, position_number=0)


token_4 = Token(lexem_class=Lexem.comparison_operation, lexem="<", line_number=0, position_number=0)

token_5 = Token(lexem_class=Lexem.number, lexem="3", line_number=0, position_number=0)
token_6 = Token(lexem_class=Lexem.arithmetic_operation, lexem="-", line_number=0, position_number=0)
token_7 = Token(lexem_class=Lexem.number, lexem="4", line_number=0, position_number=0)

tokens = [token_1, token_2, token_3, token_4, token_5, token_6]
"""
"""
token_1 = Token(lexem_class=Lexem.for_keyword, lexem="for", line_number=0, position_number=0)

token_2 = Token(lexem_class=Lexem.identifier, lexem="i", line_number=0, position_number=0)
token_3 = Token(lexem_class=Lexem.in_keyword, lexem="in", line_number=0, position_number=0)

token_4 = Token(lexem_class=Lexem.number, lexem="3", line_number=0, position_number=0)
token_5 = Token(lexem_class=Lexem.dot, lexem=".", line_number=0, position_number=0)
token_6 = Token(lexem_class=Lexem.dot, lexem=".", line_number=0, position_number=0)
token_7 = Token(lexem_class=Lexem.identifier, lexem="max", line_number=0, position_number=0)


token_8 = Token(lexem_class=Lexem.number, lexem="1", line_number=1, position_number=0)
token_9 = Token(lexem_class=Lexem.arithmetic_operation, lexem="+", line_number=1, position_number=0)
token_10 = Token(lexem_class=Lexem.number, lexem="3", line_number=1, position_number=0)

token_11 = Token(lexem_class=Lexem.number, lexem="1", line_number=2, position_number=0)
token_12 = Token(lexem_class=Lexem.arithmetic_operation, lexem="+", line_number=2, position_number=0)
token_13 = Token(lexem_class=Lexem.number, lexem="3", line_number=2, position_number=0)

token_14 = Token(lexem_class=Lexem.end_keyword, lexem="end", line_number=3, position_number=0)

tokens = [token_1, token_2, token_3,token_4,token_5, token_6, token_7, token_8, token_9, token_10, token_11, token_12, token_13, token_14]
"""

token_1 = Token(lexem_class=Lexem.if_keyword, lexem="IF", line_number=0, position_number=0)

token_2 = Token(lexem_class=Lexem.number, lexem="4", line_number=0, position_number=0)
token_3 = Token(lexem_class=Lexem.comparison_operation, lexem="<=", line_number=0, position_number=0)
token_4 = Token(lexem_class=Lexem.number, lexem="3", line_number=0, position_number=0)

token_5 = Token(lexem_class=Lexem.number, lexem="1", line_number=2, position_number=0)
token_6 = Token(lexem_class=Lexem.arithmetic_operation, lexem="+", line_number=2, position_number=0)
token_7 = Token(lexem_class=Lexem.number, lexem="3", line_number=2, position_number=0)

token_8 = Token(lexem_class=Lexem.identifier, lexem="elses", line_number=3, position_number=0)
token_9 = Token(lexem_class=Lexem.comma, lexem=",", line_number=3, position_number=0)
token_10 = Token(lexem_class=Lexem.identifier, lexem="q", line_number=3, position_number=0)

token_11 = Token(lexem_class=Lexem.assign, lexem="=", line_number=3, position_number=0)

token_12 = Token(lexem_class=Lexem.string, lexem="4", line_number=3, position_number=0)
token_13 = Token(lexem_class=Lexem.comma, lexem=",", line_number=3, position_number=0)
token_14 = Token(lexem_class=Lexem.string, lexem="q value", line_number=3, position_number=0)

'''
token_15 = Token(lexem_class=Lexem.identifier, lexem="i", line_number=4, position_number=0)
token_16 = Token(lexem_class=Lexem.assign, lexem="=", line_number=4, position_number=0)
token_17 = Token(lexem_class=Lexem.identifier, lexem="elses", line_number=4, position_number=0)
token_18 = Token(lexem_class=Lexem.arithmetic_operation, lexem="+", line_number=4, position_number=0)
token_19 = Token(lexem_class=Lexem.identifier, lexem="i", line_number=4, position_number=0)
'''

token_20 = Token(lexem_class=Lexem.identifier, lexem="elses", line_number=5, position_number=0)
token_21 = Token(lexem_class=Lexem.assign, lexem="=", line_number=5, position_number=0)
token_22 = Token(lexem_class=Lexem.identifier, lexem="elses", line_number=5, position_number=0)
token_23 = Token(lexem_class=Lexem.arithmetic_operation, lexem="*", line_number=5, position_number=0)
token_24 = Token(lexem_class=Lexem.identifier, lexem="q", line_number=5, position_number=0)


token_25 = Token(lexem_class=Lexem.while_keyword, lexem="WHILE", line_number=6, position_number=0)
token_26 = Token(lexem_class=Lexem.number, lexem="4", line_number=6, position_number=0)
token_27 = Token(lexem_class=Lexem.comparison_operation, lexem="<=", line_number=6, position_number=0)
token_28 = Token(lexem_class=Lexem.number, lexem="3", line_number=6, position_number=0)
token_29 = Token(lexem_class=Lexem.do_keyword, lexem="DO", line_number=6, position_number=0)

token_30 = Token(lexem_class=Lexem.while_keyword, lexem="WHILE", line_number=7, position_number=0)
token_31 = Token(lexem_class=Lexem.number, lexem="4", line_number=7, position_number=0)
token_32 = Token(lexem_class=Lexem.comparison_operation, lexem="<=", line_number=7, position_number=0)
token_33 = Token(lexem_class=Lexem.number, lexem="3", line_number=7, position_number=0)
token_34 = Token(lexem_class=Lexem.do_keyword, lexem="DO", line_number=7, position_number=0)

token_35 = Token(lexem_class=Lexem.for_keyword, lexem="FOR", line_number=8, position_number=0)
token_36 = Token(lexem_class=Lexem.identifier, lexem="i", line_number=8, position_number=0)
token_37 = Token(lexem_class=Lexem.in_keyword, lexem="in", line_number=8, position_number=0)
token_38 = Token(lexem_class=Lexem.number, lexem="3", line_number=8, position_number=0)
token_39 = Token(lexem_class=Lexem.dot, lexem=".", line_number=8, position_number=0)
token_40 = Token(lexem_class=Lexem.dot, lexem=".", line_number=8, position_number=0)
token_41 = Token(lexem_class=Lexem.identifier, lexem="max", line_number=8, position_number=0)

token_42 = Token(lexem_class=Lexem.if_keyword, lexem="IF", line_number=9, position_number=0)

token_43 = Token(lexem_class=Lexem.l_par, lexem="(", line_number=9, position_number=0)

token_44 = Token(lexem_class=Lexem.l_par, lexem="(", line_number=9, position_number=0)
token_45 = Token(lexem_class=Lexem.identifier, lexem="i", line_number=9, position_number=0)
token_46 = Token(lexem_class=Lexem.comparison_operation, lexem="<", line_number=9, position_number=0)
token_47 = Token(lexem_class=Lexem.identifier, lexem="j", line_number=9, position_number=0)
token_48 = Token(lexem_class=Lexem.r_par, lexem=")", line_number=9, position_number=0)

token_49 = Token(lexem_class=Lexem.logical_operation, lexem="||", line_number=9, position_number=0)

token_50 = Token(lexem_class=Lexem.l_par, lexem="(", line_number=9, position_number=0)
token_51 = Token(lexem_class=Lexem.identifier, lexem="j", line_number=9, position_number=0)
token_52 = Token(lexem_class=Lexem.comparison_operation, lexem="!=", line_number=9, position_number=0)
token_53 = Token(lexem_class=Lexem.identifier, lexem="i", line_number=9, position_number=0)
token_54 = Token(lexem_class=Lexem.r_par, lexem=")", line_number=9, position_number=0)

token_55 = Token(lexem_class=Lexem.logical_operation, lexem="&&", line_number=9, position_number=0)

token_56 = Token(lexem_class=Lexem.l_par, lexem="(", line_number=9, position_number=0)
token_57 = Token(lexem_class=Lexem.identifier, lexem="j", line_number=9, position_number=0)
token_58 = Token(lexem_class=Lexem.comparison_operation, lexem=">", line_number=9, position_number=0)
token_59 = Token(lexem_class=Lexem.identifier, lexem="i", line_number=9, position_number=0)
token_60 = Token(lexem_class=Lexem.r_par, lexem=")", line_number=9, position_number=0)

token_61 = Token(lexem_class=Lexem.r_par, lexem=")", line_number=9, position_number=0)

token_62 = Token(lexem_class=Lexem.identifier, lexem="j", line_number=10, position_number=0)

token_63 = Token(lexem_class=Lexem.end_keyword, lexem="END", line_number=11, position_number=0)
token_64 = Token(lexem_class=Lexem.end_keyword, lexem="END", line_number=12, position_number=0)
token_65 = Token(lexem_class=Lexem.end_keyword, lexem="END", line_number=13, position_number=0)
token_66 = Token(lexem_class=Lexem.end_keyword, lexem="END", line_number=14, position_number=0)
token_67 = Token(lexem_class=Lexem.end_keyword, lexem="END", line_number=15, position_number=0)










'''
token_9 = Token(lexem_class=Lexem.identifier, lexem="i", line_number=4, position_number=0)
token_10 = Token(lexem_class=Lexem.assign, lexem="=", line_number=4, position_number=0)


token_11 = Token(lexem_class=Lexem.number, lexem="5", line_number=4, position_number=0)
token_12 = Token(lexem_class=Lexem.arithmetic_operation, lexem="*", line_number=4, position_number=0)
token_13 = Token(lexem_class=Lexem.number, lexem="2", line_number=4, position_number=0)


tokens = [token_1, token_2, token_3,token_4,token_5, token_6, token_7, token_8, token_9, token_10, token_11, token_12, token_13, token_14, token_15, token_16, token_18, token_19, token_20, token_21, token_22, token_23, token_24, token_25]

'''

tokens = [token_1, token_2, token_3, token_4, token_5, token_6, token_7, token_8, token_9, token_10, token_11, token_12, token_13, token_14, token_20, token_21, token_22, token_23, token_24, token_25, token_26, token_27, token_28, token_29, token_30, token_31, token_32, token_33, token_34, token_35, token_36, token_37, token_38, token_39, token_40, token_41, token_42, token_43, token_44, token_45, token_46, token_47, token_48, token_49, token_50, token_51, token_52, token_53, token_54, token_55, token_56, token_57, token_58, token_59, token_60, token_61, token_63, token_64, token_65, token_66, token_67]

syntaxAnalyzer = SyntaxAnalyzer()
tree = syntaxAnalyzer.parse_tokens(tokens)


record_1 = NameTableRecord(name="elses", type=Lexem.string, scope=1)
record_2 = NameTableRecord(name="q", type=Lexem.string, scope=1)

semanticAnalyzer = SemanticAnalyzer([record_1, record_2])
semanticAnalyzer.check_tree(tree)

tree.show()