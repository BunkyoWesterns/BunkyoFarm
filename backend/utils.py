from passlib.context import CryptContext
from aiocache import cached
import secrets, ast
from db import Env
from typing import Tuple, List, Any

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

def _extract_value_or_none(value: Any) -> Any:
    try:
       return value.value
    except:
        return None

def extract_function_info(fun: ast.FunctionDef) -> Tuple[List[str], List[str]]:
    args = [arg.arg for arg in fun.args.args]
    default_args = [_extract_value_or_none(ele) for ele in fun.args.defaults]
    return args, default_args

def has_submit_signature(fun: ast.FunctionDef) -> bool:
    args, default_args = extract_function_info(fun)
    if len(args) == 0:
        return False, "The function must have at least one argument"
    if args[0] != "flags":
        return False, "The first argument must be named 'flags'"
    if len(default_args) == len(args):
        return False, "The first argument cannot have a default value"
    return True, "ok"

def _get_if_allowed_type_else_none(value: Any) -> Any:
    if isinstance(value, (int, str, bool, float, bytes, type(None))):
        return value
    return None
    

def get_additional_args(fun: ast.FunctionDef) -> list:
    args, default_args = extract_function_info(fun)
    args = args[1:]
    none_padding = len(args) - len(default_args)
    default_args = [None]*none_padding + default_args
    return {k:_get_if_allowed_type_else_none(v) for k,v in zip(args, default_args)}

def extract_submit(code: bytes) -> ast.FunctionDef|None:
    return extract_function("submit", code)

