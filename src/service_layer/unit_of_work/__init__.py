from typing import Callable

from sqlalchemy.orm import Session

type SessionFactory = Callable[[], Session]
