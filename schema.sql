-- Clean up existing tables to avoid conflicts on deploy
DROP TABLE IF EXISTS hire_sourcing_methods CASCADE;
DROP TABLE IF EXISTS sourcing_methods CASCADE;
DROP TABLE IF EXISTS role_hires CASCADE;
DROP TABLE IF EXISTS productions CASCADE;

-- 1. PRODUCTIONS TABLE
CREATE TABLE productions (
    production_id SERIAL PRIMARY KEY,
    respondent_id VARCHAR(50) NOT NULL,
    production_name VARCHAR(255) NOT NULL,
    respondent_role VARCHAR(100),
    production_type VARCHAR(255),
    shoot_days INT,
    hours_per_day INT,
    total_shoot_hours INT
);

-- 2. ROLE HIRES TABLE
CREATE TABLE role_hires (
    hire_id SERIAL PRIMARY KEY,
    production_id INT REFERENCES productions(production_id) ON DELETE CASCADE,
    role_hired VARCHAR(100) NOT NULL,
    ease_of_finding INT CHECK (ease_of_finding BETWEEN 1 AND 10),
    performance_rating INT CHECK (performance_rating BETWEEN 1 AND 10),
    would_hire_again VARCHAR(10),
    flaked_last_minute VARCHAR(10)
);

-- 3. SOURCING METHODS LOOKUP TABLE
CREATE TABLE sourcing_methods (
    method_id SERIAL PRIMARY KEY,
    method_name VARCHAR(100) UNIQUE NOT NULL
);

-- 4. BRIDGE TABLE (Multi-Valued Sourcing Channels)
CREATE TABLE hire_sourcing_methods (
    hire_id INT REFERENCES role_hires(hire_id) ON DELETE CASCADE,
    method_id INT REFERENCES sourcing_methods(method_id) ON DELETE CASCADE,
    PRIMARY KEY (hire_id, method_id)
);