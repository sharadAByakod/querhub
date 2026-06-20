from enum import Enum


class Actions(str, Enum):
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
