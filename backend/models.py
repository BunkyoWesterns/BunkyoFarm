import ormar, sqlalchemy, databases, env


DATABASE_URL = "postgresql+psycopg2://exploitfarm:exploitfarm@127.0.0.1:5432/exploitfarm" if env.DEBUG else ""

conf = ormar.OrmarConfig(
    database=databases.Database(DATABASE_URL),
    metadata=sqlalchemy.MetaData(),
    engine=sqlalchemy.create_engine(DATABASE_URL),
)

class Envs(ormar.Model):
    ormar_config = conf.copy(tablename="envs")
    
    id: str = ormar.Integer(primary_key=True)
    value: str = ormar.String(max_length=256)