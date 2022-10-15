"""PC est magique - [ONE-SHOT] Importe les données du site du bar dans PC est magique.

Ce script peut uniquement être appelé depuis Flask :
  * Soit depuis l'interface en ligne (menu GRI) ;
  * Soit par ligne de commande :
    cd /home/pc-est-magique/pc-est-magique
    ./env/bin/flask script import_bar_data.py

10/2022 Loïc 137
"""

import os
import sys

import tqdm
import sqlalchemy
import sqlalchemy.orm
from sqlalchemy.ext.automap import automap_base
from unidecode import unidecode
from app.enums import BarTransactionType

from app.routes.auth.utils import new_username

try:
    from app import db, __version__
    from app.models import Role, PCeen, BarItem, BarTransaction
    from app.utils import helpers, loggers, typing

except ImportError:
    sys.stderr.write(
        "ERREUR - Ce script peut uniquement être appelé depuis Flask :\n"
        "  * Soit depuis l'interface en ligne (menu GRI) ;\n"
        "  * Soit par ligne de commande :\n"
        "    cd /home/pc-est-magique/pc-est-magique; "
        "    ./env/bin/flask script import_bar_data.py\n"
    )
    sys.exit(1)


class Importer:
    def __init__(self) -> None:
        self.student_role = Role.query.filter_by(name="Élève").one()
        self.bar_user_role = Role.query.filter_by(name="Client Bar").one()
        self.barman_role = Role.query.filter_by(name="Barman").one()
        self.observer_role = Role.query.filter_by(name="Observateur Bar").one()
        self.promos_roles = {}
        for promotion in range(100, 142):
            role = Role.query.filter_by(name=str(promotion)).one_or_none()
            if not role:
                role = Role(name=str(promotion), index=promotion)
                db.session.add(role)
            self.promos_roles[promotion] = role

    def _grant_role(self, role, pceen: PCeen):
        if role not in pceen.roles:
            pceen.roles.append(role)

    def run(self):
        self.connect_to_bar_db()
        self.sync_users()
        self.create_items()
        self.create_transactions()
        self.restore_balances()

        print("Committing changes...")
        db.session.commit()

    def connect_to_bar_db(self):
        BarBase = automap_base()
        engine = sqlalchemy.create_engine(os.getenv("BAR_DATABASE_URI"))
        BarBase.prepare(autoload_with=engine)

        self.User = BarBase.classes.user
        self.Item = BarBase.classes.item
        self.Transaction = BarBase.classes.transaction
        self.GlobalSetting = BarBase.classes.global_setting

        session = sqlalchemy.orm.Session(engine)
        session.flush = lambda *args, **kwargs: print("NO FLUSH")
        self.bar_session = session

    def sync_users(self):
        self.user_id_mapping: dict[int, int] = {}
        self.user_username_mapping: dict[int, int] = {}
        self.user_balances: dict[PCeen, float] = {}

        pem_users: list[PCeen] = PCeen.query.all()
        email_mapping = {pceen.email.lower().replace(".psl.eu", ".fr"): pceen for pceen in pem_users} | {
            pceen.email.lower().replace(".fr", ".psl.eu"): pceen for pceen in pem_users
        }
        full_name_mapping = {unidecode(pceen.full_name.lower()): pceen for pceen in pem_users}

        for bar_user in tqdm.tqdm(self.bar_session.query(self.User).all(), "Users"):
            if pceen := email_mapping.get(bar_user.email.lower()):
                print(f"RECONCILIATE ON EMAIL: https://bar.pc-est-magique.fr/user/{bar_user.username} AND {pceen}")
            elif (
                pceen := full_name_mapping.get(unidecode(f"{bar_user.first_name} {bar_user.last_name}".lower()))
            ) and input(
                f"Réconcilier https://bar.pc-est-magique.fr/user/{bar_user.username} et {pceen} ? (y/n) > "
            ).lower() == "y":
                print("RECONCILIATE ON FULL NAME")

            else:
                print(f"CREATE USER: https://bar.pc-est-magique.fr/user/{bar_user.username}")
                pceen = PCeen(
                    username=new_username(bar_user.first_name, bar_user.last_name),
                    nom=bar_user.last_name.title(),
                    prenom=bar_user.first_name.title(),
                    email=bar_user.email,
                    activated=False,
                )
                db.session.add(pceen)
                db.session.flush()

            self.user_id_mapping[bar_user.id] = pceen.id
            self.user_username_mapping[bar_user.username] = pceen.id
            self.user_balances[pceen] = bar_user.balance

            pceen.promo = bar_user.grad_class
            pceen.bar_nickname = bar_user.nickname
            pceen.bar_balance = bar_user.balance
            pceen.bar_deposit = bar_user.deposit
            if not pceen._password_hash:
                pceen._password_hash = bar_user.password_hash

            if pceen.promo and pceen.promo > 136:
                self._grant_role(self.student_role, pceen)
            else:
                self._grant_role(self.bar_user_role, pceen)
            if bar_user.is_bartender or bar_user.is_admin:
                self._grant_role(self.barman_role, pceen)
            elif bar_user.is_observer:
                self._grant_role(self.observer_role, pceen)
            if pceen.promo and pceen.promo >= 100:
                self._grant_role(self.promos_roles[pceen.promo], pceen)

        deleted_bar_user = PCeen.query.filter_by(email="noreply@pc-est-magique.fr").one_or_none()
        if not deleted_bar_user:
            deleted_bar_user = PCeen(
                username="_deleted",
                nom="Bar User",
                prenom="Deleted",
                email="noreply@pc-est-magique.fr",
                bar_balance=0,
                bar_deposit=False,
                activated=False,
            )
            db.session.add(deleted_bar_user)
            db.session.flush()
            self._grant_role(self.bar_user_role, deleted_bar_user)

        self.user_id_mapping[None] = deleted_bar_user.id
        self.user_balances[deleted_bar_user] = 0

    def create_items(self):
        self.item_id_mapping = {}

        for bar_item in tqdm.tqdm(self.bar_session.query(self.Item).all(), "items"):
            item = BarItem(
                name=bar_item.name,
                price=bar_item.price,
                is_alcohol=bar_item.is_alcohol,
                is_quantifiable=bar_item.is_quantifiable,
                quantity=bar_item.quantity if bar_item.is_quantifiable else None,
                favorite_index=10 if bar_item.is_favorite else 0,
                archived=False,
            )
            db.session.add(item)
            db.session.flush()
            self.item_id_mapping[bar_item.id] = item.id

    def create_transactions(self):
        self.transaction_id_mapping = {}

        for bar_transaction in tqdm.tqdm(
            self.bar_session.query(self.Transaction).order_by(self.Transaction.date).all(), "transactions"
        ):
            if bar_transaction.type == "Top up":
                transaction = BarTransaction(
                    _client_id=self.user_id_mapping[bar_transaction.client_id],
                    _barman_id=self.user_username_mapping[bar_transaction.barman],
                    date=bar_transaction.date,
                    type=BarTransactionType.top_up,
                    balance_change=bar_transaction.balance_change,
                    is_reverted=bar_transaction.is_reverted,
                )
                db.session.add(transaction)
                db.session.flush()
                transaction._update_linked_objects(revert=False)
                self.transaction_id_mapping[bar_transaction.id] = transaction

            elif bar_transaction.type.startswith("Pay "):
                item_id = self.item_id_mapping.get(bar_transaction.item_id)
                if not item_id:
                    item = BarItem(
                        name=bar_transaction.type.removeprefix("Pay ").title(),
                        price=-bar_transaction.balance_change,
                        is_alcohol=False,
                        is_quantifiable=False,
                        favorite_index=0,
                        archived=True,
                    )
                    db.session.add(item)
                    db.session.flush()
                    item_id = item.id
                    self.item_id_mapping[bar_transaction.item_id] = item_id

                transaction = BarTransaction(
                    _client_id=self.user_id_mapping[bar_transaction.client_id],
                    _barman_id=self.user_username_mapping[bar_transaction.barman],
                    date=bar_transaction.date,
                    type=BarTransactionType.pay_item,
                    _item_id=item_id,
                    balance_change=bar_transaction.balance_change,
                    is_reverted=bar_transaction.is_reverted,
                )
                db.session.add(transaction)
                db.session.flush()
                transaction._update_linked_objects(revert=False)
                self.transaction_id_mapping[bar_transaction.id] = transaction

            elif bar_transaction.type.startswith("Revert #"):
                reverted_transaction = self.transaction_id_mapping.get(
                    int(bar_transaction.type.removeprefix("Revert #"))
                )
                if not reverted_transaction:
                    print("WARNING you piece of shit")
                    continue

                reverted_transaction.is_reverted = True
                reverted_transaction.revert_date = bar_transaction.date
                reverted_transaction._reverter_id = self.user_username_mapping[bar_transaction.barman]

            else:
                print("WARNING 2 you piece of shit")

    def restore_balances(self):
        print("Restoring balances...")
        for pceen, balance in self.user_balances.items():
            pceen.bar_balance = balance


@loggers.log_exception(reraise=True)
def main():
    if input("Really run this script? IT SHOULD ONLY BE RUN ONCE. (yes/no) > ").lower() != "yes":
        print("Mission aborted")
        return

    Importer().run()
    print("Import succeed!")
