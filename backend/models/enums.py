from enum import Enum

class ResponseStatus(Enum):
    OK = "ok"
    ERROR = "error"
    INVALID = "invalid"
    
class ExploitStatus(Enum):
    active = 'active'
    disabled = 'disabled'

class FlagStatus(Enum):
    ok = 'ok'
    wait = 'wait'
    timeout = 'timeout'
    invalid = 'invalid'

class AttackExecutionStatus(Enum):
    done = 'done'
    noflags = 'noflags'
    crashed = 'crashed'

class Language(Enum):
    python = "python"
    java = "java"
    javascript = "javascript"
    typescript = "typescript"
    csharp = "c#"
    cpp = "c++"
    php = "php"
    r = "r"
    kotlin = "kotlin"
    go = "go"
    ruby = "ruby"
    rust = "rust"
    lua = "lua"
    dart = "dart"
    perl = "perl"
    haskell = "haskell"
    other = "other"

class MessageStatusLevel(Enum):
    info = "info"
    warning = "warning"
    error = "error"    

class AttackMode(Enum):
    WAIT_FOR_TIME_TICK = "wait-for-time-tick"
    TICK_DELAY = "tick-delay"
    LOOP_DELAY = "loop-delay"

class SetupStatus(Enum):
    SETUP = "setup"
    RUNNING = "running"
