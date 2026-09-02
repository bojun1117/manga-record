from app.model import MangaCategory
from app.schema.base import CamelModel


class MangaSearchResult(CamelModel):
    id: int
    title: str
    category: MangaCategory
