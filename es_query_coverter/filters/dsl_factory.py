from typing import Any, Dict, Type

from es_query_coverter.model.dsl_models import (
    ContainsDSL,
    DSLBase,
    EndsWithDSL,
    ExistsDSL,
    MatchDSL,
    MatchPhraseDSL,
    PrefixDSL,
    RangeDSL,
    RegexDSL,
    StartsWithDSL,
    TermDSL,
    TermsDSL,
    WildcardDSL,
)


class DSLFactory:

    registry: Dict[str, Type[DSLBase]] = {
        "is": TermDSL,
        "eq": TermDSL,
        "one_of": TermsDSL,
        "in": TermsDSL,
        "match": MatchDSL,
        "match_phrase": MatchPhraseDSL,
        "phrase": MatchPhraseDSL,
        "regex": RegexDSL,
        "prefix": PrefixDSL,
        "wildcard": WildcardDSL,
        "contains": ContainsDSL,
        "starts_with": StartsWithDSL,
        "ends_with": EndsWithDSL,
        "exists": ExistsDSL,
        "range": RangeDSL,
    }

    @staticmethod
    def build_clause(
        dsl: str,
        field: str,
        value: Any = None,
        **extra,
    ) -> Dict[str, Any]:

        # validate DSL
        if dsl not in DSLFactory.registry:
            raise ValueError(f"Unsupported DSL: {dsl}")

        ModelClass = DSLFactory.registry[dsl]

        # base fields
        kwargs = {
            "dsl": dsl,
            "field": field,
        }

        # all current non-range DSLs use the primary value field
        if dsl != "range":
            kwargs["value"] = value

        # range operators (gte, gt, lte, lt)
        if dsl == "range":
            # forward extra fields such as gte/lte/gt/lt
            kwargs.update(
                {
                    "gte": extra.get("gte"),
                    "gt": extra.get("gt"),
                    "lte": extra.get("lte"),
                    "lt": extra.get("lt"),
                }
            )

        else:
            # add any other DSL-specific parameters
            kwargs.update(extra)

        # create DSL object
        model: DSLBase = ModelClass(**kwargs)

        # build ES query
        return model.to_query()
