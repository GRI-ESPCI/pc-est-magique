-- Script générique pour migrer toutes les informations d'un compte PEM vers un autre compte. Il transfère toutes les informations, l'historique des transactions, balance bar...
DO $$
DECLARE
    old_id_here INT := 1874;     -- ID du compte à supprimer
    target_id_here INT := 1781;  -- ID du compte vers lequel migrer les données
BEGIN

-- Suppression des rôles en doublon
DELETE FROM _pceen_role_at old_role
USING _pceen_role_at target_role
WHERE old_role._pceen_id = old_id_here
  AND target_role._pceen_id = target_id_here
  AND old_role._role_id = target_role._role_id;

-- Ajout des rôles restants
UPDATE _pceen_role_at
SET _pceen_id = target_id_here
WHERE _pceen_id = old_id_here;

-- Gestion spéciale du bar_daily_data (au cas où les deux comptes ont une activité sur le même jour)
UPDATE bar_daily_data target_data
SET 
    balance_change = target_data.balance_change + old_data.balance_change,
    items_bought_count = target_data.items_bought_count + old_data.items_bought_count,
    alcohol_bought_count = target_data.alcohol_bought_count + old_data.alcohol_bought_count,
    total_spent = target_data.total_spent + old_data.total_spent
FROM bar_daily_data old_data
WHERE target_data._pceen_id = target_id_here
  AND old_data._pceen_id = old_id_here
  AND target_data.date = old_data.date;

-- Nettoyage
DELETE FROM bar_daily_data old_data
USING bar_daily_data target_data
WHERE old_data._pceen_id = old_id_here
  AND target_data._pceen_id = target_id_here
  AND target_data.date = old_data.date;


UPDATE bar_daily_data
SET _pceen_id = target_id_here
WHERE _pceen_id = old_id_here;

-- Migration de la balance
UPDATE pceen AS target
SET bar_balance = COALESCE(target.bar_balance, 0) + COALESCE(old.bar_balance, 0)
FROM pceen AS old
WHERE target.id = target_id_here 
  AND old.id = old_id_here;

UPDATE pceen
SET bar_balance = 0
WHERE id = old_id_here;


-- Tout le reste
UPDATE bar_transaction SET _client_id = target_id_here WHERE _client_id = old_id_here;
UPDATE bar_transaction SET _barman_id = target_id_here WHERE _barman_id = old_id_here;
UPDATE bar_transaction SET _reverter_id = target_id_here WHERE _reverter_id = old_id_here;

UPDATE subscription SET _pceen_id = target_id_here WHERE _pceen_id = old_id_here;
UPDATE payment SET _pceen_id = target_id_here WHERE _pceen_id = old_id_here;
UPDATE ban SET _pceen_id = target_id_here WHERE _pceen_id = old_id_here;
UPDATE device SET _pceen_id = target_id_here WHERE _pceen_id = old_id_here;
UPDATE club_q_voeu SET _pceen_id = target_id_here WHERE _pceen_id = old_id_here;
UPDATE order_panier_bio SET _pceen_id = target_id_here WHERE _pceen_id = old_id_here;
UPDATE rental SET _pceen_id = target_id_here WHERE _pceen_id = old_id_here;
UPDATE photo SET _author_id = target_id_here WHERE _author_id = old_id_here;

-- Suppression de l'ancien compte
DELETE FROM pceen WHERE id = old_id_here;

END $$;