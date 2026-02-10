from alembic.config import Config
from alembic import command
import os

cfg = Config(os.path.join(os.path.dirname(__file__), '..', 'alembic.ini'))
command.upgrade(cfg, 'head')
print('alembic upgrade head executed')