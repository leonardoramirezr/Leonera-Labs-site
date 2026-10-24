#!/usr/bin/env bash
# Actualiza la rama gh-pages, que es la que sirve GitHub Pages con "Deploy from a branch":
#   - el contenido de main se copia a la raíz del sitio;
#   - el contenido del último commit de cada rama se copia a previews/<rama>/;
#   - al borrar una rama, se quita su carpeta de previews.
#
# Uso, desde la raíz del repositorio con todas las ramas descargadas (fetch-depth: 0):
#   tools/publicar_pages.sh publicar <rama> <commit>
#   tools/publicar_pages.sh borrar <rama>
set -euo pipefail

accion=${1:?Falta la acción: publicar o borrar}
rama=${2:?Falta el nombre de la rama}
commit=${3:-}

raiz=$(pwd)
# Solo se publica el sitio: no el workflow ni las herramientas del repositorio.
excluir=(':(exclude).github' ':(exclude)tools')
sitio="$(mktemp -d)/gh-pages"
trap 'cd "$raiz" && git worktree remove --force "$sitio" >/dev/null 2>&1 || true' EXIT

if git rev-parse --verify --quiet origin/gh-pages >/dev/null; then
  git worktree add --quiet -B gh-pages "$sitio" origin/gh-pages
else
  git worktree add --quiet --orphan -b gh-pages "$sitio"
fi
cd "$sitio"

case "$accion" in
  publicar)
    commit=${commit:?Falta el commit a publicar}
    rm -rf "previews/$rama"
    mkdir -p "previews/$rama"
    git archive "$commit" -- . "${excluir[@]}" | tar -x -C "previews/$rama"

    if [ "$rama" = main ]; then
      find . -mindepth 1 -maxdepth 1 ! -name .git ! -name previews -exec rm -rf {} +
      git archive "$commit" -- . "${excluir[@]}" ':(exclude)previews' | tar -x
    fi
    mensaje="Publica $rama (${commit:0:7})"
    ;;
  borrar)
    rm -rf "previews/$rama"
    mensaje="Borra el preview de $rama"
    ;;
  *)
    echo "Acción desconocida: $accion" >&2
    exit 1
    ;;
esac

# GitHub Pages ejecuta Jekyll por defecto; .nojekyll lo desactiva para servir el sitio tal cual.
touch .nojekyll
git add -A

if git diff --cached --quiet; then
  echo "gh-pages ya estaba al día para $rama"
  exit 0
fi

git -c user.name="github-actions[bot]" \
    -c user.email="41898282+github-actions[bot]@users.noreply.github.com" \
    commit --quiet -m "$mensaje"
git push --quiet origin HEAD:refs/heads/gh-pages
echo "$mensaje"
