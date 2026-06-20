from pydantic import BaseModel, Field


class PaginationRequest(BaseModel):
    size: int | None = Field(default=100)
    page: int | None = Field(default=0)

    @property
    def from_value(self) -> int:
        size = self.size or 100
        page = self.page or 0
        return size * page
