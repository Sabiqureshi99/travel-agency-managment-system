"""
core/permissions.py
====================
Permission constants and the permission-checking helper used throughout
the application.

Each module name is a string constant.  The permission actions (view, add,
edit, delete, print, export) come from ``core.enums.PermissionAction``.

Usage::

    from core.permissions import Modules, has_permission
    if not has_permission(current_user, Modules.FLIGHTS, "add"):
        raise PermissionDeniedError("add", Modules.FLIGHTS)
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.user import User


class Modules:
    """String constants for every application module name."""
    DASHBOARD = "dashboard"
    CUSTOMERS = "customers"
    EMPLOYEES = "employees"
    FLIGHTS = "flights"
    VISA = "visa"
    UMRAH = "umrah"
    HAJJ = "hajj"
    HOTELS = "hotels"
    TOURS = "tours"
    TRANSPORT = "transport"
    VENDORS = "vendors"
    ACCOUNTING = "accounting"
    REPORTS = "reports"
    DOCUMENTS = "documents"
    SETTINGS = "settings"
    BACKUP = "backup"

    ALL: list[str] = [
        DASHBOARD,
        CUSTOMERS,
        EMPLOYEES,
        FLIGHTS,
        VISA,
        UMRAH,
        HAJJ,
        HOTELS,
        TOURS,
        TRANSPORT,
        VENDORS,
        ACCOUNTING,
        REPORTS,
        DOCUMENTS,
        SETTINGS,
        BACKUP,
    ]


class Actions:
    """String constants for permission actions."""
    VIEW = "view"
    ADD = "add"
    EDIT = "edit"
    DELETE = "delete"
    PRINT = "print"
    EXPORT = "export"

    ALL: list[str] = [VIEW, ADD, EDIT, DELETE, PRINT, EXPORT]


# ---------------------------------------------------------------------------
# Default permission sets
# ---------------------------------------------------------------------------

# Admin gets EVERYTHING
ADMIN_PERMISSIONS: dict[str, list[str]] = {
    module: list(Actions.ALL) for module in Modules.ALL
}

# Owner gets EVERYTHING except they CANNOT edit the Company Configuration.
# The company_config restriction is enforced at the UI level (save button disabled).
# At the permission level the Owner has full access to all modules and actions.
OWNER_PERMISSIONS: dict[str, list[str]] = {
    module: list(Actions.ALL) for module in Modules.ALL
}

# Default employee: can view most things, no settings/backup/delete
DEFAULT_EMPLOYEE_PERMISSIONS: dict[str, list[str]] = {
    Modules.DASHBOARD: [Actions.VIEW],
    Modules.CUSTOMERS: [Actions.VIEW, Actions.ADD, Actions.EDIT, Actions.PRINT, Actions.EXPORT],
    Modules.EMPLOYEES: [Actions.VIEW],
    Modules.FLIGHTS: [Actions.VIEW, Actions.ADD, Actions.EDIT, Actions.PRINT, Actions.EXPORT],
    Modules.VISA: [Actions.VIEW, Actions.ADD, Actions.EDIT, Actions.PRINT, Actions.EXPORT],
    Modules.UMRAH: [Actions.VIEW, Actions.ADD, Actions.EDIT, Actions.PRINT, Actions.EXPORT],
    Modules.HAJJ: [Actions.VIEW, Actions.ADD, Actions.EDIT, Actions.PRINT, Actions.EXPORT],
    Modules.HOTELS: [Actions.VIEW, Actions.ADD, Actions.EDIT, Actions.PRINT, Actions.EXPORT],
    Modules.TOURS: [Actions.VIEW, Actions.ADD, Actions.EDIT, Actions.PRINT, Actions.EXPORT],
    Modules.TRANSPORT: [Actions.VIEW],
    Modules.VENDORS: [Actions.VIEW],
    Modules.ACCOUNTING: [Actions.VIEW, Actions.PRINT, Actions.EXPORT],
    Modules.REPORTS: [Actions.VIEW, Actions.PRINT, Actions.EXPORT],
    Modules.DOCUMENTS: [Actions.VIEW, Actions.ADD, Actions.PRINT],
    Modules.SETTINGS: [],
    Modules.BACKUP: [],
}


def has_permission(user: "User", module: str, action: str) -> bool:
    """
    Check whether ``user`` has the given ``action`` permission on ``module``.

    Admins always return True.
    Owners have full access but cannot update Company Configuration (enforced in UI).
    Employees are checked against their ``permissions`` JSON column.

    Args:
        user:   The authenticated User model instance.
        module: One of the ``Modules.*`` constants.
        action: One of the ``Actions.*`` constants.

    Returns:
        True if the user is allowed to perform the action, False otherwise.
    """
    from core.enums import UserRole

    if user.role == UserRole.ADMIN:
        return True

    if user.role == UserRole.OWNER:
        return True  # Full access; company config restriction is enforced at UI layer

    # permissions is stored as JSON: {"module": ["action1", "action2"], ...}
    permissions: dict[str, list[str]] = user.permissions or {}
    return action in permissions.get(module, [])


def get_all_permissions_for_user(user: "User") -> dict[str, list[str]]:
    """
    Return the full permission map for a user.

    Admins and Owners receive the full admin permission set.
    Employees receive their stored permissions (merged with defaults for
    any missing modules to ensure forward-compatibility).
    """
    from core.enums import UserRole

    if user.role in (UserRole.ADMIN, UserRole.OWNER):
        return ADMIN_PERMISSIONS.copy()

    stored: dict[str, list[str]] = user.permissions or {}
    # Merge with defaults (new modules added later get empty permissions by default)
    merged = {module: [] for module in Modules.ALL}
    merged.update(stored)
    return merged


def build_default_employee_permissions() -> dict[str, list[str]]:
    """Return a copy of the default employee permission set."""
    return {k: list(v) for k, v in DEFAULT_EMPLOYEE_PERMISSIONS.items()}


def is_owner(user: "User") -> bool:
    """Return True if the user has the Owner role."""
    from core.enums import UserRole
    return user.role == UserRole.OWNER


def can_edit_company_config(user: "User") -> bool:
    """Return True only for Admin users. Owners cannot update company configuration."""
    from core.enums import UserRole
    return user.role == UserRole.ADMIN
