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
