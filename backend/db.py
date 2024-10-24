import env, secrets
import sqlalchemy.exc
from pydantic import PlainSerializer, BaseModel
from typing import Dict, Any, Annotated, List
from typing import Union, Callable
from uuid import UUID, uuid4
from aiocache import cached
from env import RESET_DB_DANGEROUS
from hashlib import sha256
from models.enums import *
from pydantic import BeforeValidator
from utils import *
import asyncio
from sqlalchemy.pool import NullPool
from fastapi import Depends
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine, AsyncConnection
from sqlmodel import Field, SQLModel as _SQLModel, Relationship
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
from pydantic import model_validator
import sqla

def datetime_now_sql(index:bool = False) -> sqla.Column:
    return sqla.Column(sqla.DateTime(timezone=True), server_default=sqla.func.now(), index=index)

def extract_id_from_dict(x: Any) -> Any:
    if isinstance(x, dict):
        return x["id"]
    if isinstance(x, BaseModel):
        return x.id
    return x

type FkType[T] = Annotated[T|Any, PlainSerializer(lambda x: extract_id_from_dict(x), return_type=T, when_used="always")]

# IDs types

EnvKey = str
ClientID = str
ExploitID = UUID
ServiceID = UUID
TeamID = int
AttackGroupID = int
ExploitSourceID = UUID
AttackExecutionID = int
FlagID = int
SubmitterID = int

DateTime = datetime

class SQLModel(_SQLModel):
    
    #TODO try to fix parsing
    @property
    def model_fields_set(self):
        return self.__fields__

class Env(SQLModel, table=True):
    __tablename__ = "envs"
    
    key:    EnvKey      = Field(primary_key=True)
    value:  str | None  = Field(sqla.String(1024*1024))


class ClientAttackLink(SQLModel, table=True):
    client_id:          ClientID          = Field(default=None, foreign_key="clients.id", primary_key=True)
    attack_group_id:    AttackGroupID     = Field(default=None, foreign_key="attack_groups.id", primary_key=True)


MANUAL_CLIENT_ID = "manual"

def client_id_hashing(client_id: Any) -> ClientID:
    if isinstance(client_id, Union[dict, BaseModel]):
        client_id = extract_id_from_dict(client_id)
        if isinstance(client_id, dict):
            raise ValueError("Invalid client_id")
    try:
        if not isinstance(client_id, UUID):
            client_id = UUID(client_id)
    except Exception:
        return str(client_id)
    return "sha256-"+sha256(str(client_id).lower().encode()).hexdigest().lower()

def check_client_id_hashing(client_id: ClientID) -> bool:
    return client_id.startswith("sha256-")

def verify_and_parse_uuid(value: str) -> UUID:
    try:
        return client_id_hashing(UUID(value))
    except Exception:
        raise ValueError("Invalid UUID")

UnHashedClientID = Annotated[str, BeforeValidator(verify_and_parse_uuid)]

# Auto hashing client_id if ClientID is a UnHashedClientID
class Client(SQLModel, table=True):
    __tablename__ = "clients"
     
    id:                     ClientID                = Field(primary_key=True)
    name:                   str | None
    created_at:             DateTime                = Field(sa_column=datetime_now_sql())
    
    exploits_created:       List["Exploit"]         = Relationship(back_populates="created_by")
    attack_groups:          List["AttackGroup"]     = Relationship(link_model=ClientAttackLink)
    pushed_exploit_sources: List["ExploitSource"]   = Relationship(back_populates="pushed_by")
    attacks_executions:     List["AttackExecution"] = Relationship(back_populates="executed_by")

class Service(SQLModel, table=True):
    __tablename__ = "services"
    
    id:         ServiceID          = Field(primary_key=True, default=uuid4)
    name:       str
    created_at: DateTime           = Field(sa_column=datetime_now_sql())
    
    exploits:   List["Exploit"]    = Relationship(back_populates="service")

class Exploit(SQLModel, table=True):
    __tablename__ = "exploits"
    
    id:                 ExploitID               = Field(primary_key=True)
    name:               str
    language:           Language                = Field(default=Language.other)
    status:             ExploitStatus           = Field(default=ExploitStatus.disabled)
    created_at:         DateTime                = Field(sa_column=datetime_now_sql())
    created_by_id:      ClientID | None         = Field(foreign_key="clients.id")
    created_by:         Client | None           = Relationship(back_populates="exploits_created")
    service_id:         ServiceID | None        = Field(foreign_key="services.id")
    service:            Service | None          = Relationship(back_populates="exploits")
    
    groups:     List["AttackGroup"]             = Relationship(back_populates="exploit", passive_deletes="all")
    sources:    List["ExploitSource"]           = Relationship(back_populates="exploit", passive_deletes="all")
    executions: List["AttackExecution"]         = Relationship(back_populates="exploit")

class Team(SQLModel, table=True):
    __tablename__ = "teams"
    
    id:                 TeamID              = Field(primary_key=True)
    name:               str | None
    short_name:         str | None
    # The host of the team is a string because it can be an IP or a domain, but also in strange CTFs it can be something else ...
    host:               str                 = Field(unique=True)
    created_at:         DateTime            = Field(sa_column=datetime_now_sql())
    
    attacks_executions: List["AttackExecution"] = Relationship(back_populates="target")

class AttackGroup(SQLModel, table=True):
    __tablename__ = "attack_groups"
    
    id:             AttackGroupID       = Field(primary_key=True)
    name:           str
    last_attack:    DateTime | None
    created_at:     DateTime            = Field(sa_column=datetime_now_sql())
    exploit_id:     ExploitID           = Field(foreign_key="exploits.id")
    exploit:        Exploit             = Relationship(back_populates="groups", passive_deletes="all")
    clients:        List["Client"]      = Relationship(link_model=ClientAttackLink, back_populates="attack_groups")
    
    executions:     List["AttackExecution"] = Relationship(back_populates="executed_by_group")

class ExploitSource(SQLModel, table=True):
    __tablename__ = "exploit_sources"
    
    id:             ExploitSourceID             = Field(primary_key=True, default=uuid4)
    hash:           str
    message:        str | None
    pushed_at:      DateTime                    = Field(sa_column=datetime_now_sql())
    os_type:        str | None
    distro:         str | None
    arch:           str | None
    pushed_by_id:   ClientID | None             = Field(foreign_key="clients.id")
    pushed_by:      Client | None               = Relationship(back_populates="pushed_exploit_sources")
    exploit_id:     ExploitID                   = Field(foreign_key="exploits.id")
    exploit:        "Exploit"                   = Relationship(back_populates="sources", passive_deletes="all")
    
    executions: List["AttackExecution"]         = Relationship(back_populates="exploit_source")

class AttackExecution(SQLModel, table=True):
    __tablename__ = "attack_executions"
    
    id:                     AttackExecutionID          = Field(primary_key=True)
    start_time:             DateTime | None
    end_time:               DateTime | None
    status:                 AttackExecutionStatus      = Field(index=True)
    error:                  bytes | None
    received_at:            DateTime                   = Field(sa_column=datetime_now_sql(index=True))
    target_id:              TeamID | None              = Field(foreign_key="teams.id")
    target:                 Team | None                = Relationship(back_populates="attacks_executions")
    exploit_id:             ExploitID | None           = Field(foreign_key="exploits.id")
    exploit:                Exploit | None             = Relationship(back_populates="executions")
    executed_by_id:         ClientID | None            = Field(foreign_key="clients.id")
    executed_by:            Client | None              = Relationship(back_populates="attacks_executions")
    executed_by_group_id:   AttackGroupID | None    = Field(foreign_key="attack_groups.id")
    executed_by_group:      AttackGroup | None         = Relationship(back_populates="executions")
    exploit_source_id:      ExploitSourceID | None     = Field(foreign_key="exploit_sources.id")
    exploit_source:         ExploitSource | None       = Relationship(back_populates="executions")
    
    flags:                  List["Flag"]               = Relationship(back_populates="attack")

class Flag(SQLModel, table=True):
    __tablename__ = "flags"
    
    id:                 FlagID                      = Field(primary_key=True)
    flag:               str                         = Field(unique=True)
    status:             FlagStatus                  = Field(default=FlagStatus.wait, index=True)
    last_submission_at: DateTime | None             = Field(index=True)
    status_text:        str | None
    submit_attempts:    int                         = Field(default=0)
    attack_id:          AttackExecutionID | None    = Field(foreign_key="attack_executions.id")
    attack:             AttackExecution | None      = Relationship(back_populates="flags")

class Submitter(SQLModel, table=True):
    __tablename__ = "submitters"
    
    id:         SubmitterID                 = Field(primary_key=True)
    name:       str
    code:       str                         = Field(sqla.String(1024*1024))
    kargs:      Dict                        = Field(sa_type=JSONB, nullable=False)
    created_at: DateTime                    = Field(sa_column=datetime_now_sql())
    
    class Config:
        arbitrary_types_allowed = True


def dummy_decorator(func):
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper

def get_dbenv_func(var_name: str, default_func:Callable|None = None, value_cached:bool=False):
    final_decorator = cached() if value_cached else dummy_decorator 
    @final_decorator
    async def FUNC() -> str:
        async with dbsession() as session:   
            value = (await session.scalars(sqla.select(Env).where(Env.key == var_name))).one_or_none()
            if value is None:
                value = default_func() if default_func else None
                session.add(Env(key=var_name, value=value))
            return value
    return FUNC

APP_SECRET = get_dbenv_func("APP_SECRET", lambda: secrets.token_hex(32), value_cached=True)
SERVER_ID = get_dbenv_func("SERVER_ID", lambda: str(uuid4()), value_cached=True)
SUBMITTER_ERROR_OUTPUT = get_dbenv_func("SUBMITTER_ERROR_OUTPUT", lambda: "")
SUBMITTER_WARNING_OUTPUT = get_dbenv_func("SUBMITTER_WARNING_OUTPUT", lambda: "")

async def db_init_script() -> None:
    async with dbtransaction() as session:
        manual_client = (await session.scalars(
            sqla.select(Client).where(Client.id == MANUAL_CLIENT_ID)
        )).one_or_none()
        if not manual_client:
            session.add(Client(id=MANUAL_CLIENT_ID, name="Manual client"))

async def init_db():
    await connect_db()
    try:
        while True:
            try:
                async with engine.begin() as conn:
                    if RESET_DB_DANGEROUS:
                        print("!!! Resetting database !!!")
                        await conn.run_sync(SQLModel.metadata.drop_all)
                    await conn.run_sync(SQLModel.metadata.create_all)
                await db_init_script()
                print("Database initialized.")
                break
            except sqlalchemy.exc.OperationalError:
                print("Database not ready, retrying...")
                time.sleep(1)
                continue
    finally:
        await close_db()

global engine, dbconn, dbsession
engine: AsyncEngine|None = None
dbconn: AsyncConnection|None = None
dbsession: async_sessionmaker[AsyncSession]|None = None

@asynccontextmanager
async def dbtransaction():
    async with dbsession() as session:
        async with session.begin():
            yield session
            
async def _dbtransaction():
    async with dbsession() as session:
        async with session.begin():
            yield session


DBSession = Annotated[AsyncSession, Depends(_dbtransaction)]

async def connect_db():
    global engine, dbconn, dbsession
    if engine is None:
        engine = create_async_engine(
            env.POSTGRES_URL,
            poolclass=NullPool,
            echo=env.PRINT_SQL
        )
        dbconn = await engine.connect()
    elif dbconn is None or dbconn.closed:
        dbconn = await engine.connect()
    
    if dbsession is None:
        dbsession = async_sessionmaker(engine, expire_on_commit=False)
    
    return dbconn

async def close_db():
    global engine, dbconn, dbsession
    if dbconn is not None:
        if not dbconn.closed:
            await dbconn.close()
        dbconn = None
    if engine is not None:
        await engine.dispose()
        engine = None
    dbsession = None

if __name__ == "__main__":
    asyncio.run(init_db())
    print("Database initialized.")