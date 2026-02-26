-- =============================================
-- Clear all business data (keep admin user + table structure)
-- Run on server: PGPASSWORD=logist_secret psql -h localhost -U logist logist_zp -f /home/logist_zp/clear_data.sql
-- =============================================

TRUNCATE TABLE delivery_acts CASCADE;
TRUNCATE TABLE salary_advances CASCADE;
TRUNCATE TABLE payroll_lines CASCADE;
TRUNCATE TABLE payroll_periods CASCADE;
TRUNCATE TABLE audit_logs CASCADE;
TRUNCATE TABLE trip_invoices CASCADE;
TRUNCATE TABLE machinery_sessions CASCADE;
TRUNCATE TABLE machinery_tariffs CASCADE;
TRUNCATE TABLE object_places CASCADE;
TRUNCATE TABLE system_settings CASCADE;

-- References
TRUNCATE TABLE machinery CASCADE;
TRUNCATE TABLE vehicles CASCADE;
TRUNCATE TABLE materials CASCADE;
TRUNCATE TABLE carriers CASCADE;
TRUNCATE TABLE buyers CASCADE;
TRUNCATE TABLE employees CASCADE;

-- Delete all users except admin
DELETE FROM users WHERE username != 'admin';

SELECT 'All data cleared! Admin user preserved.' AS result;
