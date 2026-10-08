"""
Disparadores (triggers) de PostgreSQL sobre la tabla `abono` (Módulo 6).

Es el disparador exigido por la guía del proyecto: la trazabilidad de la
cartera la garantiza la base de datos, no solo la aplicación.

- `trg_abono_calcular_saldo` (BEFORE INSERT): bloquea la cuenta de cobro,
  calcula el saldo anterior (valor total menos lo ya abonado) y el saldo
  resultante, y rechaza montos no positivos o mayores que el saldo.
- `trg_abono_actualizar_estado` (AFTER INSERT): deja la cuenta en "Pagada",
  "Vencida" (si ya pasó su fecha de pago y queda saldo) o "Abonada".
- `trg_abono_inmutable` (BEFORE UPDATE OR DELETE): los abonos no se
  modifican ni se eliminan una vez registrados.
"""

from django.db import migrations

CREAR_DISPARADORES = """
CREATE OR REPLACE FUNCTION fn_abono_calcular_saldo() RETURNS trigger AS $$
DECLARE
    v_valor_total numeric(12, 2);
    v_abonado numeric(12, 2);
BEGIN
    IF NEW.monto IS NULL OR NEW.monto <= 0 THEN
        RAISE EXCEPTION 'El monto del abono debe ser mayor que cero.'
            USING ERRCODE = 'check_violation';
    END IF;

    -- Bloquea la cuenta para que dos abonos simultáneos no calculen el mismo saldo.
    SELECT valor_total INTO v_valor_total
      FROM cuenta_cobro
     WHERE id_cuenta_cobro = NEW.id_cuenta_cobro
       FOR UPDATE;

    SELECT COALESCE(SUM(monto), 0) INTO v_abonado
      FROM abono
     WHERE id_cuenta_cobro = NEW.id_cuenta_cobro;

    NEW.saldo_anterior := v_valor_total - v_abonado;
    IF NEW.monto > NEW.saldo_anterior THEN
        RAISE EXCEPTION 'El abono supera el saldo pendiente de la cuenta (%).', NEW.saldo_anterior
            USING ERRCODE = 'check_violation';
    END IF;
    NEW.saldo_resultante := NEW.saldo_anterior - NEW.monto;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_abono_calcular_saldo
    BEFORE INSERT ON abono
    FOR EACH ROW EXECUTE FUNCTION fn_abono_calcular_saldo();

CREATE OR REPLACE FUNCTION fn_abono_actualizar_estado_cuenta() RETURNS trigger AS $$
BEGIN
    UPDATE cuenta_cobro
       SET estado_pago = CASE
               WHEN NEW.saldo_resultante = 0 THEN 'Pagada'
               WHEN fecha_vencimiento_pago < (now() AT TIME ZONE 'America/Bogota')::date THEN 'Vencida'
               ELSE 'Abonada'
           END
     WHERE id_cuenta_cobro = NEW.id_cuenta_cobro;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_abono_actualizar_estado
    AFTER INSERT ON abono
    FOR EACH ROW EXECUTE FUNCTION fn_abono_actualizar_estado_cuenta();

CREATE OR REPLACE FUNCTION fn_abono_inmutable() RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'Los abonos no se modifican ni se eliminan: conservan la trazabilidad de la cartera.'
        USING ERRCODE = 'restrict_violation';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_abono_inmutable
    BEFORE UPDATE OR DELETE ON abono
    FOR EACH ROW EXECUTE FUNCTION fn_abono_inmutable();
"""

ELIMINAR_DISPARADORES = """
DROP TRIGGER IF EXISTS trg_abono_inmutable ON abono;
DROP TRIGGER IF EXISTS trg_abono_actualizar_estado ON abono;
DROP TRIGGER IF EXISTS trg_abono_calcular_saldo ON abono;
DROP FUNCTION IF EXISTS fn_abono_inmutable();
DROP FUNCTION IF EXISTS fn_abono_actualizar_estado_cuenta();
DROP FUNCTION IF EXISTS fn_abono_calcular_saldo();
"""


class Migration(migrations.Migration):
    dependencies = [
        ("finanzas", "0003_envios_y_cobro_automatico"),
    ]

    operations = [
        migrations.RunSQL(sql=CREAR_DISPARADORES, reverse_sql=ELIMINAR_DISPARADORES),
    ]
