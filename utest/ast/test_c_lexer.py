import re
import sys
import unittest

from pytel.ast.c_lexer import CLexer

def token_list(clex):
    return list(iter(clex.token, None))


def token_types(clex):
    return [i.type for i in token_list(clex)]


class TestCLexerNoErrors(unittest.TestCase):
    """ Test lexing of strings that are not supposed to cause
        errors. Therefore, the error_func passed to the lexer
        raises an exception.
    """
    def error_func(self, msg, line, column):
        self.fail(msg)
    
    def type_lookup_func(self, typ):
        if typ.startswith('mytype'):
            return True
        else:
            return False
    
    def setUp(self):
        self.clex = CLexer(self.error_func)
        self.clex.build(optimize=False)
    
    def assertTokensTypes(self, str, types):
        self.clex.input(str)
        self.assertEqual(token_types(self.clex), types)
    
    def test_trivial_tokens(self):
        self.assertTokensTypes('1', ['INT_CONST_DEC'])
        self.assertTokensTypes('-', ['MINUS'])
        #self.assertTokensTypes('...', ['ELLIPSIS'])
        self.assertTokensTypes('++', ['PLUSPLUS'])
        #self.assertTokensTypes('case int', ['CASE', 'INT'])
        self.assertTokensTypes('caseint', ['ID'])
        
    def test_id_typeid(self):
        self.assertTokensTypes('myt', ['ID'])
        self.assertTokensTypes('mytype', ['ID'])
        self.assertTokensTypes('mytype6 var', ['ID', 'ID'])
    
    def test_integer_constants(self):
        self.assertTokensTypes('12', ['INT_CONST_DEC'])
        self.assertTokensTypes('12u', ['INT_CONST_DEC'])
        self.assertTokensTypes('199872Ul', ['INT_CONST_DEC'])
        
        self.assertTokensTypes('077', ['INT_CONST_OCT'])
        self.assertTokensTypes('0123456L', ['INT_CONST_OCT'])
               
        self.assertTokensTypes('0xf7', ['INT_CONST_HEX'])
        self.assertTokensTypes('0x01202AAbbf7Ul', ['INT_CONST_HEX'])
        
        # no 0 before x, so ID catches it
        self.assertTokensTypes('xf7', ['ID'])
        
        # - is MINUS, the rest a constnant
        self.assertTokensTypes('-1', ['MINUS', 'INT_CONST_DEC'])
        
    def test_floating_constants(self):
        self.assertTokensTypes('1.5f', ['FLOAT_CONST'])
        self.assertTokensTypes('01.5', ['FLOAT_CONST'])
        self.assertTokensTypes('.15L', ['FLOAT_CONST'])
        self.assertTokensTypes('0.', ['FLOAT_CONST'])
        
        # but just a period is a period
        #self.assertTokensTypes('.', ['PERIOD'])
        
        self.assertTokensTypes('3.3e-3', ['FLOAT_CONST'])
        self.assertTokensTypes('.7e25L', ['FLOAT_CONST'])
        self.assertTokensTypes('6.e+125f', ['FLOAT_CONST'])
        self.assertTokensTypes('666e666', ['FLOAT_CONST'])
        self.assertTokensTypes('00666e+3', ['FLOAT_CONST'])
        
        # but this is a hex integer + 3
        self.assertTokensTypes('0x0666e+3', ['INT_CONST_HEX', 'PLUS', 'INT_CONST_DEC'])
    
    def test_char_constants(self):
        self.assertTokensTypes(r"""'x'""", ['CHAR_CONST'])
        #self.assertTokensTypes(r"""L'x'""", ['WCHAR_CONST'])
        self.assertTokensTypes(r"""'\t'""", ['CHAR_CONST'])
        self.assertTokensTypes(r"""'\''""", ['CHAR_CONST'])
        self.assertTokensTypes(r"""'\?'""", ['CHAR_CONST'])
        self.assertTokensTypes(r"""'\012'""", ['CHAR_CONST'])
        self.assertTokensTypes(r"""'\x2f'""", ['CHAR_CONST'])
        self.assertTokensTypes(r"""'\x2f12'""", ['CHAR_CONST'])
        #self.assertTokensTypes(r"""L'\xaf'""", ['WCHAR_CONST'])

    def test_string_literal(self):
        self.assertTokensTypes('"a string"', ['STRING_LITERAL'])
        #self.assertTokensTypes('L"ing"', ['WSTRING_LITERAL'])
        self.assertTokensTypes(
            '"i am a string too \t"', 
            ['STRING_LITERAL'])
        self.assertTokensTypes(
            r'''"esc\ape \"\'\? \0234 chars \rule"''', 
            ['STRING_LITERAL'])
        self.assertTokensTypes(
            r'''"hello 'joe' wanna give it a \"go\"?"''',
            ['STRING_LITERAL'])

    def test_mess(self):
        self.assertTokensTypes(
            r'[{}]()',
            ['LBRACKET', 
            'LBRACE', 'RBRACE', 
            'RBRACKET', 
            'LPAREN', 'RPAREN'])

        self.assertTokensTypes(
            r'()|C&~ZJ',
            ['LPAREN', 'RPAREN', 
            'BOR', 
            'ID', 
            'BAND', 
            'BNOT', 'ID',])
        
        self.assertTokensTypes(
            r'+-*/%|||&&&^><>=<====',
            ['PLUS', 'MINUS', 'TIMES', 'DIVIDE', 'MOD', 
            'BOR', 'BOR', 'BOR', 'BAND', 'BAND', 'BAND',
            'BXOR',  
            'GT', 'NE', 'EQUALS', 'LE', 'EQ', 'EQUALS'])
                    
        self.assertTokensTypes(
            r'++--,;:',
            ['PLUSPLUS', 'MINUSMINUS', 
             'COMMA', 'SEMI', 'COLON'])

    def test_exprs(self):
        self.assertTokensTypes(
            'bb-cc',
            ['ID', 'MINUS', 'ID'])

        self.assertTokensTypes(
            'foo & 0xFF',
            ['ID', 'BAND', 'INT_CONST_HEX'])

        self.assertTokensTypes(
            '(2+k) * 62', 
            ['LPAREN', 'INT_CONST_DEC', 'PLUS', 'ID', 
            'RPAREN', 'TIMES', 'INT_CONST_DEC'],)
        
        self.assertTokensTypes(
            'x | y >> z',
            ['ID', 'BOR', 'ID', 'RSHIFT', 'ID'])
        
        self.assertTokensTypes(
            'x <<= z << 5',
            ['ID', 'LSHIFT', 'EQUALS', 'ID', 'LSHIFT', 'INT_CONST_DEC'])
        
        self.assertTokensTypes(
            'x = y > 0 y : -6',
            ['ID', 'EQUALS', 
                'ID', 'GT', 'INT_CONST_OCT', 
                'ID', 
                'COLON', 
                'MINUS', 'INT_CONST_DEC'])
        
        self.assertTokensTypes(
            'a+++b',
            ['ID', 'PLUSPLUS', 'PLUS', 'ID'])

    def test_statements(self):
        self.assertTokensTypes(
            'for (int i = 0; i < n; ++i)endfor',
            ['FOR', 'LPAREN', 
                        'ID', 'ID', 'EQUALS', 'INT_CONST_OCT', 'SEMI', 
                        'ID', 'LT', 'ID', 'SEMI', 
                        'PLUSPLUS', 'ID', 
                    'RPAREN', 'ENDFOR'])
        
        self.assertTokensTypes(
            'self: goto self;',
            ['ID', 'COLON', 'GOTO', 'ID', 'SEMI'])
            
        self.assertTokensTypes(
            """ switch (typ)
                    case TYPE_ID:
                        m = 5;
                        break;
                    default:
                        m = 8;
                endswitch
                """,
            ['SWITCH', 'LPAREN', 'ID', 'RPAREN',  
                    'CASE', 'ID', 'COLON', 
                        'ID', 'EQUALS', 'INT_CONST_DEC', 'SEMI', 
                        'BREAK', 'SEMI', 
                    'DEFAULT', 'COLON', 
                        'ID', 'EQUALS', 'INT_CONST_DEC', 'SEMI', 
                'ENDSWITCH'])
        
        self.assertTokensTypes("""string function test(integer a)
                if (a and b or not c) endif
                    endfunction
                 """, ['STRING', 'FUNCTION', 'ID', 'LPAREN','INTEGER', 'ID', 'RPAREN',
                       'IF', 'LPAREN', 'ID', 'AND', 'ID', 'OR', 'NOT', 'ID', 'RPAREN', 'ENDIF',
                       'ENDFUNCTION'])
        
        
    def test_preprocessor(self):
        self.assertTokensTypes('#abracadabra', ['PPHASH', 'ID'])
        
        str = r"""
        546
        #line 66 "kwas\df.h" 
        id 4
        dsf
        # 9 
        armo
        """
        
        #~ self.clex.filename
        self.clex.input(str)
        self.clex.reset_lineno()
        
        t1 = self.clex.token()
        self.assertEqual(t1.type, 'INT_CONST_DEC')
        self.assertEqual(t1.lineno, 2)
        
        t2 = self.clex.token()
        self.assertEqual(t2.type, 'ID')
        self.assertEqual(t2.value, 'id')
        self.assertEqual(t2.lineno, 66)
        self.assertEqual(self.clex.filename, r'kwas\df.h')
        
        for i in xrange(3):
            t = self.clex.token()
        
        self.assertEqual(t.type, 'ID')
        self.assertEqual(t.value, 'armo')
        self.assertEqual(t.lineno, 9)
        self.assertEqual(self.clex.filename, r'kwas\df.h')
        


# Keeps all the errors the lexer spits in one place, to allow
# easier modification if the error syntax changes.
#
ERR_ILLEGAL_CHAR    = 'Illegal character'
ERR_OCTAL           = 'Invalid octal constant'
ERR_UNMATCHED_QUOTE = 'Unmatched \''
ERR_INVALID_CCONST  = 'Invalid char constant'
ERR_STRING_ESCAPE   = 'String contains invalid escape'

ERR_FILENAME_BEFORE_LINE    = 'filename before line'
ERR_LINENUM_MISSING         = 'line number missing'
ERR_INVALID_LINE_DIRECTIVE  = 'invalid #line directive'


class TestCLexerErrors(unittest.TestCase):
    """ Test lexing of erroneous strings.
        Works by passing an error functions that saves the error
        in an attribute for later perusal.
    """    
    def error_func(self, msg, line, column):
        self.error = msg
        
    def type_lookup_func(self, typ):
        return False
        
    def setUp(self):
        self.clex = CLexer(self.error_func)
        self.clex.build(optimize=False)
        self.error = ""

    def assertLexerError(self, str, error_like):
        # feed the string to the lexer
        self.clex.input(str)
        
        # Pulls all tokens from the string. Errors will
        # be written into self.error by the error_func
        # callback
        #
        token_types(self.clex) 
        
        # compare the error to the expected
        self.failUnless(re.search(error_like, self.error),
            "\nExpected error matching: %s\nGot: %s" % 
                (error_like, self.error))
        
        # clear last error, for the sake of subsequent invocations
        self.error = ""

    def test_trivial_tokens(self):
        self.assertLexerError('@', ERR_ILLEGAL_CHAR)
        self.assertLexerError('$', ERR_ILLEGAL_CHAR)
        self.assertLexerError('`', ERR_ILLEGAL_CHAR)
        self.assertLexerError('\\', ERR_ILLEGAL_CHAR)
    
    def test_integer_constants(self):
        self.assertLexerError('029', ERR_OCTAL)
        self.assertLexerError('012345678', ERR_OCTAL)
        
    def test_char_constants(self):
        self.assertLexerError("'", ERR_UNMATCHED_QUOTE)
        self.assertLexerError("'b\n", ERR_UNMATCHED_QUOTE)
    
        self.assertLexerError("'jx'", ERR_INVALID_CCONST)
        self.assertLexerError("'\*'", ERR_INVALID_CCONST)
        self.assertLexerError("'\9'", ERR_INVALID_CCONST)
        self.assertLexerError("L'\9'", ERR_INVALID_CCONST)
    
    def test_string_literals(self):
        self.assertLexerError('"jx\9"', ERR_STRING_ESCAPE)
        self.assertLexerError('"hekllo\* on ix"', ERR_STRING_ESCAPE)
        self.assertLexerError('L"hekllo\* on ix"', ERR_STRING_ESCAPE)
            
    def test_preprocessor(self):
        self.assertLexerError('#line "ka"', ERR_FILENAME_BEFORE_LINE)
        self.assertLexerError('#line df', ERR_INVALID_LINE_DIRECTIVE)
        self.assertLexerError('#line \n', ERR_LINENUM_MISSING)


if __name__ == '__main__':
    unittest.main()
        

