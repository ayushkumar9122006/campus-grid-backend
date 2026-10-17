from campus_grid.schema.base_schema import BaseSchema
from campus_grid.schema.user_schema import UserResponse


class TokenResponse(BaseSchema):
    access_token: str
    token_type: str = "bearer"
    expiration: str
    user: UserResponse
