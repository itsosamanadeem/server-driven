from fastapi import HTTPException, status


class PermissionService:
    @staticmethod
    def _has_super_admin(user) -> bool:
        return any(group.name == "super_admin" for group in user.groups)

    @staticmethod
    def can(user, model_name: str, action: str) -> bool:
        if PermissionService._has_super_admin(user):
            return True

        # direct user permissions
        for perm in getattr(user, "direct_permissions", []):
            if perm.model == model_name and perm.action == action:
                return True

        # group permissions
        for group in user.groups:
            for perm in getattr(group, "permissions", []):
                if perm.model == model_name and perm.action == action:
                    return True

        return False

    @staticmethod
    def ensure(user, model_name: str, action: str) -> None:
        if not PermissionService.can(user, model_name, action):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied for {action} on {model_name}",
            )
