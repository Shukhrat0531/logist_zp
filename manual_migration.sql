-- Rename tables and columns
ALTER TABLE excavators RENAME TO machinery;
ALTER TABLE excavator_sessions RENAME TO machinery_sessions;
ALTER TABLE machinery_sessions RENAME COLUMN excavator_id TO machinery_id;

-- Create new tables
CREATE TABLE IF NOT EXISTS salary_advances (
    id SERIAL PRIMARY KEY,
    employee_id INTEGER NOT NULL REFERENCES employees(id),
    amount NUMERIC(12, 2) NOT NULL,
    date DATE NOT NULL DEFAULT CURRENT_DATE,
    comment VARCHAR(500),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS object_places (
    id SERIAL PRIMARY KEY,
    buyer_id INTEGER NOT NULL REFERENCES buyers(id),
    name VARCHAR(200) NOT NULL,
    comment VARCHAR(500),
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS delivery_acts (
    id SERIAL PRIMARY KEY,
    buyer_id INTEGER NOT NULL REFERENCES buyers(id),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    total_trips INTEGER DEFAULT 0,
    total_volume NUMERIC(12, 2) DEFAULT 0,
    status VARCHAR DEFAULT 'open',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Add columns to existing tables
ALTER TABLE machinery_sessions ADD COLUMN IF NOT EXISTS hourly_rate INTEGER DEFAULT 0 NOT NULL;

ALTER TABLE trip_invoices ADD COLUMN IF NOT EXISTS fuel_liters NUMERIC(10, 2);
ALTER TABLE trip_invoices ADD COLUMN IF NOT EXISTS volume_m3 NUMERIC(10, 2);
ALTER TABLE trip_invoices ADD COLUMN IF NOT EXISTS place_id INTEGER REFERENCES object_places(id);
ALTER TABLE trip_invoices ADD COLUMN IF NOT EXISTS delivery_act_id INTEGER REFERENCES delivery_acts(id);

ALTER TABLE payroll_lines ADD COLUMN IF NOT EXISTS manual_correction NUMERIC(12, 2) DEFAULT 0 NOT NULL;
ALTER TABLE payroll_lines ADD COLUMN IF NOT EXISTS is_paid BOOLEAN DEFAULT FALSE NOT NULL;
