#!/usr/bin/env bash
# Actualiza la línea "Última actualización" del README con la fecha de hoy.
set -euo pipefail

declare -A MESES=(
  ["01"]="enero" ["02"]="febrero" ["03"]="marzo" ["04"]="abril"
  ["05"]="mayo" ["06"]="junio" ["07"]="julio" ["08"]="agosto"
  ["09"]="septiembre" ["10"]="octubre" ["11"]="noviembre" ["12"]="diciembre"
)

NEW_DATE="$(date +"%d") de ${MESES[$(date +"%m")]} de $(date +"%Y")"
sed -i "s/Última actualización: .*/Última actualización: ${NEW_DATE}<\/sub>/" README.md
