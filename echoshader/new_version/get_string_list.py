import ast


def convert_string_to_list(string):
    try:
        # Attempt to evaluate the string using ast.literal_eval()
        result = ast.literal_eval(string)

        # Check if the result is a list
        if isinstance(result, list):
            return result
        else:
            return False
    except (SyntaxError, ValueError):
        return False
