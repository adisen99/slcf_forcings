#!/usr/bin/env bash
# Download the CMIP7 CEDS 0.5-degree (gn) files listed in ESGF wget scripts.
#
# The generated ESGF scripts are intentionally retained unchanged. This wrapper
# filters their embedded manifests to gn files, downloads a small number in
# parallel, resumes .part files, and verifies every SHA-256 checksum.

set -euo pipefail

readonly PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
readonly DEFAULT_MAIN_SCRIPT="$PROJECT_ROOT/data/SLCF_main/wget_script_2026-9-17_22-49-39.sh"
readonly DEFAULT_SUPP_SCRIPT="$PROJECT_ROOT/data/SLCF_supp/wget_script_2026-9-17_22-52-15.sh"

collection="all"
jobs=3
dry_run=0
main_script="$DEFAULT_MAIN_SCRIPT"
supp_script="$DEFAULT_SUPP_SCRIPT"
output_dir=""

usage() {
    cat <<'EOF'
Usage: scripts/download_ceds_gn.sh [options]

Download only the standard 0.5-degree CEDS files (grid ID "gn") from the
current generated ESGF main and supplemental manifests.

Options:
  --collection NAME   main, supplemental, or all (default: all)
  --output-dir PATH   Destination directory (default: data/SLCF_<collection>)
  --jobs N            Concurrent downloads; use 3 by default
  --dry-run           Write manifests and report counts, but do not download
  --main-script PATH  Generated ESGF script for the main collection
  --supp-script PATH  Generated ESGF script for the supplemental collection
  -h, --help          Show this help

Examples:
  # Inspect the requested files without network transfers
  scripts/download_ceds_gn.sh --collection all --dry-run

  # Download each collection separately (recommended)
  scripts/download_ceds_gn.sh --collection main --jobs 3
  scripts/download_ceds_gn.sh --collection supplemental --jobs 3

Downloads are saved as <filename>.part until their SHA-256 checksum passes.
Existing final files are never overwritten: a valid one is skipped, while an
invalid one causes the command to stop and request manual review.
EOF
}

fail() {
    printf 'Error: %s\n' "$*" >&2
    exit 1
}

sha256_file() {
    if command -v shasum >/dev/null 2>&1; then
        shasum -a 256 "$1" | awk '{print $1}'
    elif command -v sha256sum >/dev/null 2>&1; then
        sha256sum "$1" | awk '{print $1}'
    else
        fail "Neither shasum nor sha256sum is available."
    fi
}

download_one() {
    local destination_dir="$1"
    local filename="$2"
    local url="$3"
    local expected_sha256="$4"
    local final_file="$destination_dir/$filename"
    local partial_file="$final_file.part"
    local actual_sha256

    mkdir -p "$destination_dir"

    if [[ -f "$final_file" ]]; then
        actual_sha256="$(sha256_file "$final_file")"
        if [[ "$actual_sha256" == "$expected_sha256" ]]; then
            printf 'verified: %s\n' "$filename"
            return 0
        fi
        printf 'invalid existing file (not overwritten): %s\n' "$final_file" >&2
        return 1
    fi

    printf 'downloading: %s\n' "$filename"
    curl --fail --location --retry 4 --retry-all-errors --continue-at - \
        --output "$partial_file" "$url"

    actual_sha256="$(sha256_file "$partial_file")"
    if [[ "$actual_sha256" != "$expected_sha256" ]]; then
        printf 'checksum failed: %s\n' "$filename" >&2
        return 1
    fi

    mv "$partial_file" "$final_file"
    printf 'verified: %s\n' "$filename"
}

if [[ "${1:-}" == "--download-one" ]]; then
    shift
    [[ "$#" -eq 4 ]] || fail "Internal downloader received an invalid argument count."
    download_one "$@"
    exit 0
fi

while [[ "$#" -gt 0 ]]; do
    case "$1" in
        --collection)
            collection="${2:-}"; shift 2 ;;
        --output-dir)
            output_dir="${2:-}"; shift 2 ;;
        --jobs)
            jobs="${2:-}"; shift 2 ;;
        --dry-run)
            dry_run=1; shift ;;
        --main-script)
            main_script="${2:-}"; shift 2 ;;
        --supp-script)
            supp_script="${2:-}"; shift 2 ;;
        -h|--help)
            usage; exit 0 ;;
        *)
            fail "Unknown option: $1" ;;
    esac
done

[[ "$collection" == "main" || "$collection" == "supplemental" || "$collection" == "all" ]] \
    || fail "--collection must be main, supplemental, or all."
[[ "$jobs" =~ ^[1-9][0-9]*$ ]] || fail "--jobs must be a positive integer."
command -v curl >/dev/null 2>&1 || fail "curl is required."
command -v xargs >/dev/null 2>&1 || fail "xargs is required."

# Converts lines of the generated script manifest into filename<TAB>url<TAB>sha256.
# A gn filename contains '_gn_' (or the grid-cell area file ends in '_gn.nc').
make_manifest() {
    local source_script="$1"
    local manifest="$2"

    [[ -f "$source_script" ]] || fail "Manifest script not found: $source_script"
    awk -F "'" '
        /^'\''[^'\'']+\.nc'\'' / {
            filename = $2
            if (filename ~ /_gn(_|\.)/) {
                print filename "\t" $4 "\t" $8
            }
        }
    ' "$source_script" | sort -u > "$manifest"

    [[ -s "$manifest" ]] || fail "No gn files found in: $source_script"
}

run_collection() {
    local name="$1"
    local source_script="$2"
    local destination
    local manifest
    local count

    if [[ -n "$output_dir" && "$collection" != "all" ]]; then
        destination="$output_dir"
    elif [[ -n "$output_dir" ]]; then
        destination="$output_dir/$name"
    elif [[ "$name" == "main" ]]; then
        destination="$PROJECT_ROOT/data/SLCF_main"
    else
        destination="$PROJECT_ROOT/data/SLCF_supp"
    fi

    mkdir -p "$destination"
    manifest="$destination/download_manifest_gn.tsv"
    make_manifest "$source_script" "$manifest"
    count="$(wc -l < "$manifest" | tr -d ' ')"

    printf '\n%s: %s gn files\nmanifest: %s\ndestination: %s\n' \
        "$name" "$count" "$manifest" "$destination"

    if (( dry_run )); then
        return 0
    fi

    # xargs invokes this script once per manifest line. The final three fields
    # are supplied by xargs as filename, URL, and checksum respectively.
    cut -f1-3 "$manifest" | xargs -P "$jobs" -n 3 \
        "$0" --download-one "$destination"
}

case "$collection" in
    main)
        run_collection main "$main_script" ;;
    supplemental)
        run_collection supplemental "$supp_script" ;;
    all)
        run_collection main "$main_script"
        run_collection supplemental "$supp_script" ;;
esac
