from enum import Enum


class Actions(str, Enum):
    READ = "Read"
    WRITE = "write"
    DELETE = "DELETE"
