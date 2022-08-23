"""PC est magique - Répare les miniatures et versions zippées manquantes.

Ce script peut uniquement être appelé depuis Flask :
  * Soit depuis l'interface en ligne (menu GRI) ;
  * Soit par ligne de commande :
    cd /home/pc-est-magique/pc-est-magique
    ./env/bin/flask script fix_photos.py

02/2022 Loïc 137
"""

import subprocess
import sys

try:
    from app.models import Photo
    from app.utils import loggers
    from app.utils.helpers import print_progressbar
except ImportError:
    sys.stderr.write(
        "ERREUR - Ce script peut uniquement être appelé depuis Flask :\n"
        "  * Soit depuis l'interface en ligne (menu GRI) ;\n"
        "  * Soit par ligne de commande :\n"
        "    cd /home/pc-est-magique/pc-est-magique; "
        "    ./env/bin/flask script fix_photos.py\n"
    )
    sys.exit(1)


@loggers.log_exception(reraise=True)
def main() -> None:
    photos = Photo.query.all()
    n = len(photos)
    print_progressbar(0, n, "Fixing photos...", f"{0}/{n}")
    for i, photo in enumerate(photos):
        # Create thumbnail and gzipped versions
        try:
            subprocess.run(
                [
                    "convert",
                    photo.full_path,  # Take the picture,
                    "-resize",
                    "136x136^",  # Fill a 136x136 box,
                    "-gravity",
                    "center",  # Refer to image center,
                    "-extent",
                    "136x136",  # Then crop overflow,
                    photo.thumb_full_path,  # There is the thumbnail!
                ],
                capture_output=True,
                check=True,
            )
        except subprocess.CalledProcessError as exc:
            print(
                f"WARNING: {photo.full_path} Unable to create thumbnail:",
                exc.cmd,
                exc.stderr.decode(),
            )
            continue
        except Exception as exc:
            print(f"WARNING: {photo.full_path} Unable to create thumbnail:", exc)
            continue
        subprocess.run(["gzip", "-fk", photo.full_path])
        subprocess.run(["gzip", "-fk", photo.thumb_full_path])
        print_progressbar(i + 1, n, "Fixing photos...", f"{i + 1}/{n}")
