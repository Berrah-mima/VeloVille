-- Comptes de démonstration VéloVille. À exécuter après sql/schema.sql.
-- Les deux comptes ont le mot de passe de formation Formation2026!.
-- Seuls des hachages bcrypt sont conservés dans la base.

INSERT INTO utilisateur (username, mot_de_passe_hash, role) VALUES
  (
    'exploitant01',
    '$2b$12$ej20gmOU7l.L1SOku8K66uV2PMETEc5ub8A.PM.Y.7QGHEvUlBkEi',
    'exploitant'
  ),
  (
    'direction01',
    '$2b$12$l8m1OACxjxS8rOcvTBH7oOuxkXEfMed1KAcZIZDxGZPLvBmR4w8We',
    'direction'
  )
ON CONFLICT (username) DO UPDATE
SET mot_de_passe_hash = EXCLUDED.mot_de_passe_hash,
    role = EXCLUDED.role;
