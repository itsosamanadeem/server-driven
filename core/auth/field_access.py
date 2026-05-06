from modules.base.models.rbac import FieldAccess


class FieldAccessService:
    @staticmethod
    def _has_super_admin(user) -> bool:
        return any(group.name == "super_admin" for group in user.groups)

    @staticmethod
    def _resolve_rule(user, db, model_name: str, field_name: str, for_write: bool) -> bool:
        if FieldAccessService._has_super_admin(user):
            return True

        # user-specific rules override group rules
        user_rule = (
            db.query(FieldAccess)
            .filter(
                FieldAccess.model == model_name,
                FieldAccess.field == field_name,
                FieldAccess.user_id == user.id,
            )
            .first()
        )
        if user_rule:
            return user_rule.can_write if for_write else user_rule.can_read

        group_ids = [group.id for group in user.groups]
        if not group_ids:
            return True

        rules = (
            db.query(FieldAccess)
            .filter(
                FieldAccess.model == model_name,
                FieldAccess.field == field_name,
                FieldAccess.group_id.in_(group_ids),
            )
            .all()
        )

        if not rules:
            return True

        # If any group allows the field, allow it.
        return any(rule.can_write if for_write else rule.can_read for rule in rules)

    @staticmethod
    def can_read_field(user, db, model_name: str, field_name: str) -> bool:
        return FieldAccessService._resolve_rule(user, db, model_name, field_name, for_write=False)

    @staticmethod
    def can_write_field(user, db, model_name: str, field_name: str) -> bool:
        return FieldAccessService._resolve_rule(user, db, model_name, field_name, for_write=True)
