import re

class LambdaInterpreter:
    def __init__(self):
        self.env = {}

    def evaluate(self, expr):
        try:
            if expr.startswith("letrec"):
                return self.handle_letrec(expr)
            else:
                raise ValueError(f"Unknown expression format: {expr}")
        except Exception as e:
            return f"Error in lambda calculus parsing: {str(e)}\nNone"

    def handle_letrec(self, expr):
        # Parse the letrec construct
        match = re.match(r"letrec (\w+) = \\(\w+)\. (.+) in (\w+) (\d+)", expr)
        if not match:
            raise ValueError("Invalid letrec syntax")

        func_name, param, body, call_func, arg = match.groups()
        arg = int(arg)

        def recursive_func(n):
            local_env = {func_name: recursive_func, param: n}
            return self.evaluate_expr(body, local_env)

        self.env[func_name] = recursive_func
        return recursive_func(arg)

    def evaluate_expr(self, expr, local_env):
        expr = expr.strip()
        # Handle function application
        if '(' in expr and ')' in expr:
            func_name, arg_expr = re.match(r"(\w+)\((.+)\)", expr).groups()
            if func_name not in local_env:
                raise ValueError(f"Unknown function: {func_name}")
            func = local_env[func_name]
            arg = self.evaluate_expr(arg_expr, local_env)
            return func(arg)
        # Handle conditionals
        elif "if" in expr:
            condition, true_branch, false_branch = re.match(
                r"if (.+) then (.+) else (.+)", expr
            ).groups()
            if self.evaluate_expr(condition, local_env):
                return self.evaluate_expr(true_branch, local_env)
            else:
                return self.evaluate_expr(false_branch, local_env)
        # Handle equality
        elif "==" in expr:
            left, right = map(str.strip, expr.split("=="))
            return self.evaluate_expr(left, local_env) == self.evaluate_expr(right, local_env)
        # Handle addition
        elif "+" in expr:
            left, right = map(str.strip, expr.rsplit("+", 1))
            return self.evaluate_expr(left, local_env) + self.evaluate_expr(right, local_env)
        # Handle multiplication
        elif "*" in expr:
            left, right = map(str.strip, expr.rsplit("*", 1))
            return self.evaluate_expr(left, local_env) * self.evaluate_expr(right, local_env)
        # Handle numbers
        elif expr.isdigit():
            return int(expr)
        # Handle variables
        elif expr in local_env:
            return local_env[expr]
        else:
            raise ValueError(f"Unknown tree structure: {expr}")

# Test cases
interpreter = LambdaInterpreter()

# Example 1
input1 = "letrec f = \\n. if n==0 then 1 else n*f(n-1) in f 4"
print("Input:", input1)
print("Expected: 24.0")
print("Output:", interpreter.evaluate(input1), "\n")

# Example 2
input2 = "letrec f = \\n. if n==0 then 0 else 1 + 2*(n-1) + f(n-1) in f 6"
print("Input:", input2)
print("Expected: 36.0")
print("Output:", interpreter.evaluate(input2))
