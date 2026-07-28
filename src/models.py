from pydantic import BaseModel


class UserModel(BaseModel):
    telegram_id: str
    user_name: str
    companion_type: str
    companion_name: str
    user_description: str
    ideal_description: str
