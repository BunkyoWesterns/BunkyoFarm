from passlib.context import CryptContext
from aiocache import cached
import secrets, ast
from db import Env

crypto = CryptContext(schemes=["bcrypt"], deprecated="auto")

@cached()
async def APP_SECRET():
    secret = await Env.objects.get_or_none(key="APP_SECRET")
    secret = secret.value if secret else None
    if secret is None:
        secret = secrets.token_hex(32)
        await Env.objects.update_or_create(key="APP_SECRET", value=secret)
    return secret

def extract_function(fun_name:str, code: bytes) -> ast.FunctionDef|None:
    try:
        node = ast.parse(code)
        function = [n for n in node.body if isinstance(n, ast.FunctionDef) and n.name == fun_name]
        if len(function) > 0:
            return function[0]
    except Exception as e:
        pass
    return None

def has_submit_signature(fun: ast.FunctionDef) -> bool:
    args = [arg.arg for arg in fun.args.args]
    return len(args) > 0 #The first argument is the flag array (array of strings)

def get_additional_args(fun: ast.FunctionDef) -> list:
    args = [arg.arg for arg in fun.args.args]
    return args[1:] #The first argument is the flag array (array of strings)

def extract_submit(code: bytes) -> ast.FunctionDef|None:
    return extract_function("submit", code)

