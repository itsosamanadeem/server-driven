from sqlalchemy import event
from sqlalchemy.orm import Session

from core.hooks.executor import HookExecutor
from core.hooks import events
from core.hooks.context import HookContext
from core.hooks.hook_registry import hook_registry


@event.listens_for(Session, "before_flush")
def before_flush(session, flush_context, instances):

    # 🔹 NEW RECORDS (CREATE)
    for obj in session.new:
        ctx = HookContext(
            db=session,
            model=obj.__class__.__name__,
            obj=obj,
            data=obj.__dict__,
            action="create"
        )

        HookExecutor.run(events.BEFORE_CREATE, ctx)

        if ctx.stop:
            session.rollback()
            raise Exception(ctx.message or "Blocked by BEFORE_CREATE hook")

    # 🔹 UPDATED RECORDS
    for obj in session.dirty:
        ctx = HookContext(
            db=session,
            model=obj.__class__.__name__,
            obj=obj,
            data=obj.__dict__,
            action="write"
        )

        HookExecutor.run(events.BEFORE_UPDATE, ctx)

        if ctx.stop:
            session.rollback()
            raise Exception(ctx.message or "Blocked by BEFORE_UPDATE hook")

    # 🔹 DELETED RECORDS
    for obj in session.deleted:
        ctx = HookContext(
            db=session,
            model=obj.__class__.__name__,
            obj=obj,
            data=None,
            action="delete"
        )

        HookExecutor.run(events.BEFORE_DELETE, ctx)

        if ctx.stop:
            session.rollback()
            raise Exception(ctx.message or "Blocked by BEFORE_DELETE hook")