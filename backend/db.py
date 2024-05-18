import ormar, sqlalchemy, databases, env, secrets
from pydantic import AwareDatetime, IPvAnyAddress
from pydantic import PlainSerializer, WithJsonSchema, BaseModel
from typing import Dict, Any, TypeAlias, Annotated
from uuid import UUID, uuid4
from utils import datetime_now
from aiocache import cached
from env import RESET_DB_DANGEROUS
from hashlib import sha256
from models.enums import *
from typing import TypeVar, Union, Type

T = TypeVar('T')

def extract_id_from_dict(x: Any) -> T:
    if isinstance(x, dict):
        return x["id"]
    if isinstance(x, BaseModel):
        return x.id
    return x

FkType = Annotated[T|Any, PlainSerializer(lambda x: extract_id_from_dict(x), return_type=T, when_used="always")]

dbconf = ormar.OrmarConfig(
    database = databases.Database(env.POSTGRES_URL),
    metadata = sqlalchemy.MetaData(),
    engine = sqlalchemy.create_engine(env.POSTGRES_URL),
)

EnvKey: TypeAlias = str
class Env(ormar.Model):
    ormar_config = dbconf.copy(tablename="envs")
    
    key: EnvKey = ormar.String(max_length=1024, primary_key=True)
    value: str|None = ormar.String(max_length=1024, nullable=True)

AuthKeyID: TypeAlias = int
class AuthKey(ormar.Model):
    ormar_config = dbconf.copy(tablename="authkeys")
    
    id: AuthKeyID = ormar.Integer(primary_key=True)
    key: str = ormar.String(max_length=1024)
    created_at: AwareDatetime = ormar.DateTime(timezone=True, default=datetime_now)

ClientID: TypeAlias = UUID
_GenericClientID: TypeAlias = str

# Auto hashing client_id if GenericClientID is a ClientID

def client_id_hashing(client_id: Any) -> _GenericClientID:
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

GenericClientID: TypeAlias = Annotated[
    ClientID|_GenericClientID|Any,
    PlainSerializer(client_id_hashing, return_type=_GenericClientID, when_used="always"),
    WithJsonSchema({'type': 'string'}, mode='serialization'),
]

class Client(ormar.Model):
    ormar_config = dbconf.copy(tablename="clients")
    
    id: ClientID = ormar.UUID(primary_key=True)
    name: str|None = ormar.String(max_length=1024, nullable=True)
    address: IPvAnyAddress|None = ormar.String(max_length=1024, nullable=True)
    created_at: AwareDatetime = ormar.DateTime(timezone=True, default=datetime_now)

async def find_client_by_hash(hashed_id: GenericClientID) -> Client|None:
    hashed_id = hashed_id.lower()
    try:
        return list(filter(
            lambda x: client_id_hashing(x.id) == hashed_id,
            await Client.objects.all()
        ))[0]
    except IndexError:
        return None

ServiceID: TypeAlias = UUID
class Service(ormar.Model):
    ormar_config = dbconf.copy(tablename="services")
    
    id: ServiceID = ormar.UUID(default=uuid4, primary_key=True)
    name: str = ormar.String(max_length=1024)
    created_at: AwareDatetime = ormar.DateTime(timezone=True, default=datetime_now)

ExploitID: TypeAlias = UUID
class Exploit(ormar.Model):
    ormar_config = dbconf.copy(tablename="exploits")
    
    id: ExploitID = ormar.UUID(primary_key=True)
    name: str = ormar.String(max_length=1024)
    language: str = ormar.String(max_length=1024, choices=list(Language), default=Language.other.value)
    status: str = ormar.String(max_length=1024, choices=list(ExploitStatus), default=ExploitStatus.disabled.value)
    last_upadte: AwareDatetime = ormar.DateTime(timezone=True, default=datetime_now)
    created_at: AwareDatetime = ormar.DateTime(timezone=True, default=datetime_now)
    service: Service = ormar.ForeignKey(Service, related_name='exploits')
    client: Client = ormar.ForeignKey(Client, related_name='exploits')

TeamID: TypeAlias = int
class Team(ormar.Model):
    ormar_config = dbconf.copy(tablename="teams")
    
    id: TeamID = ormar.Integer(primary_key=True)
    name: str|None = ormar.String(max_length=1024, nullable=True)
    short_name: str|None = ormar.String(max_length=1024, nullable=True)
    host: IPvAnyAddress = ormar.String(max_length=1024, unique=True)
    created_at: AwareDatetime = ormar.DateTime(timezone=True, default=datetime_now)

AttackExecutionID: TypeAlias = int
class AttackExecution(ormar.Model):
    ormar_config = dbconf.copy(tablename="attack_executions")
    
    id: AttackExecutionID = ormar.Integer(primary_key=True)
    start_time: AwareDatetime = ormar.DateTime(timezone=True) #Client generated, not affortable, useful for stats only
    end_time: AwareDatetime = ormar.DateTime(timezone=True) #Client generated, not affortable, useful for stats only
    status: str = ormar.String(max_length=1024, choices=list(AttackExecutionStatus))
    error: str|None = ormar.String(max_length=1024, nullable=True)
    output: bytes = ormar.LargeBinary(max_length=1024*1024)
    recieved_at: AwareDatetime = ormar.DateTime(timezone=True, default=datetime_now) #Server generated
    target: Team = ormar.ForeignKey(Team, related_name='attacks_executions')
    exploit: Exploit = ormar.ForeignKey(Exploit, related_name='executions')

FlagID: TypeAlias = int
class Flag(ormar.Model):
    ormar_config = dbconf.copy(tablename="flags")
    
    id: FlagID = ormar.Integer(primary_key=True)
    flag: str = ormar.String(max_length=1024, unique=True)
    status: str = ormar.String(max_length=1024, choices=list(FlagStatus))
    last_submission_at: AwareDatetime|None = ormar.DateTime(timezone=True, nullable=True)
    status_text: str|None = ormar.String(max_length=1024, nullable=True)
    submit_attempts: int = ormar.Integer(default=0)
    attack: AttackExecution = ormar.ForeignKey(AttackExecution, related_name='flags')

SubmitterID: TypeAlias = int
class Submitter(ormar.Model):
    ormar_config = dbconf.copy(tablename="submitters")
    
    id: SubmitterID = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=1024)
    code: bytes = ormar.LargeBinary(max_length=1024*1024)
    kargs: Dict[str, Dict[str, Any]] = ormar.JSON(default={})
    created_at: AwareDatetime = ormar.DateTime(timezone=True, default=datetime_now)

@cached()
async def APP_SECRET():
    secret = await Env.objects.get_or_none(key="APP_SECRET")
    secret = secret.value if secret else None
    if secret is None:
        secret = secrets.token_hex(32)
        await Env.objects.update_or_create(key="APP_SECRET", value=secret)
    return secret

def init_db():
    if RESET_DB_DANGEROUS:
        dbconf.metadata.drop_all(dbconf.engine)
    dbconf.metadata.create_all(dbconf.engine)

async def connect_db():
    return await dbconf.database.connect()

async def close_db():
    return await dbconf.database.disconnect()

transactional = dbconf.database.transaction()

if __name__ == "__main__":
    init_db()
    print("Database initialized.")