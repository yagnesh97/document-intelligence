#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FIXTURE_DIR="${ROOT_DIR}/tests/fixtures/pdf/sample-files"
REPO_URL="https://github.com/py-pdf/sample-files.git"

if [[ -d "${FIXTURE_DIR}/.git" ]]; then
    echo "PDF sample repository already exists:"
    echo "  ${FIXTURE_DIR}"
    exit 0
fi

mkdir -p "$(dirname "${FIXTURE_DIR}")"

echo "Cloning PDF sample files..."
git clone --depth 1 "${REPO_URL}" "${FIXTURE_DIR}"

echo
echo "PDF sample files downloaded to:"
echo "  ${FIXTURE_DIR}"