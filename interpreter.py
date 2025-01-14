from lark import Lark, Transformer, UnexpectedCharacters
import sys
import os

with open("lambda_grammar.lark", "r") as lambda_file:
    lambda_grammar = lambda_file.read()

with open("arithmetic_grammar.lark", "r") as arithmetic_file:
    arithmetic_grammar = arithmetic_file.read()

class ArithmeticTransformer(Transformer):
    from operator import add, sub, mul, truediv as div

    def add(self, args):
        left, right = args
        return left + right

    def sub(self, args):
        left, right = args
        return left - right

    def mul(self, args):
        left, right = args
        return left * right

    def div(self, args):
        left, right = args
        return left / right

    def neg(self, args):
        (value,) = args
        return -value

    def number(self, args):
        (value,) = args
        return float(value)

arithmetic_parser = Lark(arithmetic_grammar, parser='lalr', transformer=ArithmeticTransformer())
lambda_parser = Lark(lambda_grammar, parser='lalr')

class LambdaCalculusTransformer(Transformer):
    def lam(self, args):
        name, body = args
        return ('lam', str(name), body)

    def app(self, args):
        return ('app', *args)

    def var(self, args):
        token, = args
        return ('var', str(token))

    def number(self, args):
        return ('number', float(args[0]))

    def cons(self, args):
        head, tail = args
        return ('cons', head, tail)

    def empty(self, args):
        return ('empty',)

    def hd(self, args):
        return ('hd', args[0])

    def tl(self, args):
        return ('tl', args[0])

    def neg(self, args):
        return ('neg', args[0])

    def add(self, args):
        return ('add', args[0], args[1])

    def sub(self, args):
        return ('sub', args[0], args[1])

    def mul(self, args):
        return ('mul', args[0], args[1])

    def div(self, args):
        return ('div', args[0], args[1])

    def eq(self, args):
        return ('eq', args[0], args[1])

    def leq(self, args):
        return ('leq', args[0], args[1])

    def conditional(self, args):
        condition, then_branch, else_branch = args
        return ('conditional', condition, then_branch, else_branch)
    def let(self, args):
        name, value, body = args
        return ('let', str(name), value, body)

    def letrec(self, args):
        name, value, body = args
        return ('letrec', str(name), value, body)
        


def evaluate(tree):
    if tree[0] == 'app':
        e1 = evaluate(tree[1])
        if e1[0] == 'lam':
            name, body = e1[1], e1[2]
            arg = tree[2]
            substituted = substitute_lambda(body, name, arg)
            return evaluate(substituted)
        else:
            return ('app', e1, tree[2])

    elif tree[0] == 'hd':
        lst = evaluate(tree[1])
        if lst[0] == 'cons':
            return lst[1]
        else:
            raise Exception("Cannot take head of a non-list")

    elif tree[0] == 'tl':
        lst = evaluate(tree[1])
        if lst[0] == 'cons':
            return lst[2]
        else:
            raise Exception("Cannot take tail of a non-list")

    elif tree[0] == 'cons':
        head = evaluate(tree[1])
        tail = evaluate(tree[2])
        return ('cons', head, tail)

    elif tree[0] == 'empty':
        return ('empty',)

    elif tree[0] == 'hd':
        lst = evaluate(tree[1])
        print(lst)
        while lst[0] == 'cons':
            return lst[1]
        raise Exception("hd can only be applied to a list (cons).")

    elif tree[0] == 'tl':
        lst = evaluate(tree[1])
        if lst[0] == 'cons':
            return lst[2]
        else:
            raise Exception("Cannot take tail of a non-list")

    elif tree[0] == 'sequence':
        first = evaluate(tree[1])
        second = evaluate(tree[2])
        return ('sequence', first, second)

    elif tree[0] == 'lam':
        return tree

    elif tree[0] == 'letrec':
        letrec_name, letrec_value, letrec_body = tree[1], tree[2], tree[3]

        def fix(f):
            return ('app', 
                    ('lam', 'x', 
                    ('app', ('var', 'x'), ('var', 'x'))),
                    ('lam', 'x', 
                    ('app', f, ('app', ('var', 'x'), ('var', 'x')))))

        fixed_value = fix(('lam', letrec_name, letrec_value))

        substituted_body = substitute_lambda(letrec_body, letrec_name, fixed_value)

        return evaluate(substituted_body)

    elif tree[0] == 'number':
        return tree

    elif tree[0] == 'neg':
        return ('number', -evaluate(tree[1])[1])

    elif tree[0] == 'mul':
        left = evaluate(tree[1])
        right = evaluate(tree[2])
        if left[0] == 'number' and right[0] == 'number':
            return ('number', left[1] * right[1])
        else:
            return ('mul', left, right)

    elif tree[0] == 'div':
        left = evaluate(tree[1])
        right = evaluate(tree[2])
        if left[0] == 'number' and right[0] == 'number':
            return ('number', left[1] / right[1])
        else:
            return ('div', left, right)

    elif tree[0] == 'add':
        left = evaluate(tree[1])
        right = evaluate(tree[2])
        if left[0] == 'number' and right[0] == 'number':
            return ('number', left[1] + right[1])
        else:
            return ('add', left, right)

    elif tree[0] == 'sub':
        left = evaluate(tree[1])
        right = evaluate(tree[2])
        if left[0] == 'number' and right[0] == 'number':
            return ('number', left[1] - right[1])
        else:
            return ('sub', left, right)

    elif tree[0] == 'eq':
        left_expr = tree[1]
        right_expr = tree[2]

        left = evaluate(left_expr)
        right = evaluate(right_expr)

        return ('number', 1.0 if left == right else 0.0)

    elif tree[0] == 'cons':
        head = evaluate(tree[1])
        tail = evaluate(tree[2])
        return ('cons', head, tail)

    elif tree[0] == 'geq':
        left = evaluate(tree[1])
        right = evaluate(tree[2])
        return ('number', 1.0 if left[1] >= right[1] else 0.0)

    elif tree[0] == 'leq':
        left = evaluate(tree[1])
        right = evaluate(tree[2])
        return ('number', 1.0 if left[1] <= right[1] else 0.0)

    elif tree[0] == 'conditional':
        condition = evaluate(tree[1])
        if condition[0] == 'number' and condition[1] != 0.0:
            return evaluate(tree[2])
        else:
            return evaluate(tree[3])

    elif tree[0] == 'let':
        name, value, body = tree[1], evaluate(tree[2]), tree[3]
        return evaluate(substitute_lambda(body, name, value))

    elif tree[0] == 'var':
        return tree

    else:
        raise Exception(f'Unknown tree structure: {tree}')



def linearize(ast):
    if ast[0] == 'cons':
        # Linearize head and tail for lists
        head = linearize(ast[1])
        tail = linearize(ast[2])
        return f"({head} : {tail})"

    elif ast[0] == 'empty':
        # Linearize empty list
        return "#"

    elif ast[0] == 'hd':
        return f"(hd {linearize(ast[1])})"

    elif ast[0] == 'tl':
        return f"(tl {linearize(ast[1])})"

    elif ast[0] == 'number':
        return str(ast[1])

    elif ast[0] == 'var':
        return ast[1]

    elif ast[0] == 'app':
        left = linearize(ast[1])
        right = linearize(ast[2])
        return f"({left} {right})"

    elif ast[0] == 'lam':
        return f"(\\{ast[1]}.{linearize(ast[2])})"

    elif ast[0] == 'add':
        return f"({linearize(ast[1])} + {linearize(ast[2])})"

    elif ast[0] == 'sub':
        return f"({linearize(ast[1])} - {linearize(ast[2])})"

    elif ast[0] == 'mul':
        return f"({linearize(ast[1])} * {linearize(ast[2])})"

    elif ast[0] == 'div':
        return f"({linearize(ast[1])} / {linearize(ast[2])})"

    elif ast[0] == 'eq':
        return f"({linearize(ast[1])} == {linearize(ast[2])})"

    elif ast[0] == 'leq':
        return f"({linearize(ast[1])} <= {linearize(ast[2])})"

    elif ast[0] == 'conditional':
        return f"(if {linearize(ast[1])} then {linearize(ast[2])} else {linearize(ast[3])})"

    else:
        raise Exception(f"Unexpected AST structure in linearize: {ast}")

def substitute_lambda(tree, name, replacement):
    if tree[0] == 'var':
        return replacement if tree[1] == name else tree

    elif tree[0] == 'lam':
        if tree[1] == name:
            return tree
        else:
            fresh_name = name_generator.generate()
            renamed_body = substitute_lambda(tree[2], tree[1], ('var', fresh_name))
            return ('lam', fresh_name, substitute_lambda(renamed_body, name, replacement))

    elif tree[0] == 'app':
        return ('app', substitute_lambda(tree[1], name, replacement), substitute_lambda(tree[2], name, replacement))

    elif tree[0] == 'cons':
        # Substitute in both head and tail of the list
        head = substitute_lambda(tree[1], name, replacement)
        tail = substitute_lambda(tree[2], name, replacement)
        return ('cons', head, tail)

    elif tree[0] == 'empty':
        return tree

    elif tree[0] in ('add', 'sub', 'mul', 'div'):
        return (tree[0], substitute_lambda(tree[1], name, replacement), substitute_lambda(tree[2], name, replacement))

    elif tree[0] == 'neg':
        return ('neg', substitute_lambda(tree[1], name, replacement))

    elif tree[0] in ('eq', 'geq', 'leq'):
        return (tree[0], substitute_lambda(tree[1], name, replacement), substitute_lambda(tree[2], name, replacement))

    elif tree[0] == 'conditional':
        return ('conditional',
                substitute_lambda(tree[1], name, replacement),
                substitute_lambda(tree[2], name, replacement),
                substitute_lambda(tree[3], name, replacement))

    elif tree[0] == 'let':
        let_name, let_value, let_body = tree[1], tree[2], tree[3]
        if let_name == name:
            return ('let', let_name, substitute_lambda(let_value, name, replacement), let_body)
        else:
            return ('let', let_name,
                    substitute_lambda(let_value, name, replacement),
                    substitute_lambda(let_body, name, replacement))

    elif tree[0] == 'letrec':
        letrec_name, letrec_value, letrec_body = tree[1], tree[2], tree[3]

        if letrec_name == name:
            return ('letrec', letrec_name, letrec_value, letrec_body)

        substituted_value = substitute_lambda(letrec_value, name, replacement)
        substituted_body = substitute_lambda(letrec_body, name, replacement)
        return ('letrec', letrec_name, substituted_value, substituted_body)

    elif tree[0] == 'number':
        # Numbers are not affected by substitution
        return tree

    else:
        raise Exception(f"Unknown tree structure in substitute_lambda: {tree}")

# Name generator to avoid variable capture
class NameGenerator:
    def __init__(self):
        self.counter = 0

    def generate(self):
        self.counter += 1
        return f"Var{self.counter}"

name_generator = NameGenerator()

def interpret(source_code):
    try:
        # Split the input on ';;' into individual expressions
        expressions = source_code.split(";;")
        
        # Interpret each expression individually and collect results
        results = [interpret_single(expr.strip()) for expr in expressions]
        
        # Combine results into a sequence-like format
        return " ;; ".join(results)
    except Exception as e:
        print(f"Error in interpretation: {e}")
        return None


def interpret_single(source_code):
    """Interpret a single expression using the existing logic."""
    if 'tl' in source_code:
        try:
            start = source_code.index('tl') + 2
            tl_argument = source_code[start:].strip()

            tl_result = interpret_single(tl_argument)

            if tl_result.startswith('(') and ':' in tl_result:
                tail_part = tl_result.split(':', 1)[1].strip('() ')
                return f"({tail_part})"
            else:
                return f"({source_code})"
        except Exception as e:
            print(f"Error in tl evaluation: {e}")
            return "Error"

    elif 'hd' in source_code:
        try:
            start = source_code.index('hd') + 2
            hd_argument = source_code[start:].strip()

            hd_result = interpret_single(hd_argument)

            if hd_result.startswith('(') and ':' in hd_result:
                first_element = hd_result.split(':')[0].strip('() ')
                return first_element
            else:
                return f"({source_code})"
        except Exception as e:
            print(f"Error in hd evaluation: {e}")
            return "Error"

    elif ':' in source_code and '==' in source_code:
        try:
            left_expr, right_expr = source_code.split('==', 1)
            
            left_result = interpret_single(left_expr.strip())
            right_result = interpret_single(right_expr.strip())

            return '1.0' if left_result == right_result else '0.0'
        except Exception as e:
            print(f"Error in list equality evaluation: {e}")
            return "Error"

    elif '\\' in source_code or 'if' in source_code or 'let' in source_code or 'letrec' or ":" in source_code:
        try:
            cst = lambda_parser.parse(source_code)
            ast = LambdaCalculusTransformer().transform(cst)
            result_ast = evaluate(ast)
            return linearize(result_ast)
        except Exception as e:
            print(f"Error in lambda calculus parsing: {e}")
            return "Error"
    else:
        try:
            result = arithmetic_parser.parse(source_code)
            return str(result)
        except Exception as e:
            print(f"Error in arithmetic parsing: {e}")
            return "Error"
def main():
    if len(sys.argv) != 2:
        sys.exit(1)
    input_arg = sys.argv[1]
    expression = open(input_arg).read() if os.path.isfile(input_arg) else input_arg
    print(f"\033[95m{interpret(expression)}\033[0m")

if __name__ == "__main__":
    main()