"""initial

Revision ID: 001
Revises:
Create Date: 2025-01-01 00:00:00
"""
from alembic import op
import sqlalchemy as sa

revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Users
    op.create_table(
        'users',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('username', sa.String(100), unique=True, nullable=False),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(200), nullable=False, server_default=''),
        sa.Column('role', sa.Enum('admin', 'dispatcher', 'accountant', name='userrole'), nullable=False),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('employee_id', sa.Integer, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_users_username', 'users', ['username'])

    # Employees
    op.create_table(
        'employees',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('full_name', sa.String(200), nullable=False),
        sa.Column('employee_type', sa.Enum('driver', 'operator', name='employeetype'), nullable=False),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # Carriers
    op.create_table(
        'carriers',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(200), nullable=False, unique=True),
        sa.Column('price_per_trip', sa.Numeric(12, 2), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # Buyers
    op.create_table(
        'buyers',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(200), nullable=False, unique=True),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # Materials
    op.create_table(
        'materials',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(200), nullable=False, unique=True),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # Vehicles
    op.create_table(
        'vehicles',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('plate_number', sa.String(50), nullable=False, unique=True),
        sa.Column('vehicle_type', sa.Enum('truck', name='vehicletype'), nullable=False, server_default='truck'),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # Excavators
    op.create_table(
        'excavators',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(200), nullable=False, unique=True),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # Trip Invoices
    op.create_table(
        'trip_invoices',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('trip_date', sa.Date, nullable=False),
        sa.Column('driver_id', sa.Integer, sa.ForeignKey('employees.id'), nullable=False),
        sa.Column('vehicle_id', sa.Integer, sa.ForeignKey('vehicles.id'), nullable=False),
        sa.Column('carrier_id', sa.Integer, sa.ForeignKey('carriers.id'), nullable=False),
        sa.Column('buyer_id', sa.Integer, sa.ForeignKey('buyers.id'), nullable=False),
        sa.Column('material_id', sa.Integer, sa.ForeignKey('materials.id'), nullable=False),
        sa.Column('invoice_number', sa.String(100), nullable=True),
        sa.Column('trip_price_fixed', sa.Numeric(12, 2), nullable=False),
        sa.Column('status', sa.Enum('draft', 'confirmed', 'void', 'locked', name='tripstatus'), nullable=False, server_default='draft'),
        sa.Column('created_by', sa.Integer, sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint('invoice_number', 'trip_date', 'vehicle_id', name='uq_invoice_trip_vehicle'),
    )
    op.create_index('ix_trip_invoices_trip_date', 'trip_invoices', ['trip_date'])
    op.create_index('ix_trip_invoices_status', 'trip_invoices', ['status'])

    # Excavator Sessions
    op.create_table(
        'excavator_sessions',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('work_date', sa.Date, nullable=False),
        sa.Column('operator_id', sa.Integer, sa.ForeignKey('employees.id'), nullable=False),
        sa.Column('excavator_id', sa.Integer, sa.ForeignKey('excavators.id'), nullable=False),
        sa.Column('buyer_id', sa.Integer, sa.ForeignKey('buyers.id'), nullable=True),
        sa.Column('start_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.Enum('open', 'closed', 'locked', name='sessionstatus'), nullable=False, server_default='open'),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('created_by', sa.Integer, sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_excavator_sessions_work_date', 'excavator_sessions', ['work_date'])
    op.create_index('ix_excavator_sessions_status', 'excavator_sessions', ['status'])

    # Payroll Periods
    op.create_table(
        'payroll_periods',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('month', sa.String(7), nullable=False, unique=True),
        sa.Column('status', sa.Enum('open', 'closed', 'paid', name='periodstatus'), nullable=False, server_default='open'),
        sa.Column('closed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('closed_by', sa.Integer, sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_payroll_periods_month', 'payroll_periods', ['month'])

    # Payroll Lines
    op.create_table(
        'payroll_lines',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('period_id', sa.Integer, sa.ForeignKey('payroll_periods.id'), nullable=False),
        sa.Column('employee_id', sa.Integer, sa.ForeignKey('employees.id'), nullable=False),
        sa.Column('employee_type', sa.String(20), nullable=False),
        sa.Column('trips_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('trips_amount', sa.Numeric(14, 2), nullable=False, server_default='0'),
        sa.Column('hours_total', sa.Numeric(10, 2), nullable=False, server_default='0'),
        sa.Column('hours_amount', sa.Numeric(14, 2), nullable=False, server_default='0'),
        sa.Column('total_amount', sa.Numeric(14, 2), nullable=False, server_default='0'),
    )
    op.create_index('ix_payroll_lines_period_id', 'payroll_lines', ['period_id'])

    # Payment Records
    op.create_table(
        'payment_records',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('period_id', sa.Integer, sa.ForeignKey('payroll_periods.id'), nullable=False),
        sa.Column('employee_id', sa.Integer, sa.ForeignKey('employees.id'), nullable=False),
        sa.Column('paid_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('paid_by', sa.Integer, sa.ForeignKey('users.id'), nullable=False),
        sa.Column('note', sa.Text, nullable=True),
    )

    # Audit Log
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id'), nullable=False),
        sa.Column('action', sa.String(50), nullable=False),
        sa.Column('entity_type', sa.String(100), nullable=False),
        sa.Column('entity_id', sa.Integer, nullable=False),
        sa.Column('old_data', sa.JSON, nullable=True),
        sa.Column('new_data', sa.JSON, nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_audit_logs_timestamp', 'audit_logs', ['timestamp'])

    # System Settings
    op.create_table(
        'system_settings',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('key', sa.String(100), nullable=False, unique=True),
        sa.Column('value', sa.String(500), nullable=False, server_default=''),
    )


def downgrade():
    op.drop_table('system_settings')
    op.drop_table('audit_logs')
    op.drop_table('payment_records')
    op.drop_table('payroll_lines')
    op.drop_table('payroll_periods')
    op.drop_table('excavator_sessions')
    op.drop_table('trip_invoices')
    op.drop_table('excavators')
    op.drop_table('vehicles')
    op.drop_table('materials')
    op.drop_table('buyers')
    op.drop_table('carriers')
    op.drop_table('employees')
    op.drop_table('users')
