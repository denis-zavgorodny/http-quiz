import random
from pathlib import Path

from flask import Flask, request, make_response, Request
import jwt
from dotenv import dotenv_values

config = dotenv_values(Path(__file__).parent / ".env")
print(config)

app = Flask(__name__)

SEPARATOR = """
\n\r\n\r
/******************************************************/
/******************************************************/
/******************************************************/
\n\r\n\r
"""


@app.route("/")
def index():
    return """
     /\_/\  
    ( o.o ) 
     > ^ <
     
Hey! Let's play! 

The rules are simple: I want you to send different HTTP requests and solving puzzles.

Please, use /hello endpoint to start.
    """, 200


def check_step(step: str):
    def decorator(f):
        def decorated_function(*args, **kwargs):
            api_key = request.headers.get("x-secret")
            if api_key is None:
                return wrap_error("You need to pass a valid non-empty token as `x-secret` header"), 401

            try:
                data = jwt.decode(jwt=api_key, key=config.get("SECRET"), algorithms='HS256')
                if data.get("step") != step:
                    return wrap_error(f"You need to finish previous step. Please visit `{step}`")

            except Exception as e:
                return wrap_error("Looks like it's wrong token. Please pass valid token in `x-secret` header."), 400

            return f(*args, **kwargs)

        decorated_function.__name__ = f.__name__
        decorated_function.__doc__ = f.__doc__
        return decorated_function

    return decorator


@app.route("/hello")
def hello():
    email = request.args.get("email")

    if email is None:
        return wrap_error("Please, send me your email as `email` GET parameter so we could start"), 401

    signature = jwt.encode({"email": email, "step": "/hello"}, config.get("SECRET"), algorithm='HS256')

    return f"""
    {SEPARATOR}  
    █░░░░░░░░░░░ 1/4
      
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
    {SEPARATOR}
    ██████░░░░░░ 2/4
    
    Good job! You just have learned how to send GET HTTP request with custom headers 🚀.\n\r
    
    Here is your next task: Please inspect this response very carefully and find two cookies 
    in the response with the following names: `first_number` and `second_number`.\n\r
    If you do not see cookies you probably should use `-v` for your cURL call.\n\r
    
    Then please, add those two numbers and send me the result back 
    to the endpoint `/mission2` as a cookie with name `result`.\n\r
    
    ❗❗❗I also expect you to send me this token in HTTP header `x-secret`\n\r
    \n\r
    {signature}
    \n\r
    {SEPARATOR}
    """
    response.status_code = 200

    return response


@app.route("/mission2")
@check_step(step="/mission1")
def mission2():
    result = request.cookies.get("result")

    if result is None:
        return wrap_error("I can not find cookie with name `result` in your request")

    data = jwt.decode(jwt=request.headers.get("x-secret"), key=config.get("SECRET"), algorithms='HS256')

    signature = jwt.encode({
        "email": data.get("email"),
        "step": "/mission2",
    }, config.get("SECRET"), algorithm='HS256')

    if int(data.get("first_number")) + int(data.get("second_number")) == int(result):
        json = """
        {
            "email": "your email here",
            "today": "Monday (put current day of the week here)"    
        }
        """
        return f"""
        {SEPARATOR}
        █████████░░░ 3/4
        
        Cool. The result is {result}. Well done!
        Now I would ask you to send me POST request to endpoint `/mission3` with JSON data. 
        Please send the following JSON data:
        {json}
        \n\rYour secret for this mission is: {signature} \n\r
        Please, use `x-secret` header to add the secret to the request
        {SEPARATOR}
        """, 200

    return wrap_error("Hmmm, looks like you need to think really carefully, it's just a Math.")


@app.route("/mission3", methods=["POST"])
@check_step(step="/mission2")
def mission3():
    data = request.get_json()
    agent = get_user_agent(request)
    if data.get("email") is None:
        return wrap_error("I expect you to send your email"), 400

    if data.get("today") is None:
        return wrap_error("I expect you to send current day of the Week"), 400

    user_data = jwt.decode(jwt=request.headers.get("x-secret"), key=config.get("SECRET"), algorithms='HS256')

    if data.get("email") != user_data.get("email"):
        return wrap_error("Please check email in your JSON"), 400

    signature = jwt.encode({
        "email": data.get("email"),
        "step": "/mission3",
    }, config.get("SECRET"), algorithm='HS256')

    return f"""
    {SEPARATOR}
    ████████████ 4/4
    
    Yahoo! Well done! 
    
    You sent your POST request with JSON data using {agent}. 
    Now you know how to manually send HTTP requests with headers, cookies and 
    parameters. 
    
    Regular Web sites and applications use the same HTTP requests 
    to communicate with web servers.
    
    The quiz is done ✅
      
    \n\rHere is your code: {signature}
    
    ☝️ Please, use this code as an answer and add it to the Moodle.
    {SEPARATOR}
    """, 200


def get_user_agent(request: Request) -> str:
    user_agent = request.headers.get("User-Agent")

    if "curl" in user_agent:
        return "cURL"
    elif "Postman" in user_agent:
        return "Postman"
    else:
        return f"Browser"


def wrap_error(error: str) -> str:
    return f"""
    {SEPARATOR}
    ⚠️ Something went wrong:
    
    {error}
    {SEPARATOR}
    """

if __name__ == '__main__':
    app.run(debug=True, port=config.get("PORT"))
