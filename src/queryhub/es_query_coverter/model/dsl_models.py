from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, model_validator


class DSLBase(BaseModel):
    field: str
    dsl: str

    def to_query(self) -> Dict[str, Any]:
        raise NotImplementedError("Subclasses must implement to_query()")


class TermDSL(DSLBase):
    dsl: str = "is"
    value: Union[str, int, float, bool]

    def to_query(self) -> Dict[str, Any]:
        return {"term": {self.field: self.value}}


class TermsDSL(DSLBase):
    dsl: str = "one_of"
    value: List[Any]

    @model_validator(mode="after")
    def validate_list(self):
        if not isinstance(self.value, list) or len(self.value) == 0:
            raise ValueError("value for 'one_of' must be a non-empty list")
        return self

    def to_query(self) -> Dict[str, Any]:
        return {"terms": {self.field: self.value}}


class MatchDSL(DSLBase):
    dsl: str = "match"
    value: Union[str, int, float, bool]

    def to_query(self) -> Dict[str, Any]:
        return {"match": {self.field: self.value}}


class MatchPhraseDSL(DSLBase):
    dsl: str = "match_phrase"
    value: Union[str, int, float, bool]

    def to_query(self) -> Dict[str, Any]:
        return {"match_phrase": {self.field: self.value}}


class RegexDSL(DSLBase):
    dsl: str = "regex"
    value: str

    def to_query(self) -> Dict[str, Any]:
        return {"regexp": {self.field: self.value}}


class PrefixDSL(DSLBase):
    dsl: str = "prefix"
    value: str

    def to_query(self) -> Dict[str, Any]:
        return {"prefix": {self.field: self.value}}


class WildcardDSL(DSLBase):
    dsl: str = "wildcard"
    value: str

    def to_query(self) -> Dict[str, Any]:
        return {"wildcard": {self.field: self.value}}


class ContainsDSL(DSLBase):
    dsl: str = "contains"
    value: str

    def to_query(self) -> Dict[str, Any]:
        return {"wildcard": {self.field: f"*{self.value}*"}}


class StartsWithDSL(DSLBase):
    dsl: str = "starts_with"
    value: str

    def to_query(self) -> Dict[str, Any]:
        return {"prefix": {self.field: self.value}}


class EndsWithDSL(DSLBase):
    dsl: str = "ends_with"
    value: str

    def to_query(self) -> Dict[str, Any]:
        return {"wildcard": {self.field: f"*{self.value}"}}


class ExistsDSL(DSLBase):
    dsl: str = "exists"
    value: bool = True

    @model_validator(mode="after")
    def validate_value(self):
        if not isinstance(self.value, bool):
            raise ValueError("value for 'exists' must be boolean")
        return self

    def to_query(self) -> Dict[str, Any]:
        if self.value:
            return {"exists": {"field": self.field}}

        return {"bool": {"must_not": [{"exists": {"field": self.field}}]}}


class RangeDSL(DSLBase):
    dsl: str = "range"

    # numeric operators
    gte: Optional[Union[int, float]] = None
    lte: Optional[Union[int, float]] = None
    gt: Optional[Union[int, float]] = None
    lt: Optional[Union[int, float]] = None

    @model_validator(mode="after")
    def validate_range(self):
        """
        Ensure at least one valid bound is provided.
        Acceptable combinations:
        - gte
        - gt
        - lte
        - lt
        - gte + lte
        - gt + lt
        - gte + lt
        - gt + lte
        - (any combination)
        """
        if not any(op is not None for op in (self.gte, self.gt, self.lte, self.lt)):
            raise ValueError("RangeDSL requires at least one of gte, gt, lte, lt")
        return self

    def to_query(self) -> Dict[str, Any]:
        """
        Build the final Elasticsearch range query.
        Only include non‑None operators.
        """
        range_dict = {}

        if self.gte is not None:
            range_dict["gte"] = self.gte
        if self.gt is not None:
            range_dict["gt"] = self.gt
        if self.lte is not None:
            range_dict["lte"] = self.lte
        if self.lt is not None:
            range_dict["lt"] = self.lt

        return {"range": {self.field: range_dict}}
