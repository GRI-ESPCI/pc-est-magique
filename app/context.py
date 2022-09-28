"""PC est magique - Custom request context"""

from ipaddress import IPv4Address
import functools
import re
import subprocess
from typing import TYPE_CHECKING, Any

import flask
from flask import g
from flask_babel import _
import flask_login

from app.models import Model, Device, PCeen, PermissionType, PermissionScope
from app.utils import helpers, typing
from app.utils.roles import grant_rezident_role

if TYPE_CHECKING:

    class _RequestContext:
        #: The caller's IP. Should never be ``None``, except if there is a problem with Nginx
        #: and that the current user is GRI.
        remote_ip: str | None
        #: Whether the request comes from the internal Rez network (and not from the Internet).
        internal: bool
        #: The caller's MAC address. Defined only if :attr:`.internal` is ``True``, else ``None``.
        mac: str | None
        #: Shorthand for :attr:`flask_login.current_user.is_authenticated`.
        logged_in: bool
        #: Shorthand for :attr:`flask_login.current_user`.
        #: Warning: ignores doas mechanism; please use :attr:`.pceen` instead. (default ``None``)
        logged_in_user: PCeen | None
        #: If ``True``, the logged in user is a GRI that is doing an action as another PCéen.
        doas: bool
        #: The PCéen the request is made as: ``None`` if not :attr:`.logged_in`,
        #: the controlled PCéen if :attr:`.doas`, or :attr:`.logged_in_user`.
        pceen: PCeen | None
        #: Whether the current user is logged in and is a GRI.
        is_gri: bool
        #: Whether the current is logged in and has a rolling rental.
        has_a_room: bool
        #: The :class:`~.models.Device` of the current request, if registered.
        #: ``None`` if attr:`.internal` is ``False``.
        device: Device | None
        #: Whether the current user is logged in and that :attr:`.g.device` is defined and owned by the user.
        own_device: bool
        #: ``True``, except if:
        #:    * The user is not logged in;
        #:    * The user is logged in but do not have a room;
        #:    * The user is logged in, has a room but connects from the internal network from a device not registered;
        #:    * The user is logged in, has a room and connects from the internal network from a device registered
        #:      but not owned by him.
        intrarez_setup: bool
        #: The endpoint of the page that the user must visit first to regularize its situation
        #: (see :func:`.intrarez_setup_only`).  Defined only if attr:`.intrarez_setup` is ``False``.
        redemption_endpoint: str
        #: The query parameters for attr:`.redemption_endpoint`, if applicable.
        redemption_params: dict[str, Any]

    #: salut
    g: _RequestContext


def create_request_context() -> typing.RouteReturn | None:
    """Make checks about current request and define custom ``g`` properties.

    Intended to be registered by :func:`before_request`.
    """
    # Defaults
    g.remote_ip = None
    g.mac = None
    g.internal = False
    g.logged_in = False
    g.logged_in_user = None
    g.pceen = None
    g.is_gri = False
    g.doas = False
    g.has_a_room = False
    g.device = None
    g.own_device = False
    g.intrarez_setup = True
    g.redemption_endpoint = None
    g.redemption_params = {}

    # Get user
    current_user = typing.cast(flask_login.AnonymousUserMixin | PCeen, flask_login.current_user)
    g.logged_in = current_user.is_authenticated
    if g.logged_in:
        g.logged_in_user = typing.cast(PCeen, current_user)
        g.pceen = g.logged_in_user  # May be overridden later if doas
        g.is_gri = g.pceen.is_gri
    else:
        g.intrarez_setup = False
        g.redemption_endpoint = "auth.auth_needed"

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
            return flask.redirect(flask.url_for(flask.request.endpoint or "main.index", **new_args))

    # Check maintenance
    if flask.current_app.config["MAINTENANCE"]:
        if g.is_gri:
            flask.flash(
                _("Le site est en mode maintenance : seuls les GRI peuvent y accéder."),
                "warning",
            )
        else:
            flask.abort(503)  # 503 Service Unavailable

    # Get IP
    g.remote_ip = flask.current_app.config["FORCE_IP"] or _get_remote_ip()
    if not g.remote_ip:
        # X-Real-Ip header not set by Nginx: application bug?
        if g.is_gri:
            flask.flash("X-Real-Ip header not present! Check Nginx config!", "danger")
        else:
            g.intrarez_setup = False
            g.redemption_endpoint = "devices.error"
            g.redemption_params = {"reason": "ip"}
            return helpers.safe_redirect("devices.error", reason="ip")

    # Get MAC
    if not g.doas:
        # Doas = never internal, because we are not on PCeen's device
        g.mac = flask.current_app.config["FORCE_MAC"] or _get_mac(g.remote_ip)
        g.internal = bool(g.mac)
    if not g.internal and not g.intrarez_setup:
        g.redemption_endpoint = "main.index"

    if not g.logged_in:
        # All further checks need a logged-in user
        return None

    # Inform type-checker we now have a real PCeen
    g.pceen = typing.cast(PCeen, g.pceen)

    # Check room
    g.has_a_room = g.pceen.has_a_room
    if not g.has_a_room:
        g.intrarez_setup = False
        g.redemption_endpoint = "rooms.register"
        if not g.doas:
            g.redemption_params = {"hello": True}

    if g.internal:
        # Get device
        g.device = Device.query.filter_by(mac_address=g.mac).first()
        if g.device:
            g.device.update_last_seen()
        else:
            if not g.pceen.has_permission(PermissionType.read, PermissionScope.intrarez):
                # Internal connection from a new device: grant access to IntraRez
                grant_rezident_role(g.pceen)

            if g.intrarez_setup:
                # Internal but device not registered: must register
                g.intrarez_setup = False
                g.redemption_endpoint = "devices.register"
                g.redemption_params = {"mac": g.mac}
                if not g.doas:
                    g.redemption_params["hello"] = True

            # Last check need a device
            return None

        # Check device owner
        g.own_device = g.pceen == g.device.pceen
        if g.intrarez_setup and not g.own_device:
            # Internal, device but not owned: must transfer
            g.intrarez_setup = False
            g.redemption_endpoint = "devices.transfer"
            g.redemption_params = {"mac": g.mac}
            if not g.doas:
                g.redemption_params["hello"] = True
            return None

    # Check at least one device
    if g.intrarez_setup and not g.pceen.devices:
        g.intrarez_setup = False
        g.redemption_endpoint = "devices.register"
        return None

    # Add first subscription if necessary
    if g.intrarez_setup and not g.pceen.current_subscription:
        g.pceen.add_first_subscription()

    # All set!
    return None


def _get_remote_ip() -> str | None:
    """Fetch the remote IP from the request headers.

    Returns:
        The calling IP, or ``None`` if the header is missing.
    """
    return flask.request.headers.get("X-Real-Ip")


def _get_mac(remote_ip) -> str | None:
    """Fetch the remote rezident MAC address from the ARP table.

    Args:
        remote_ip: The IP of the remote rezident.

    Returns:
        The corresponding MAC address, or ``None`` if not in the list.
    """
    output = subprocess.run(["/sbin/arp", "-a"], capture_output=True)
    # arp -a liste toutes les correspondances IP - mac connues
    # résultat : lignes "domain (ip) at mac_address ..."
    match = re.search(rf"^.*? \({remote_ip}\) at ([0-9a-f:]{{17}}).*", output.stdout.decode(), re.M)
    if match:
        return match.group(1)
    else:
        return None


# Type variables for decorators below
_RP = typing.ParamSpec("_RP")
_Route = typing.Callable[_RP, typing.RouteReturn]


def intrarez_setup_only(route: _Route) -> _Route:
    """Route function decorator to restrict route to all-good users.

    Redirects user to :attr:`.g.redemption_endpoint` if :attr:`.g.intrarez_setup` is ``False``.

    Args:
        route: The route function to restrict access to.

    Returns:
        The protected route.
    """

    @functools.wraps(route)
    def new_route(*args: _RP.args, **kwargs: _RP.kwargs) -> typing.RouteReturn:
        if g.intrarez_setup:
            return route(*args, **kwargs)
        else:
            return helpers.safe_redirect(g.redemption_endpoint, **g.redemption_params) or route()

    return new_route


def internal_only(route: _Route) -> _Route:
    """Route function decorator to restrict route to internal network.

    Aborts with a 401 Unauthorized if the request comes from the Internet (:attr:`.g.internal` is ``False``).

    Args:
        route: The route function to restrict access to.

    Returns:
        The protected route.
    """

    @functools.wraps(route)
    def new_route(*args: _RP.args, **kwargs: _RP.kwargs) -> typing.RouteReturn:
        if g.internal:
            return route(*args, **kwargs)
        else:
            flask.abort(401)  # 401 Unauthorized
            raise  # never reached, just to tell the type checker

    return new_route


def logged_in_only(route: _Route) -> _Route:
    """Route function decorator to restrict route to logged in users.

    Redirects user to "auth.auth_needed" if :attr:`.g.logged_in` is ``False``.

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
            flask.flash(_("Veuillez vous authentifier pour accéder à cette page."), "warning")
            return helpers.ensure_safe_redirect("auth.auth_needed")

    return new_route


def gris_only(route: _Route) -> _Route:
    """Route function decorator to restrict route to logged in GRIs.

    Aborts with a 403 if :attr:`.g.is_gri` is ``False``.

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
            flask.flash(_("Veuillez vous authentifier pour accéder à cette page."), "warning")
            return helpers.ensure_safe_redirect("auth.login")

    return new_route


def has_permission(type: PermissionType, scope: PermissionScope, elem: Model | None = None) -> bool | None:
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


def check_permission(type: PermissionType, scope: PermissionScope, elem: Model | None = None) -> None:
    """Ensure that the current user (if logged in) has a specific permission.

    Aborts with a redirection to the login page if not logged in;
    aborts with a 403 if the user does not have the requested permission;
    else silently returns.

    Args:
        type, scope, elem: Passed to :func:`.has_permission`.
    """
    permission = has_permission(type=type, scope=scope, elem=elem)
    if permission is None:
        flask.flash(_("Veuillez vous authentifier pour accéder à cette page."), "warning")
        flask.abort(helpers.ensure_safe_redirect("auth.login"))
    elif not permission:
        flask.abort(403)  # 403 Not Authorized


PSE = tuple[PermissionType, PermissionScope] | tuple[PermissionType, PermissionScope, Model | None]


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


def _address_in_range(address: str, start: str, stop: str) -> bool:
    return IPv4Address(start) <= IPv4Address(address) <= IPv4Address(stop)


def capture() -> typing.RouteReturn | None:
    """Redirect request to the adequate page based on its remote IP.

    Function called by the captive portal if the requested address is not one
    of PC est magique.

    Returns:
        The return value of :func:`flask.redirect`, or ``None`` if we are
        already on the adequate page (process request).
    """
    remote_ip = _get_remote_ip()
    if not remote_ip:
        # X-Real-Ip header not set by Nginx: application bug?
        return helpers.safe_redirect("devices.error", reason="ip")
    if _address_in_range(remote_ip, "10.0.0.100", "10.0.0.199"):
        # 10.0.0.100-199: Not registered
        return helpers.safe_redirect("main.index")
    if _address_in_range(remote_ip, "10.0.8.0", "10.0.255.255"):
        # 10.0.8-255.0-255: Banned (IP stores ban ID)
        a, b, c, d = g.remote_ip.split(".")
        g._ban = (int(c) - 8) * 256 + int(d)
        return helpers.safe_redirect("main.banned")

    return helpers.safe_redirect("main.index")
