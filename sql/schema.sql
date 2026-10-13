-- Schéma rejouable PostgreSQL 14+.
CREATE TABLE IF NOT EXISTS station (
    station_id VARCHAR(10) PRIMARY KEY,
    nom TEXT NOT NULL,
    commune TEXT NOT NULL,
    capacite INTEGER NOT NULL CHECK (capacite > 0),
    latitude NUMERIC(8,5) NOT NULL CHECK (latitude BETWEEN -90 AND 90),
    longitude NUMERIC(8,5) NOT NULL CHECK (longitude BETWEEN -180 AND 180),
    date_mise_en_service DATE NOT NULL
);

CREATE TABLE IF NOT EXISTS trajet (
    trajet_id VARCHAR(12) PRIMARY KEY,
    velo_id VARCHAR(8) NOT NULL,
    depart_horodatage TIMESTAMP NOT NULL,
    station_depart VARCHAR(10) NOT NULL REFERENCES station(station_id),
    station_arrivee VARCHAR(10) REFERENCES station(station_id),
    duree_secondes INTEGER NOT NULL CHECK (duree_secondes > 0),
    type_usager VARCHAR(20) NOT NULL CHECK (type_usager IN ('abonne', 'occasionnel')),
    usager_ref VARCHAR(9),
    CONSTRAINT ck_trajet_usager_ref CHECK (
        (type_usager = 'abonne' AND usager_ref IS NOT NULL)
        OR (type_usager = 'occasionnel' AND usager_ref IS NULL)
    )
);

CREATE TABLE IF NOT EXISTS incident (
    incident_id VARCHAR(12) PRIMARY KEY,
    date_signalement TIMESTAMP NOT NULL,
    cible VARCHAR(10) NOT NULL CHECK (cible IN ('velo', 'station')),
    velo_id VARCHAR(8),
    station_id VARCHAR(10) REFERENCES station(station_id),
    type_incident TEXT NOT NULL,
    statut VARCHAR(20) NOT NULL CHECK (statut IN ('ouvert', 'en_cours', 'resolu')),
    date_resolution TIMESTAMP,
    technicien TEXT,
    CONSTRAINT ck_incident_cible_reference CHECK (
        (cible = 'velo' AND velo_id IS NOT NULL AND station_id IS NULL)
        OR (cible = 'station' AND velo_id IS NULL AND station_id IS NOT NULL)
    ),
    CONSTRAINT ck_incident_date_resolution_statut CHECK (
        (statut = 'resolu' AND date_resolution IS NOT NULL)
        OR (statut <> 'resolu' AND date_resolution IS NULL)
    ),
    CONSTRAINT ck_incident_dates_coherentes CHECK (
        date_resolution IS NULL OR date_resolution >= date_signalement
    )
);

CREATE TABLE IF NOT EXISTS utilisateur (
    id_utilisateur SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    mot_de_passe_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('exploitant', 'direction'))
);

CREATE INDEX IF NOT EXISTS idx_station_commune_station_id ON station (commune, station_id);
CREATE INDEX IF NOT EXISTS idx_trajet_depart_horodatage ON trajet (depart_horodatage);
CREATE INDEX IF NOT EXISTS idx_trajet_station_arrivee ON trajet (station_arrivee);
CREATE INDEX IF NOT EXISTS idx_incident_statut_date ON incident (statut, date_signalement DESC);
