from functools import wraps
from loguru import logger

from campus_grid.services.base_service import BaseService


def inject(func):
    """Wrapper ensuring service scoped sessions are properly closed post-request."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        for arg in kwargs.values():
            if isinstance(arg, BaseService):
                try:
                    arg.close_scoped_session()
                except Exception as e:
                    logger.error(f"Error closing scoped session: {e}")
        return result

    return wrapper
