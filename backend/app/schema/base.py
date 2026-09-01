# API.md 的 JSON 欄位是 camelCase（mangaName、currentVolume...），Python 慣例是 snake_case。
# 這個 base class 讓兩邊各自用自己的慣例：程式裡寫 snake_case，進出 JSON 自動轉 camelCase。

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
