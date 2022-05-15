""""PC est magique - Custom request context"""

import functools

import flask
from flask import g
from flask_babel import _
import flask_login

from app.models import Model, PCeen, PermissionType, PermissionScope
from app.utils import helpers, typing


def create_request_context() -> typing.RouteReturn | None:
    """Make checks about current request and define custom ``g`` properties.

    Intended to be registered by :func:`before_request`.

    Defines:
      * :attr:`flask.g.logged_in` (default ``False``):
            Shorthand for :attr:`flask_login.current_user.is_authenticated`.
      * :attr:`flask.g.logged_in_user` (default ``None``):
            Shorthand for :attr:`flask_login.current_user`. Warning: ignores
            doas mechanism; please use :attr:`flask.g.pceen` instead.
      * :attr:`flask.g.doas` (default ``False``):
            If ``True``, the logged in user is a GRI that is doing an action
            as another pceen.
      * :attr:`flask.g.pceen` (default ``None``):
            The pceen the request is made as: ``None`` if not
            :attr:`flask.g.logged_in`, the controlled pceen if
            :attr:`~flask.g.doas`, or :attr:`flask.g.logged_in_user`.
      * :attr:`flask.g.is_gri` (default ``False``):
            ``True`` if the user is logged in and is a GRI.
    """
    # Defaults
    g.logged_in = False
    g.logged_in_user = None
    g.pceen = None
    g.is_gri = False
    g.doas = False

    # Get user
    current_user = typing.cast(
        flask_login.AnonymousUserMixin | PCeen, flask_login.current_user
    )
    g.logged_in = current_user.is_authenticated
    if g.logged_in:
        g.logged_in_user = typing.cast(PCeen, current_user)
        g.pceen = g.logged_in_user  # May be overridden later if doas
        g.is_gri = g.pceen.is_gri

    # Check doas
    doas_id = flask.request.args.get("doas", "")
    doas = PCeen.query.get(doas_id) if doas_id.isdigit() else None
    if doas:
        if g.is_gri:
            g.pceen = doas
            g.is_gri = g.pceen.is_gri
            g.doas = True
        else:
            # Not authorized to do things as other pceens!
            new_args = flask.request.args.copy()
            del new_args["doas"]
            return flask.redirect(
                flask.url_for(flask.request.endpoint or "main.index", **new_args)
            )

    # Check maintenance
    if flask.current_app.config["MAINTENANCE"]:
        if g.is_gri:
            flask.flash(
                _(
                    "Le site est en mode maintenance : seuls les GRI "
                    "peuvent y accéder."
                ),
                "warning",
            )
        else:
            flask.abort(503)  # 503 Service Unavailable

    # All set!
    return None


# Type variables for decoraters below
_RP = typing.ParamSpec("_RP")
_Route = typing.Callable[_RP, typing.RouteReturn]


def logged_in_only(route: _Route) -> _Route:
    """Route function decorator to restrict route to logged in users.

    Redirects user to "auth.auth_needed" if :attr:`flask.g.logged_in`
    is ``False``.

    Args:
        route: The route function to restrict access to.

    Returns:
        The protected route.
    """

    @functools.wraps(route)
    def new_route(*args: _RP.args, **kwargs: _RP.kwargs) -> typing.RouteReturn:
        if g.logged_in:
            return route(*args, **kwargs)
        else:
            flask.flash(
                _("Veuillez vous authentifier pour accéder " "à cette page."), "warning"
            )
            return helpers.ensure_safe_redirect("auth.auth_needed")

    return new_route


def gris_only(route: _Route) -> _Route:
    """Route function decorator to restrict route to logged in GRIs.

    Aborts with a 403 if :attr:`flask.g.is_gri` is ``False``.

    Args:
        route: The route function to restrict access to.

    Returns:
        The protected route.
    """

    @functools.wraps(route)
    def new_route(*args: _RP.args, **kwargs: _RP.kwargs) -> typing.RouteReturn:
        if g.is_gri:
            return route(*args, **kwargs)
        elif g.logged_in:
            flask.abort(403)  # 403 Not Authorized
            raise  # never reached, just to tell the type checker
        else:
            flask.flash(
                _("Veuillez vous authentifier pour accéder " "à cette page."), "warning"
            )
            return helpers.ensure_safe_redirect("auth.login")

    return new_route


def has_permission(
    type: PermissionType, scope: PermissionScope, elem: Model | None = None
) -> bool | None:
    """Check if the current user (if logged in) has a specific permission.

    Args:
        type: The permission type (.read, .write...).
        scope: The permission scope (.pceen, .album...).
        elem: The database entry to check the permission for, if applicable.

    Returns:
        ``None`` if no user is logged in, else whether the logged in user
        has the requested permission.
    """
    if not g.logged_in:
        return None
    return g.pceen.has_permission(type=type, scope=scope, elem=elem)


def check_permission(
    type: PermissionType, scope: PermissionScope, elem: Model | None = None
) -> None:
    """Ensure that the current user (if logged in) has a specific permission.

    Aborts with a redirection to the login page if not logged in;
    aborts with a 403 if the user does not have the requested permission;
    else silently returns.

    Args:
        type, scope, elem: Passed to :func:`.has_permission`.
    """
    permission = has_permission(type=type, scope=scope, elem=elem)
    if permission is None:
        flask.flash(
            _("Veuillez vous authentifier pour accéder à cette page."), "warning"
        )
        flask.abort(helpers.ensure_safe_redirect("auth.login"))
    elif not permission:
        flask.abort(403)  # 403 Not Authorized


PSE = (
    tuple[PermissionType, PermissionScope]
    | tuple[PermissionType, PermissionScope, Model | None]
)


def check_any_permission(*pses: PSE) -> None:
    """Ensure that the current user has at least one of several permissions.

    Behaves like :func:`.check_permission`.

    Args:
        *pses: Permissions arguments to check: tuples ``(type, scope)``
            or ``(type, scope, elem)`` to pass to :func:`.has_permission`.
    """
    if not pses:
        return
    pse, *other = pses
    if has_permission(*pse):
        return
    if other:
        check_any_permission(*other)  # Other permissions: check
    else:
        check_permission(*pse)  # Last permission, none granted: abort


def check_all_permissions(*pses: PSE) -> None:
    """Ensure that the current user has all of several permissions.

    Behaves like :func:`.check_permission`.

    Args:
        *pses: Permissions arguments to check: tuples ``(type, scope)``
            or ``(type, scope, elem)`` to pass to :func:`.has_permission`.
    """
    if not pses:
        return
    pse, *other = pses
    check_permission(*pse)
    check_all_permissions(*other)


def permission_only(
    type: PermissionType, scope: PermissionScope, elem: Model | None = None
) -> typing.Callable[[_Route], _Route]:
    """Route function decorator to restrict route to a specific permission.

    Decorator version of :func:`.check_permission`.

    Args:
        type, scope, elem: Passed to :func:`.check_permission`.

    Returns:
        The decorator to apply to protect the route.
    """

    def decorator(route: _Route) -> _Route:
        @functools.wraps(route)
        def new_route(*args: _RP.args, **kwargs: _RP.kwargs) -> typing.RouteReturn:
            check_permission(type=type, scope=scope, elem=elem)
            return route(*args, **kwargs)

        return new_route

    return decorator
