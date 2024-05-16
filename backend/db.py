import ormar, sqlalchemy, databases, env
from enum import Enum
from pydantic import AwareDatetime
from typing import Dict, Optional, Any
from uuid import UUID, uuid4

dbconf = ormar.OrmarConfig(
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
    invalid = 'invalid'

class AttackExecutionStatus(Enum):
    done = 'done'
    noflags = 'noflags'
    crashed = 'crashed'

class Env(ormar.Model):
    ormar_config = dbconf.copy(tablename="envs")
    
    key: str = ormar.String(max_length=1024, primary_key=True)
    value: str|None = ormar.String(max_length=1024, nullable=True)

class AuthKey(ormar.Model):
    ormar_config = dbconf.copy(tablename="authkeys")
    
    id: int = ormar.Integer(primary_key=True)
    key: str = ormar.String(max_length=1024)

class Client(ormar.Model):
    ormar_config = dbconf.copy(tablename="clients")
    
    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=1024)
    address: str = ormar.String(max_length=1024)

class Service(ormar.Model):
    ormar_config = dbconf.copy(tablename="services")
    
    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=1024)

class Exploit(ormar.Model):
    ormar_config = dbconf.copy(tablename="exploits")
    
    id: UUID = ormar.UUID(primary_key=True, default=uuid4)
    name: str = ormar.String(max_length=1024)
    language: str = ormar.String(max_length=1024, default="unknown")
    hash: str|None = ormar.String(max_length=1024, nullable=True)
    cli: bool = ormar.Boolean()
    status: str = ormar.String(max_length=1024, choices=list(ExploitStatus))
    last_upadte: AwareDatetime = ormar.DateTime(timezone=True)
    created_at: AwareDatetime = ormar.DateTime(timezone=True)
    service: Service = ormar.ForeignKey(Service)
    executor: Optional[Client] = ormar.ForeignKey(Client, related_name='exploit_executing', nullable=True)
    created_by: Optional[Client] = ormar.ForeignKey(Client, related_name='exploit_created', nullable=True)

class Team(ormar.Model):
    ormar_config = dbconf.copy(tablename="teams")
    
    id: int = ormar.Integer(primary_key=True)
    name: str|None = ormar.String(max_length=1024, nullable=True)
    shortName: str|None = ormar.String(max_length=1024, nullable=True)
    address: str = ormar.String(max_length=1024)
    created_at: AwareDatetime = ormar.DateTime(timezone=True)

class AttackExecution(ormar.Model):
    ormar_config = dbconf.copy(tablename="attack_executions")
    
    id: int = ormar.Integer(primary_key=True)
    start_time: AwareDatetime = ormar.DateTime(timezone=True) #Client generated, not affortable, useful for stats only
    end_time: AwareDatetime = ormar.DateTime(timezone=True) #Client generated, not affortable, useful for stats only
    status: str = ormar.String(max_length=1024, choices=list(AttackExecutionStatus))
    error: str|None = ormar.String(max_length=1024, nullable=True)
    output: bytes = ormar.LargeBinary(max_length=1024*1024)
    recieved_at: AwareDatetime = ormar.DateTime(timezone=True) #Server generated
    target: Team = ormar.ForeignKey(Team, related_name='target')
    exploit: Exploit = ormar.ForeignKey(Exploit, related_name='exploit')

class Flag(ormar.Model):
    ormar_config = dbconf.copy(tablename="flags")
    
    id: int = ormar.Integer(primary_key=True)
    flag: str = ormar.String(max_length=1024, unique=True)
    status: str = ormar.String(max_length=1024, choices=list(FlagStatus))
    last_submission_at: AwareDatetime|None = ormar.DateTime(timezone=True, nullable=True)
    status_text: str|None = ormar.String(max_length=1024, nullable=True)
    submit_attempts: int = ormar.Integer(default=0)
    attack: AttackExecution = ormar.ForeignKey(AttackExecution, related_name='attack')

class Submitter(ormar.Model):
    ormar_config = dbconf.copy(tablename="submitters")
    
    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=1024)
    code: bytes = ormar.LargeBinary(max_length=1024*1024)
    kargs: Dict[str, Dict[str, Any]] = ormar.JSON(default={})

def init_db():
    dbconf.metadata.create_all(dbconf.engine)

async def connect_db():
    return await dbconf.database.connect()

async def close_db():
    return await dbconf.database.disconnect()

if __name__ == "__main__":
    init_db()
    print("Database initialized.")

dbtransaction = dbconf.database.transaction