-- Nécessaire pour la recherche "fuzzy" des pcéens
CREATE EXTENSION IF NOT EXISTS unaccent;

BEGIN;

-- Ce script est une requête SQL pour migrer chaque compte @espci.psl.eu vers son compte PEM "classique" correspondant. 

ALTER TABLE pceen ADD IF NOT EXISTS espci_email VARCHAR(255);

-- Copie de l'email pcéen sur le compte principal
UPDATE pceen AS p1
SET espci_email = p2.email
FROM pceen AS p2
WHERE unaccent(LOWER(p1.nom)) = unaccent(LOWER(p2.nom)) 
  AND unaccent(LOWER(p1.prenom)) = unaccent(LOWER(p2.prenom)) 
  AND p1.promo = p2.promo
  AND p1.email NOT LIKE '%@espci.psl.eu' 
  AND p2.email LIKE '%@espci.psl.eu';

SELECT 
    p1.nom, 
    p1.prenom, 
    p1.promo, 
    p1.email AS personal_email, 
    p2.email AS new_espci_email
FROM pceen p1
JOIN pceen p2 
    ON unaccent(LOWER(p1.nom)) = unaccent(LOWER(p2.nom)) 
    AND unaccent(LOWER(p1.prenom)) = unaccent(LOWER(p2.prenom)) 
    AND p1.promo = p2.promo
WHERE p1.email NOT LIKE '%@espci.psl.eu' 
  AND p2.email LIKE '%@espci.psl.eu';

-- Migration du solde du bar (bar_balance) et des informations de profil
-- 1. Ajout du solde de l'ancien compte au compte principal et fusion des profils
UPDATE pceen AS p_prim
SET 
    bar_balance = COALESCE(p_prim.bar_balance, 0) + COALESCE(p_dup.bar_balance, 0),
    bar_nickname = COALESCE(p_prim.bar_nickname, p_dup.bar_nickname),
    sub_state = COALESCE(p_prim.sub_state, p_dup.sub_state),
    discontent = COALESCE(p_prim.discontent, p_dup.discontent),
    is_gri = COALESCE(p_prim.is_gri, false) OR COALESCE(p_dup.is_gri, false),
    bar_deposit = COALESCE(p_prim.bar_deposit, false) OR COALESCE(p_dup.bar_deposit, false)
FROM pceen AS p_dup
WHERE unaccent(LOWER(p_prim.nom)) = unaccent(LOWER(p_dup.nom)) 
  AND unaccent(LOWER(p_prim.prenom)) = unaccent(LOWER(p_dup.prenom)) 
  AND p_prim.promo = p_dup.promo
  AND p_dup.email LIKE '%@espci.psl.eu'
  AND p_dup.espci_email IS NULL
  AND p_prim.email NOT LIKE '%@espci.psl.eu';

-- 2. Mise à zéro du solde de l'ancien compte
UPDATE pceen AS p_dup
SET bar_balance = 0
FROM pceen AS p_prim
WHERE unaccent(LOWER(p_dup.nom)) = unaccent(LOWER(p_prim.nom)) 
  AND unaccent(LOWER(p_dup.prenom)) = unaccent(LOWER(p_prim.prenom)) 
  AND p_dup.promo = p_prim.promo
  AND p_dup.email LIKE '%@espci.psl.eu'
  AND p_dup.espci_email IS NULL
  AND p_prim.email NOT LIKE '%@espci.psl.eu';

-- Migration des données supplémentaires
-- Migration du bar (transactions)
UPDATE bar_transaction AS bt
SET _client_id = p_prim.id
FROM pceen AS p_dup
JOIN pceen AS p_prim ON unaccent(LOWER(p_dup.nom)) = unaccent(LOWER(p_prim.nom)) 
                    AND unaccent(LOWER(p_dup.prenom)) = unaccent(LOWER(p_prim.prenom)) 
                    AND p_dup.promo = p_prim.promo
WHERE bt._client_id = p_dup.id
  AND p_dup.email LIKE '%@espci.psl.eu'
  AND p_dup.espci_email IS NULL
  AND p_prim.email NOT LIKE '%@espci.psl.eu';

UPDATE subscription AS s
SET _pceen_id = p_prim.id
FROM pceen AS p_dup
JOIN pceen AS p_prim ON unaccent(LOWER(p_dup.nom)) = unaccent(LOWER(p_prim.nom)) 
                    AND unaccent(LOWER(p_dup.prenom)) = unaccent(LOWER(p_prim.prenom)) 
                    AND p_dup.promo = p_prim.promo
WHERE s._pceen_id = p_dup.id
  AND p_dup.email LIKE '%@espci.psl.eu'
  AND p_dup.espci_email IS NULL
  AND p_prim.email NOT LIKE '%@espci.psl.eu';

UPDATE payment AS p
SET _pceen_id = p_prim.id
FROM pceen AS p_dup
JOIN pceen AS p_prim ON unaccent(LOWER(p_dup.nom)) = unaccent(LOWER(p_prim.nom)) 
                    AND unaccent(LOWER(p_dup.prenom)) = unaccent(LOWER(p_prim.prenom)) 
                    AND p_dup.promo = p_prim.promo
WHERE p._pceen_id = p_dup.id
  AND p_dup.email LIKE '%@espci.psl.eu'
  AND p_dup.espci_email IS NULL
  AND p_prim.email NOT LIKE '%@espci.psl.eu';

UPDATE payment AS p
SET _gri_id = p_prim.id
FROM pceen AS p_dup
JOIN pceen AS p_prim ON unaccent(LOWER(p_dup.nom)) = unaccent(LOWER(p_prim.nom)) 
                    AND unaccent(LOWER(p_dup.prenom)) = unaccent(LOWER(p_prim.prenom)) 
                    AND p_dup.promo = p_prim.promo
WHERE p._gri_id = p_dup.id
  AND p_dup.email LIKE '%@espci.psl.eu'
  AND p_dup.espci_email IS NULL
  AND p_prim.email NOT LIKE '%@espci.psl.eu';

-- Cas pour gérer les doublons
DELETE FROM _pceen_role_at AS pra_dup
USING pceen AS p_dup, 
      pceen AS p_prim, 
      _pceen_role_at AS pra_prim
WHERE pra_dup._pceen_id = p_dup.id
  AND unaccent(LOWER(p_dup.nom)) = unaccent(LOWER(p_prim.nom)) 
  AND unaccent(LOWER(p_dup.prenom)) = unaccent(LOWER(p_prim.prenom)) 
  AND p_dup.promo = p_prim.promo
  AND p_dup.email LIKE '%@espci.psl.eu'
  AND p_dup.espci_email IS NULL
  AND p_prim.email NOT LIKE '%@espci.psl.eu'
  -- Supprimer seulement si le rôle est en doublon
  AND pra_prim._pceen_id = p_prim.id
  AND pra_dup._role_id = pra_prim._role_id;

UPDATE _pceen_role_at AS pra
SET _pceen_id = p_prim.id
FROM pceen AS p_dup
JOIN pceen AS p_prim ON unaccent(LOWER(p_dup.nom)) = unaccent(LOWER(p_prim.nom)) 
                    AND unaccent(LOWER(p_dup.prenom)) = unaccent(LOWER(p_prim.prenom)) 
                    AND p_dup.promo = p_prim.promo
WHERE pra._pceen_id = p_dup.id
  AND p_dup.email LIKE '%@espci.psl.eu'
  AND p_dup.espci_email IS NULL
  AND p_prim.email NOT LIKE '%@espci.psl.eu';

UPDATE ban AS b
SET _pceen_id = p_prim.id
FROM pceen AS p_dup
JOIN pceen AS p_prim ON unaccent(LOWER(p_dup.nom)) = unaccent(LOWER(p_prim.nom)) 
                    AND unaccent(LOWER(p_dup.prenom)) = unaccent(LOWER(p_prim.prenom)) 
                    AND p_dup.promo = p_prim.promo
WHERE b._pceen_id = p_dup.id
  AND p_dup.email LIKE '%@espci.psl.eu'
  AND p_dup.espci_email IS NULL
  AND p_prim.email NOT LIKE '%@espci.psl.eu';

-- Update du bar daily
-- Gestion spéciale pour les cas où les 2 comptes ont une activité au bar ce jour-ci
UPDATE bar_daily_data AS bdd_prim 
SET 
    balance_change = bdd_prim.balance_change + bdd_dup.balance_change,
    items_bought_count = bdd_prim.items_bought_count + bdd_dup.items_bought_count,
    alcohol_bought_count = bdd_prim.alcohol_bought_count + bdd_dup.alcohol_bought_count,
    total_spent = bdd_prim.total_spent + bdd_dup.total_spent
FROM bar_daily_data AS bdd_dup
JOIN pceen AS p_dup ON bdd_dup._pceen_id = p_dup.id
JOIN pceen AS p_prim ON unaccent(LOWER(p_dup.nom)) = unaccent(LOWER(p_prim.nom)) 
                    AND unaccent(LOWER(p_dup.prenom)) = unaccent(LOWER(p_prim.prenom)) 
                    AND p_dup.promo = p_prim.promo
WHERE bdd_prim._pceen_id = p_prim.id
  AND bdd_prim.date = bdd_dup.date 
  AND p_dup.email LIKE '%@espci.psl.eu'
  AND p_dup.espci_email IS NULL
  AND p_prim.email NOT LIKE '%@espci.psl.eu';

DELETE FROM bar_daily_data AS bdd_dup 
USING pceen AS p_dup,
      pceen AS p_prim,
      bar_daily_data AS bdd_prim
WHERE bdd_dup._pceen_id = p_dup.id
  AND unaccent(LOWER(p_dup.nom)) = unaccent(LOWER(p_prim.nom)) 
  AND unaccent(LOWER(p_dup.prenom)) = unaccent(LOWER(p_prim.prenom)) 
  AND p_dup.promo = p_prim.promo
  AND p_dup.email LIKE '%@espci.psl.eu'
  AND p_dup.espci_email IS NULL
  AND p_prim.email NOT LIKE '%@espci.psl.eu'
  AND bdd_prim._pceen_id = p_prim.id
  AND bdd_prim.date = bdd_dup.date;

UPDATE bar_daily_data AS bdd
SET _pceen_id = p_prim.id
FROM pceen AS p_dup
JOIN pceen AS p_prim ON unaccent(LOWER(p_dup.nom)) = unaccent(LOWER(p_prim.nom)) 
                    AND unaccent(LOWER(p_dup.prenom)) = unaccent(LOWER(p_prim.prenom)) 
                    AND p_dup.promo = p_prim.promo
WHERE bdd._pceen_id = p_dup.id
  AND p_dup.email LIKE '%@espci.psl.eu'
  AND p_dup.espci_email IS NULL
  AND p_prim.email NOT LIKE '%@espci.psl.eu';

-- Update des devices
UPDATE device AS d
SET _pceen_id = p_prim.id
FROM pceen AS p_dup
JOIN pceen AS p_prim ON unaccent(LOWER(p_dup.nom)) = unaccent(LOWER(p_prim.nom)) 
                    AND unaccent(LOWER(p_dup.prenom)) = unaccent(LOWER(p_prim.prenom)) 
                    AND p_dup.promo = p_prim.promo
WHERE d._pceen_id = p_dup.id
  AND p_dup.email LIKE '%@espci.psl.eu'
  AND p_dup.espci_email IS NULL
  AND p_prim.email NOT LIKE '%@espci.psl.eu';

UPDATE club_q_voeu AS cqv
SET _pceen_id = p_prim.id
FROM pceen AS p_dup
JOIN pceen AS p_prim ON unaccent(LOWER(p_dup.nom)) = unaccent(LOWER(p_prim.nom)) 
                    AND unaccent(LOWER(p_dup.prenom)) = unaccent(LOWER(p_prim.prenom)) 
                    AND p_dup.promo = p_prim.promo
WHERE cqv._pceen_id = p_dup.id
  AND p_dup.email LIKE '%@espci.psl.eu'
  AND p_dup.espci_email IS NULL
  AND p_prim.email NOT LIKE '%@espci.psl.eu';

UPDATE order_panier_bio AS opb
SET _pceen_id = p_prim.id
FROM pceen AS p_dup
JOIN pceen AS p_prim ON unaccent(LOWER(p_dup.nom)) = unaccent(LOWER(p_prim.nom)) 
                    AND unaccent(LOWER(p_dup.prenom)) = unaccent(LOWER(p_prim.prenom)) 
                    AND p_dup.promo = p_prim.promo
WHERE opb._pceen_id = p_dup.id
  AND p_dup.email LIKE '%@espci.psl.eu'
  AND p_dup.espci_email IS NULL
  AND p_prim.email NOT LIKE '%@espci.psl.eu';

UPDATE rental AS r
SET _pceen_id = p_prim.id
FROM pceen AS p_dup
JOIN pceen AS p_prim ON unaccent(LOWER(p_dup.nom)) = unaccent(LOWER(p_prim.nom)) 
                    AND unaccent(LOWER(p_dup.prenom)) = unaccent(LOWER(p_prim.prenom)) 
                    AND p_dup.promo = p_prim.promo
WHERE r._pceen_id = p_dup.id
  AND p_dup.email LIKE '%@espci.psl.eu'
  AND p_dup.espci_email IS NULL
  AND p_prim.email NOT LIKE '%@espci.psl.eu';

UPDATE photo AS ph
SET _author_id = p_prim.id
FROM pceen AS p_dup
JOIN pceen AS p_prim ON unaccent(LOWER(p_dup.nom)) = unaccent(LOWER(p_prim.nom)) 
                    AND unaccent(LOWER(p_dup.prenom)) = unaccent(LOWER(p_prim.prenom)) 
                    AND p_dup.promo = p_prim.promo
WHERE ph._author_id = p_dup.id
  AND p_dup.email LIKE '%@espci.psl.eu'
  AND p_dup.espci_email IS NULL
  AND p_prim.email NOT LIKE '%@espci.psl.eu';

UPDATE bar_transaction AS bt
SET _barman_id = p_prim.id
FROM pceen AS p_dup
JOIN pceen AS p_prim ON unaccent(LOWER(p_dup.nom)) = unaccent(LOWER(p_prim.nom)) 
                    AND unaccent(LOWER(p_dup.prenom)) = unaccent(LOWER(p_prim.prenom)) 
                    AND p_dup.promo = p_prim.promo
WHERE bt._barman_id = p_dup.id
  AND p_dup.email LIKE '%@espci.psl.eu'
  AND p_dup.espci_email IS NULL
  AND p_prim.email NOT LIKE '%@espci.psl.eu';

UPDATE bar_transaction AS bt
SET _reverter_id = p_prim.id
FROM pceen AS p_dup
JOIN pceen AS p_prim ON unaccent(LOWER(p_dup.nom)) = unaccent(LOWER(p_prim.nom)) 
                    AND unaccent(LOWER(p_dup.prenom)) = unaccent(LOWER(p_prim.prenom)) 
                    AND p_dup.promo = p_prim.promo
WHERE bt._reverter_id = p_dup.id
  AND p_dup.email LIKE '%@espci.psl.eu'
  AND p_dup.espci_email IS NULL
  AND p_prim.email NOT LIKE '%@espci.psl.eu';

-- Déletion finale !!!
DELETE FROM pceen p_dup
WHERE email LIKE '%@espci.psl.eu'
  AND espci_email IS NULL
  AND EXISTS (
      SELECT 1 
      FROM pceen p_prim 
      WHERE unaccent(LOWER(p_prim.nom)) = unaccent(LOWER(p_dup.nom)) 
        AND unaccent(LOWER(p_prim.prenom)) = unaccent(LOWER(p_dup.prenom)) 
        AND p_prim.promo = p_dup.promo 
        AND p_prim.email NOT LIKE '%@espci.psl.eu'
  );

COMMIT;