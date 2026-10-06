"""PC est magique - BD (Bandes Dessinées) Routes"""

import io
import re

import flask
from flask_babel import _
import openpyxl
import sqlalchemy as sa

from app import context, db
from app.models import BDItem, PermissionScope, PermissionType
from app.routes.bd import bp
from app.routes.bd.forms import UploadCatalogueForm
from app.utils import typing

_ALLOWED_SHEETS = {"Livres": "livre", "Bandes Dessinées": "bd"}

import requests

def fetch_info_from_google_books(isbn: str | None, titre: str, auteurs: str) -> dict:
    def do_fetch(query):
        url = f"https://www.googleapis.com/books/v1/volumes?q={requests.utils.quote(query)}"
        api_key = flask.current_app.config.get("GOOGLE_BOOKS_API_KEY")
        if api_key:
            url += f"&key={api_key}"
        resp = requests.get(url, timeout=3)
        data = resp.json()
        if "error" in data and data["error"].get("code") == 429:
            raise Exception("Quota")
        if "items" in data and data["items"]:
            for item in data["items"]:
                v = item.get("volumeInfo", {})
                resume = v.get("description")
                image_url = v.get("imageLinks", {}).get("thumbnail")
                if image_url and image_url.startswith("http:"):
                    image_url = image_url.replace("http:", "https:")
                
                found_isbn = None
                for id_obj in v.get("industryIdentifiers", []):
                    if id_obj.get("type") in ("ISBN_13", "ISBN_10"):
                        found_isbn = id_obj.get("identifier")
                        if id_obj.get("type") == "ISBN_13":
                            break
                
                if resume or image_url:
                    return {"resume": resume, "image_url": image_url, "isbn": found_isbn}
        return {}

    try:
        if isbn:
            clean = isbn.replace("-", "").replace(" ", "")
            res = do_fetch(f"isbn:{clean}")
            if res:
                return res
        auteur = auteurs.split(",")[0].strip() if auteurs else ""
        
        # Fallback search (strict searches often fail)
        query = f"{titre} {auteur}".strip()
        return do_fetch(query)
    except Exception as e:
        if str(e) == "Quota":
            raise e
        return {}



def _clean_isbn(raw) -> str | None:
    """Normalize an ISBN value from the spreadsheet cell."""
    if raw is None:
        return None
    s = str(raw).strip().replace("-", "").replace(" ", "")
    # Remove trailing .0 that Excel adds to numeric ISBNs
    s = re.sub(r"\.0$", "", s)
    return s if s else None


def _clean_pages(raw) -> int | None:
    """Convert a pages cell value to int, or None."""
    if raw is None:
        return None
    try:
        return int(float(str(raw).strip()))
    except (ValueError, TypeError):
        return None


def _clean_date(raw) -> str | None:
    """Convert a date cell value to a short string (YYYY or full date)."""
    if raw is None:
        return None
    s = str(raw).strip()
    return s if s else None


def _import_xlsx(file_stream) -> tuple[int, int, int]:
    """Parse the XLSX catalogue and insert items into the database.

    Returns:
        Tuple (added, updated, deleted) counts.
    """
    wb = openpyxl.load_workbook(file_stream, read_only=True, data_only=True)

    # Collect all incoming rows per category
    incoming: dict[str, list[dict]] = {"livre": [], "bd": []}

    for sheet_name, categorie in _ALLOWED_SHEETS.items():
        if sheet_name not in wb.sheetnames:
            continue
        ws = wb[sheet_name]
        rows = list(ws.iter_rows(min_row=2, values_only=True))
        for row in rows:
            if not row or len(row) < 2:
                continue
            auteurs = str(row[0]).strip() if row[0] else ""
            titre = str(row[1]).strip() if row[1] else ""
            if not auteurs and not titre:
                continue  # skip empty rows

            date_pub = _clean_date(row[4]) if len(row) > 4 else None
            editeur = str(row[5]).strip() if len(row) > 5 and row[5] else None
            pages = _clean_pages(row[6]) if len(row) > 6 else None
            isbn = _clean_isbn(row[7]) if len(row) > 7 else None

            incoming[categorie].append(
                {
                    "auteurs": auteurs,
                    "titre": titre,
                    "date_publication": date_pub,
                    "editeur": editeur,
                    "pages": pages,
                    "isbn": isbn,
                    "categorie": categorie,
                }
            )

    wb.close()

    added = 0
    updated = 0
    deleted = 0

    for categorie, rows in incoming.items():
        if not rows:
            # No data for this category in the file: leave existing intact
            continue

        # Build a lookup key -> existing DB record for this category
        existing: dict[tuple, BDItem] = {}
        for item in db.session.scalars(
            sa.select(BDItem).where(BDItem.categorie == categorie)
        ).all():
            key = (_normalize(item.titre), _normalize(item.auteurs))
            existing[key] = item

        seen_keys: set[tuple] = set()
        for row in rows:
            key = (_normalize(row["titre"]), _normalize(row["auteurs"]))

            if key in existing:
                # Update existing item
                item = existing[key]
                item.date_publication = row["date_publication"]
                item.editeur = row["editeur"]
                item.pages = row["pages"]
                item.isbn = row["isbn"]

                updated += 1
            else:
                # New item

                item = BDItem(**row)
                db.session.add(item)
                added += 1

            seen_keys.add(key)

        # Delete items that are no longer in the file
        for key, item in existing.items():
            if key not in seen_keys:
                db.session.delete(item)
                deleted += 1

    db.session.commit()
    return added, updated, deleted



def _background_sync_task(app):
    """Background task to sync missing covers/summaries for the entire catalog."""
    import time
    with app.app_context():
        missing_items = db.session.scalars(
            sa.select(BDItem).where(
                sa.or_(
                    BDItem.resume.is_(None), 
                    BDItem.resume == "",
                    BDItem.image_url.is_(None),
                    BDItem.image_url == ""
                )
            )
        ).all()
        for item in missing_items:
            try:
                info = fetch_info_from_google_books(item.isbn, item.titre, item.auteurs)
                item.resume = info.get("resume") or ""
                item.image_url = info.get("image_url") or ""
                if info.get("isbn") and not item.isbn: 
                    item.isbn = info["isbn"]
                db.session.commit()
                time.sleep(1) # Soft pause between requests
            except Exception as e:
                # E.g. Quota
                db.session.rollback()
                break

def _normalize(s: str) -> str:
    """Lowercase and collapse whitespace for comparison."""
    return re.sub(r"\s+", " ", s.lower()).strip()

@bp.route("")
@bp.route("/")
def main() -> typing.RouteReturn:
    """BD catalogue – user view."""

    search = flask.request.args.get("q", "").strip()

    query = sa.select(BDItem).order_by(BDItem.titre)
    if search:
        pattern = f"%{search}%"
        query = query.where(
            sa.or_(
                BDItem.titre.ilike(pattern),
                BDItem.auteurs.ilike(pattern),
                BDItem.editeur.ilike(pattern),
            )
        )

    items = db.session.scalars(query).all()

    # Stats for display
    total_livres = db.session.scalar(
        sa.select(sa.func.count()).where(BDItem.categorie == "livre")
    ) or 0
    total_bds = db.session.scalar(
        sa.select(sa.func.count()).where(BDItem.categorie == "bd")
    ) or 0

    can_admin = context.g.is_gri or (
        context.g.logged_in
        and context.g.pceen.has_permission(PermissionType.write, PermissionScope.bd)
    )

    return flask.render_template(
        "bd/main.html",
        title=_("Catalogue BD"),
        items=items,
        search=search,
        total_livres=total_livres,
        total_bds=total_bds,
        can_admin=can_admin,
    )


@bp.route("/admin", methods=["GET"])
@context.permission_only(PermissionType.write, PermissionScope.bd)
def admin() -> typing.RouteReturn:
    """BD admin dashboard."""
    form = UploadCatalogueForm()

    total_livres = db.session.scalar(
        sa.select(sa.func.count()).where(BDItem.categorie == "livre")
    ) or 0
    total_bds = db.session.scalar(
        sa.select(sa.func.count()).where(BDItem.categorie == "bd")
    ) or 0

    # Last 10 items added (highest IDs)
    recent = db.session.scalars(
        sa.select(BDItem).order_by(BDItem.id.desc()).limit(10)
    ).all()

    return flask.render_template(
        "bd/admin.html",
        title=_("BD – Administration"),
        form=form,
        total_livres=total_livres,
        total_bds=total_bds,
        recent=recent,
    )


@bp.route("/admin/upload", methods=["POST"])
@context.permission_only(PermissionType.write, PermissionScope.bd)
def admin_upload() -> typing.RouteReturn:
    """Handle XLSX catalogue upload and upsert into DB."""
    form = UploadCatalogueForm()
    if not form.validate_on_submit():
        for field, errors in form.errors.items():
            for error in errors:
                flask.flash(f"{error}", "danger")
        return flask.redirect(flask.url_for("bd.admin"))

    file_data = form.fichier.data
    stream = io.BytesIO(file_data.read())

    try:
        added, updated, deleted = _import_xlsx(stream)
        
        # Start background sync
        import threading
        app = flask.current_app._get_current_object()
        threading.Thread(target=_background_sync_task, args=(app,)).start()
        
    except Exception as exc:
        flask.flash(
            _("Erreur lors de l'import : %(err)s", err=str(exc)), "danger"
        )
        return flask.redirect(flask.url_for("bd.admin"))

    flask.flash(
        _(
            "Import rapide réussi : %(a)d ajouté(s), %(u)d mis à jour, %(d)d supprimé(s). La récupération des résumés manquants via Google Books continue en arrière-plan (cela peut prendre quelques minutes).",
            a=added,
            u=updated,
            d=deleted,
        ),
        "success",
    )
    return flask.redirect(flask.url_for("bd.admin"))


@bp.route("/admin/fetch_missing", methods=["POST"])
@context.permission_only(PermissionType.write, PermissionScope.bd)
def admin_fetch_missing() -> typing.RouteReturn:
    """Fetch missing summaries/covers for existing books (max 15 at a time)."""
    missing_items = db.session.scalars(
        sa.select(BDItem).where(
            sa.or_(
                BDItem.resume.is_(None), 
                BDItem.resume == "",
                BDItem.image_url.is_(None),
                BDItem.image_url == ""
            )
        ).limit(15)
    ).all()

    if not missing_items:
        flask.flash(_("Toutes les BD ont été analysées !"), "success")
        return flask.redirect(flask.url_for("bd.admin"))

    count = 0
    import time
    for item in missing_items:
        try:
            print(f"[BD Debug] Analyse de : {item.titre}...")
            info = fetch_info_from_google_books(item.isbn, item.titre, item.auteurs)
            
            # Update fields. If none found, we set to "" so we don't query again
            item.resume = info.get("resume") or ""
            item.image_url = info.get("image_url") or ""
            if info.get("isbn") and not item.isbn: 
                item.isbn = info["isbn"]
                
            count += 1
            # Rate limiting soft pause
            time.sleep(0.5)
        except Exception as e:
            if str(e) == "Quota":
                flask.flash(_("Quota Google Books atteint. Réessayez plus tard ou ajoutez une clé d'API."), "warning")
                break
            else:
                print(f"[BD Debug] Erreur lors de l'analyse : {e}")

    db.session.commit()
    flask.flash(_("%(c)d fiches ont été analysées.", c=count), "success")
    return flask.redirect(flask.url_for("bd.admin"))
