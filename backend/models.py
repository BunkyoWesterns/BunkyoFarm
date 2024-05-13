import ormar, sqlalchemy, databases, env
from enum import Enum
from datetime import datetime
from typing import Union, Dict, Optional

conf = ormar.OrmarConfig(
    database = databases.Database(env.POSTGRES_URL),
    metadata = sqlalchemy.MetaData(),
    engine = sqlalchemy.create_engine(env.POSTGRES_URL),
)

class ExploitStatus(Enum):
    active = 'active'
    noflags = 'noflags'
    disabled = 'disabled'

class FlagStatus(Enum):
    ok = 'ok'
    wait = 'wait'
    timeout = 'timeout'
    wrong = 'wrong'

class AttackExecutionStatus(Enum):
    done = 'done'
    noflags = 'noflags'
    crashed = 'crashed'

class Env(ormar.Model):
    ormar_config = conf.copy(tablename="envs")
    
    id: str = ormar.Integer(primary_key=True)
    value: str = ormar.String(max_length=1024)

class AuthKey(ormar.Model):
    ormar_config = conf.copy(tablename="authkeys")
    
    id: str = ormar.Integer(primary_key=True)
    key: str = ormar.String(max_length=1024)

class Client(ormar.Model):
    ormar_config = conf.copy(tablename="clients")
    
    id: str = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=1024)
    address: str = ormar.String(max_length=1024)

class Service(ormar.Model):
    ormar_config = conf.copy(tablename="services")
    
    id: str = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=1024)
    port: int = ormar.Integer(nullable=True)

class Exploit(ormar.Model):
    ormar_config = conf.copy(tablename="exploits")
    
    id: str = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=1024)
    language: str = ormar.String(max_length=1024, default="unknown")
    hash: str = ormar.String(max_length=1024, nullable=True)
    cli: bool = ormar.Boolean()
    status: str = ormar.String(max_length=1024, choices=list(ExploitStatus))
    last_upadte: datetime = ormar.DateTime()
    created_at: datetime = ormar.DateTime()
    service: Union[Service, Dict] = ormar.ForeignKey(Service, related_name='service')
    executor: Optional[Union[Client, Dict]] = ormar.ForeignKey(Client, related_name='executor')
    created_by: Optional[Union[Client, Dict]] = ormar.ForeignKey(Client, related_name='created_by')

class Team(ormar.Model):
    ormar_config = conf.copy(tablename="teams")
    
    id: str = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=1024, nullable=True)
    shortName: str = ormar.String(max_length=1024, nullable=True)
    address: str = ormar.String(max_length=1024)
    created_at: datetime = ormar.DateTime()

class AttackExecution(ormar.Model):
    ormar_config = conf.copy(tablename="attack_executions")
    
    id: str = ormar.Integer(primary_key=True)
    start_time: datetime = ormar.DateTime()
    end_time: datetime = ormar.DateTime()
    status: str = ormar.String(max_length=1024, choices=list(AttackExecutionStatus))
    error: str = ormar.String(max_length=1024, nullable=True)
    output: str = ormar.String(max_length=1024, nullable=True)
    recieved_at: datetime = ormar.DateTime()
    target: Union[Team, Dict] = ormar.ForeignKey(Team, related_name='target')
    exploit: Union[Exploit, Dict] = ormar.ForeignKey(Exploit, related_name='exploit')

class Flag(ormar.Model):
    ormar_config = conf.copy(tablename="flags")
    
    id: str = ormar.Integer(primary_key=True)
    flag: str = ormar.String(max_length=1024, unique=True)
    status: str = ormar.String(max_length=1024, choices=list(FlagStatus))
    last_submission_at: datetime = ormar.DateTime()
    status_text: str = ormar.String(max_length=1024, nullable=True)
    submit_attempts: int = ormar.Integer(default=0)
    attack: Union[AttackExecution, Dict] = ormar.ForeignKey(AttackExecution, related_name='attack')

class Submitter(ormar.Model):
    ormar_config = conf.copy(tablename="submitters")
    
    id: str = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=1024)
    code: bytes = ormar.LargeBinary(max_length=1024)
    kargs: list = ormar.JSON(default=[])

def init_db():
    conf.metadata.create_all(conf.engine)

if __name__ == "__main__":
    init_db()
    print("Database initialized.")