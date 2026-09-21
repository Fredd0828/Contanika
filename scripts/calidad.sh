#!/usr/bin/env bash
# ==============================================================
# Script único de calidad del proyecto Contanika.
# Ejecuta análisis de estilo, seguridad y pruebas con cobertura.
# Uso: bash scripts/calidad.sh
# ==============================================================
set -e

echo "== 1/5 Ruff: estilo y errores =="
.venv/bin/ruff check .

echo "== 2/5 Ruff: formato =="
.venv/bin/ruff format --check .

echo "== 3/5 Bandit: análisis de seguridad del código =="
.venv/bin/bandit -q -c pyproject.toml -r aplicaciones config

echo "== 4/5 pip-audit: vulnerabilidades en dependencias =="
.venv/bin/pip-audit --skip-editable

echo "== 5/5 Pruebas con cobertura =="
.venv/bin/pytest --cov=aplicaciones --cov-report=term-missing

echo "Calidad verificada correctamente."
