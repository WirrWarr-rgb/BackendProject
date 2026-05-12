from fastapi import Depends, HTTPException, status
from app.models.user import User, UserRole
from app.api.v1.endpoints.auth import get_current_user


def require_admin(current_user: User = Depends(get_current_user)):
    """
    Dependency: требует роль ADMIN.
    Использование: Depends(require_admin)
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


def require_role(required_roles: list[UserRole]):
    """
    Фабрика dependency: требует одну из указанных ролей.
    Использование: Depends(require_role([UserRole.ADMIN]))
    """
    async def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role not in required_roles:
            roles_str = ", ".join([r.value for r in required_roles])
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required role(s): {roles_str}"
            )
        return current_user
    return role_checker