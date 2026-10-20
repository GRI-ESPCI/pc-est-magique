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


def _import_xlsx(file_stream) -> int:
    """Parse the XLSX catalogue and insert new items into the database.

    Returns:
        Number of added items.
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

        for row in rows:
            key = (_normalize(row["titre"]), _normalize(row["auteurs"]))

            if key not in existing:
                # New item
                item = BDItem(**row)
                db.session.add(item)
                existing[key] = item
                added += 1

    db.session.commit()
    return added



def _background_sync_task(app):
    """Background task to sync missing covers/summaries for the entire catalog."""
    import time
    with app.app_context():
        missing_items = db.session.scalars(
            sa.select(BDItem).where(
                sa.or_(
                    BDItem.resume.is_(None),
                    BDItem.image_url.is_(None),
                )
            )
        ).all()
        for item in missing_items:
            try:
                info = fetch_info_from_google_books(item.isbn, item.titre, item.auteurs)
                if not item.resume:
                    item.resume = info.get("resume") or ""
                if not item.image_url:
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


def _get_bd_counts() -> tuple[int, int]:
    """Return (total_livres, total_bds) in a single grouped query."""
    counts = dict(
        db.session.execute(
            sa.select(BDItem.categorie, sa.func.count(BDItem.id)).group_by(BDItem.categorie)
        ).all()
    )
    return counts.get("livre", 0), counts.get("bd", 0)


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
    total_livres, total_bds = _get_bd_counts()

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
    total_livres, total_bds = _get_bd_counts()

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
        added = _import_xlsx(stream)
        
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
            "Import réussi : %(a)d nouvelle(s) entrée(s) ajoutée(s). La récupération des résumés manquants via Google Books continue en arrière-plan (cela peut prendre quelques minutes).",
            a=added,
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
                BDItem.image_url.is_(None),
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
            if not item.resume:
                item.resume = info.get("resume") or ""
            if not item.image_url:
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


@bp.route("/edit/<int:item_id>", methods=["POST"])
@context.permission_only(PermissionType.write, PermissionScope.bd)
def edit_item(item_id: int) -> typing.RouteReturn:
    """Update BD item details (image_url, resume, nota_bene)."""
    item = db.session.get(BDItem, item_id)
    if not item:
        flask.flash(_("Entrée introuvable."), "danger")
        return flask.redirect(flask.url_for("bd.main"))

    image_url = flask.request.form.get("image_url", "").strip()
    resume = flask.request.form.get("resume", "").strip()
    nota_bene = flask.request.form.get("nota_bene", "").strip()
    search_q = flask.request.form.get("q", "").strip()

    if image_url:
        item.image_url = image_url[:500]
    elif item.image_url is not None:
        item.image_url = ""

    if resume:
        item.resume = resume
    elif item.resume is not None:
        item.resume = ""

    item.nota_bene = nota_bene or None

    db.session.commit()

    flask.flash(
        _("La fiche « %(titre)s » a été mise à jour.", titre=item.titre),
        "success",
    )

    if search_q:
        return flask.redirect(flask.url_for("bd.main", q=search_q))
    return flask.redirect(flask.url_for("bd.main"))


@bp.route("/delete/<int:item_id>", methods=["POST"])
@context.permission_only(PermissionType.write, PermissionScope.bd)
def delete_item(item_id: int) -> typing.RouteReturn:
    """Delete a BD item."""
    item = db.session.get(BDItem, item_id)
    if not item:
        flask.flash(_("Entrée introuvable."), "danger")
        return flask.redirect(flask.url_for("bd.main"))

    titre = item.titre
    search_q = flask.request.form.get("q", "").strip()

    db.session.delete(item)
    db.session.commit()

    flask.flash(
        _("La fiche « %(titre)s » a été supprimée.", titre=titre),
        "success",
    )

    if search_q:
        return flask.redirect(flask.url_for("bd.main", q=search_q))
    return flask.redirect(flask.url_for("bd.main"))
