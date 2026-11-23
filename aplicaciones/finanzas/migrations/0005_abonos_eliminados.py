"""
Eliminar un pago o abono que quedó mal (23-nov-2026).

- Tabla `abono_eliminado`: copia del abono, quién lo eliminó, cuándo y por qué.
- `fn_abono_inmutable` sigue rechazando cualquier cambio y cualquier borrado,
  salvo uno: el del último abono de su cuenta, cuando la aplicación lo
  autoriza en la misma transacción con
  `set_config('contanika.eliminar_abono', '<id_abono>', true)`.
- `trg_abono_estado_tras_eliminar` (AFTER DELETE): recalcula el estado de
  pago de la cuenta (Pendiente, Abonada o Vencida).
"""

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

PERMITIR_BORRAR_ULTIMO = """
CREATE OR REPLACE FUNCTION fn_abono_inmutable() RETURNS trigger AS $$
BEGIN
    IF TG_OP = 'DELETE'
       AND current_setting('contanika.eliminar_abono', true) = OLD.id_abono::text
       AND NOT EXISTS (
           SELECT 1 FROM abono
            WHERE id_cuenta_cobro = OLD.id_cuenta_cobro
              AND id_abono > OLD.id_abono
       ) THEN
        RETURN OLD;
    END IF;
    RAISE EXCEPTION 'Los abonos no se modifican ni se eliminan: conservan la trazabilidad de la cartera.'
        USING ERRCODE = 'restrict_violation';
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION fn_abono_estado_tras_eliminar() RETURNS trigger AS $$
DECLARE
    v_hoy date := (now() AT TIME ZONE 'America/Bogota')::date;
BEGIN
    UPDATE cuenta_cobro c
       SET estado_pago = CASE
               WHEN c.fecha_vencimiento_pago < v_hoy THEN 'Vencida'
               WHEN EXISTS (SELECT 1 FROM abono a WHERE a.id_cuenta_cobro = c.id_cuenta_cobro) THEN 'Abonada'
               ELSE 'Pendiente'
           END
     WHERE c.id_cuenta_cobro = OLD.id_cuenta_cobro;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_abono_estado_tras_eliminar
    AFTER DELETE ON abono
    FOR EACH ROW EXECUTE FUNCTION fn_abono_estado_tras_eliminar();
"""

VOLVER_A_INMUTABLE = """
DROP TRIGGER IF EXISTS trg_abono_estado_tras_eliminar ON abono;
DROP FUNCTION IF EXISTS fn_abono_estado_tras_eliminar();

CREATE OR REPLACE FUNCTION fn_abono_inmutable() RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'Los abonos no se modifican ni se eliminan: conservan la trazabilidad de la cartera.'
        USING ERRCODE = 'restrict_violation';
END;
$$ LANGUAGE plpgsql;
"""


class Migration(migrations.Migration):
    dependencies = [
        ("clientes", "0008_ampliar_obligaciones_dian"),
        ("finanzas", "0004_disparadores_abono"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="AbonoEliminado",
            fields=[
                ("id_abono_eliminado", models.AutoField(primary_key=True, serialize=False)),
                ("numero_cuenta", models.PositiveIntegerField()),
                ("fecha_abono", models.DateField()),
                ("monto", models.DecimalField(decimal_places=2, max_digits=12)),
                ("metodo_pago", models.CharField(blank=True, max_length=40)),
                ("registrado_por", models.CharField(max_length=150)),
                ("fecha_eliminacion", models.DateTimeField(auto_now_add=True)),
                ("motivo", models.TextField()),
                (
                    "cliente",
                    models.ForeignKey(
                        db_column="id_cliente",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="abonos_eliminados",
                        to="clientes.cliente",
                    ),
                ),
                (
                    "cuenta_cobro",
                    models.ForeignKey(
                        blank=True,
                        db_column="id_cuenta_cobro",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="abonos_eliminados",
                        to="finanzas.cuentacobro",
                    ),
                ),
                (
                    "eliminado_por",
                    models.ForeignKey(
                        db_column="id_usuario_elimino",
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="abonos_eliminados",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "abono eliminado",
                "verbose_name_plural": "abonos eliminados",
                "db_table": "abono_eliminado",
                "ordering": ["-fecha_eliminacion", "-id_abono_eliminado"],
            },
        ),
        migrations.RunSQL(sql=PERMITIR_BORRAR_ULTIMO, reverse_sql=VOLVER_A_INMUTABLE),
    ]
