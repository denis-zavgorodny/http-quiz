import random

from flask import Flask, request, make_response
import jwt
from dotenv import dotenv_values


config = dotenv_values(".env")

app = Flask(__name__)

SEPARATOR = "\n\r/******************************************************/\n\r"

@app.route("/")
def index():
    return """
     /\_/\  
    ( o.o ) 
     > ^ <
     
Hey! Let's play! THe game is about sending different HTTP requests and solving puzzles.\n\t
Please, use /hello endpoint to start.
    """, 200


def check_step(step: str):
    def decorator(f):
        def decorated_function(*args, **kwargs):
            api_key = request.headers.get("x-secret")
            if api_key is None:
                return "You need to pass a valid non-empty token as `x-secret` header \n\r", 401

            try:
                data = jwt.decode(jwt=api_key, key=config.get("SECRET"), algorithms='HS256')
                if data.get("step") != step:
                    return f"You need to finish previous step. Please visit `{step}`\n\r"

            except Exception as e:
                return "\n\rLooks like it's wrong token\n\r", 400

            return f(*args, **kwargs)

        decorated_function.__name__ = f.__name__
        decorated_function.__doc__ = f.__doc__
        return decorated_function
    return decorator


@app.route("/hello")
@check_step(step="/")
def hello():
    email = request.args.get("email")

    if email is None:
        return """\n\r Please, send me your email as `email` GET parameter so we could start\n\r""", 401

    signature = jwt.encode({"email": email, "step": "/hello"}, config.get("SECRET"), algorithm='HS256')

    return f"""
{SEPARATOR}    
 Nice to meet you, {email}!

 You just sent HTTP GET request with parameter using cURL. Well done!

 Here is your personal token:\n\r
 \t{signature}\n\r
 Your next mission is to send me this token in HTTP header `x-secret` back to endpoint `/mission1`.
{SEPARATOR}
    \n\r"""


@app.route("/mission1")
@check_step(step="/hello")
def mission1():
    first_number = random.randint(1, 100)
    second_number = random.randint(1, 100)
    data = jwt.decode(jwt=request.headers.get("x-secret"), key=config.get("SECRET"), algorithms='HS256')
    signature = jwt.encode({
        "email": data.get("email"),
        "step": "/mission1",
        "first_number": first_number,
        "second_number": second_number
    }, config.get("SECRET"), algorithm='HS256')

    response = make_response()
    response.set_cookie("first_number", first_number.__str__())
    response.set_cookie("second_number", second_number.__str__())
    response.data = f"""
    Good job! You just have learned how to send GET HTTP request with custom headers.\n\r
    
    Here is your next task: Please inspect this request very carefully and find two cookies 
    in the response with the following names: `first_number` and `second_number`.\n\r
    If you do not see cookies you probably should use `-v` for your cURL call.\n\r
    
    Then please, add those two numbers and send me the result back to the endpoint `/mission2` as a cookie
    with name `result`.\n\r
    
    I also expect you to send me this token in HTTP header `x-secret`\n\r
    \n\r
    {signature}
    \n\r
    """
    response.status_code = 200

    return response


@app.route("/mission2")
@check_step(step="/mission1")
def mission2():
    result = request.cookies.get("result")

    if result is None:
        return "I can not find cookie with name `result` in your request"

    data = jwt.decode(jwt=request.headers.get("x-secret"), key=config.get("SECRET"), algorithms='HS256')
    if int(data.get("first_number")) + int(data.get("second_number")) == int(result):
        return f"""
        Cool. The result is {result}. Well done! \n\r
        Now I would ask you to send me POST request to endpoint `/mission3`. \n\r  
        
        """, 200

    return "Hmmm, looks like you need to think really carefully, it's just a Math."


@app.route("/mission3")
@check_step(step="/mission2")
def mission3():
    # data = jwt.decode(jwt=request.headers.get("x-secret"), key=config.get("SECRET"), algorithms='HS256')

    return "Yahoo! Well done! You just finished the puzzle"


if __name__ == '__main__':
    app.run(debug=True)
