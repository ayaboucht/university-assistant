"""Audit qualité du corpus documentaire.

Vérifie les documents présents dans ``data/raw/original_files`` :
- Empreinte SHA-256 pour la détection des doublons.
- Extractibilité du texte (détection des PDF scannés nécessitant de l'OCR).
- Détection basique d'indices de données personnelles (e-mail, téléphone, CIN).
- Mise à jour de ``data/reference/corpus_index.csv`` en préservant les champs
  édités manuellement et les documents au statut ``a_demander``.

Usage :
    python scripts/audit_corpus.py
    python scripts/audit_corpus.py --no-update-csv
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import logging
import re
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_CORPUS_DIR = Path("data/raw/original_files")
DEFAULT_INDEX_CSV = Path("data/reference/corpus_index.csv")
SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".docx"}

COL_REL_PATH = "chemin_relatif"
COL_NOTES = "notes"
STATUS_YES = "oui"
STATUS_READ_ERROR = "erreur_lecture"
DUPLICATE_NOTE_PREFIX = "Doublon exact de "

CSV_COLUMNS = [
    "doc_id",
    "nom_fichier",
    COL_REL_PATH,
    "categorie",
    "annee",
    "filiere_option",
    "semestre",
    "date_validite",
    "version",
    "statut",
    "extractible",
    "nb_pages",
    "donnees_personnelles",
    "sha256",
    COL_NOTES,
]

EMAIL_RE = re.compile(r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b")
PHONE_RE = re.compile(r"(?:\+212|0)[\s.-]?[5-7](?:[\s.-]?\d{2}){4}\b")
CIN_RE = re.compile(r"\b[A-Z]{1,2}\d{5,6}\b")
NOMINAL_KEYWORDS_RE = re.compile(
    r"\b(?:cne|apog[eé]e|matricule|liste\s+des\s+admis|"
    r"nom\s+et\s+pr[eé]nom)\b",
    re.IGNORECASE,
)


@dataclass
class ExtractionResult:
    """Résultat d'extraction de texte d'un document."""

    text: str
    nb_pages: int
    extractible: str
    error: str | None = None


@dataclass
class AuditSummary:
    """Agrégat des résultats produits lors de l'audit du corpus."""

    corpus_dir: Path
    file_count: int
    rows: list[dict[str, str]] = field(default_factory=list)
    category_counts: dict[str, int] = field(
        default_factory=lambda: defaultdict(int)
    )
    duplicates: dict[str, list[str]] = field(default_factory=dict)
    ocr_needed: list[str] = field(default_factory=list)
    pii_flagged: list[tuple[str, str]] = field(default_factory=list)
    extraction_errors: list[tuple[str, str]] = field(default_factory=list)


def compute_sha256(file_path: Path) -> str:
    """Calcule l'empreinte SHA-256 d'un fichier."""
    digest = hashlib.sha256()
    with file_path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_pages_with_pypdf(file_path: Path) -> list[str] | None:
    """Tente de lire les pages d'un PDF avec pypdf, sinon retourne None."""
    try:
        from pypdf import PdfReader
    except ImportError:
        return None

    logging.getLogger("pypdf").setLevel(logging.ERROR)
    reader = PdfReader(str(file_path))
    return [(page.extract_text() or "").strip() for page in reader.pages]


def _read_pages_with_pymupdf(file_path: Path) -> list[str] | None:
    """Tente de lire les pages d'un PDF avec PyMuPDF, sinon retourne None."""
    try:
        import fitz
    except ImportError:
        return None

    with fitz.open(str(file_path)) as doc:
        return [page.get_text("text").strip() for page in doc]


def _load_pdf_pages(file_path: Path) -> tuple[list[str] | None, str | None]:
    """Lit les pages d'un PDF avec pypdf puis PyMuPDF en repli."""
    try:
        pages = _read_pages_with_pypdf(file_path)
        if pages is not None:
            return pages, None
        pages = _read_pages_with_pymupdf(file_path)
        if pages is not None:
            return pages, None
        return None, "Aucune bibliothèque PDF disponible (pypdf ou pymupdf)."
    except Exception as exc:  # pragma: no cover - dépend des PDF corrompus
        return None, str(exc)


def extract_pdf_text(file_path: Path) -> ExtractionResult:
    """Extrait le texte d'un PDF et évalue s'il nécessite de l'OCR."""
    page_texts, error = _load_pdf_pages(file_path)
    if page_texts is None:
        status = (
            "non_verifie (installer pypdf ou pymupdf)"
            if error and "Aucune bibliothèque" in error
            else STATUS_READ_ERROR
        )
        return ExtractionResult(text="", nb_pages=0, extractible=status, error=error)

    nb_pages = len(page_texts)
    if nb_pages == 0:
        return ExtractionResult(text="", nb_pages=0, extractible="vide")

    non_empty_pages = sum(1 for txt in page_texts if len(txt) >= 25)
    full_text = "\n".join(page_texts)

    if len(full_text.strip()) < 30 or non_empty_pages == 0:
        status = "non (OCR requis)"
    elif non_empty_pages < nb_pages:
        status = f"partiel ({non_empty_pages}/{nb_pages} pages)"
    else:
        status = STATUS_YES

    return ExtractionResult(text=full_text, nb_pages=nb_pages, extractible=status)


def extract_docx_text(file_path: Path) -> ExtractionResult:
    """Extrait le texte d'un fichier DOCX via python-docx."""
    try:
        import docx
    except ImportError:
        return ExtractionResult(
            text="",
            nb_pages=0,
            extractible="non_verifie (installer python-docx)",
            error="python-docx non installé.",
        )

    try:
        document = docx.Document(str(file_path))
        text = "\n".join(p.text for p in document.paragraphs if p.text.strip())
        status = STATUS_YES if len(text.strip()) >= 20 else "non"
        return ExtractionResult(text=text, nb_pages=1, extractible=status)
    except Exception as exc:
        return ExtractionResult(
            text="", nb_pages=0, extractible=STATUS_READ_ERROR, error=str(exc)
        )


def extract_document_text(file_path: Path) -> ExtractionResult:
    """Dispatch l'extraction selon l'extension du fichier."""
    suffix = file_path.suffix.lower()
    if suffix == ".pdf":
        return extract_pdf_text(file_path)
    if suffix == ".txt":
        text = file_path.read_text(encoding="utf-8", errors="replace")
        status = STATUS_YES if len(text.strip()) >= 20 else "vide"
        return ExtractionResult(text=text, nb_pages=1, extractible=status)
    if suffix == ".docx":
        return extract_docx_text(file_path)
    return ExtractionResult(text="", nb_pages=0, extractible="format_non_supporte")


def detect_pii_signals(filename: str, text: str) -> str:
    """Repère des motifs courants de données personnelles dans le nom ou texte."""
    signals: list[str] = []

    if NOMINAL_KEYWORDS_RE.search(filename) or NOMINAL_KEYWORDS_RE.search(text):
        signals.append("liste_nominative")
    if EMAIL_RE.search(text):
        signals.append("email")
    if PHONE_RE.search(text):
        signals.append("telephone")
    if CIN_RE.search(text):
        signals.append("cin_potentiel")

    return f"{STATUS_YES} ({', '.join(signals)})" if signals else "non_detectee"


def _infer_year(raw: str) -> str:
    """Déduit l'année universitaire depuis le chemin ou le nom du fichier."""
    if "2026-2027" in raw:
        return "2026-2027"
    if (
        "2025-2026" in raw
        or "25-26" in raw
        or re.search(r"(?:^|[\s_-])2026(?:$|[\s_.-])", raw)
        or "S2 26" in raw
    ):
        return "2025-2026"
    return ""


def _infer_program(raw: str) -> str:
    """Déduit la filière et l'option depuis le chemin ou le nom du fichier."""
    upper_raw = raw.upper()
    niveau_match = re.search(
        r"(?<![A-Z0-9])([1-5]IIRK?)(?![A-Z0-9])", raw, re.IGNORECASE
    )
    niveau = niveau_match.group(1).upper().replace("K", "") if niveau_match else ""
    options = [
        opt for opt in ("IADATA", "IA-DATA", "DDSI", "CIR") if opt in upper_raw
    ]
    option_clean = options[0].replace("IA-DATA", "IADATA") if options else ""

    if niveau and option_clean:
        return f"{niveau}-{option_clean}"
    if niveau:
        return niveau
    if any(tag in upper_raw for tag in ("MASTER", "MBDS", "IA2")):
        return "Master"
    return "EMSI (Général)"


def _infer_semester(upper_raw: str) -> str:
    """Déduit le semestre (S1/S2) depuis le chemin en majuscules."""
    if (
        re.search(r"(?:^|[/_\s-])S1(?:$|[/_\s.-])", upper_raw)
        or "PREMIER_SEMESTRE" in upper_raw
        or "SEMETRE_1" in upper_raw
    ):
        return "S1"
    if (
        re.search(r"(?:^|[/_\s-])S2(?:$|[/_\s.-])", upper_raw)
        or "SECOND_SEMESTRE" in upper_raw
    ):
        return "S2"
    return ""


def infer_metadata(rel_path: Path) -> dict[str, str]:
    """Déduit les métadonnées initiales à partir du chemin et du nom de fichier."""
    parts = rel_path.parts
    raw = rel_path.as_posix()
    return {
        "categorie": parts[0] if len(parts) > 1 else "non_classee",
        "annee": _infer_year(raw),
        "filiere_option": _infer_program(raw),
        "semestre": _infer_semester(raw.upper()),
    }


def load_existing_index(
    csv_path: Path,
) -> tuple[dict[str, dict[str, str]], list[dict[str, str]]]:
    """Charge l'index existant pour conserver annotations manuelles et demandes."""
    by_path: dict[str, dict[str, str]] = {}
    pending_rows: list[dict[str, str]] = []
    if not csv_path.exists():
        return by_path, pending_rows

    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            rel_path = (row.get(COL_REL_PATH) or "").strip()
            statut = (row.get("statut") or "").strip()
            if statut == "a_demander" and not rel_path:
                pending_rows.append(row)
            elif rel_path:
                by_path[rel_path] = row
    return by_path, pending_rows


def _collect_supported_files(corpus_dir: Path) -> list[Path]:
    """Retourne les fichiers supportés triés par chemin."""
    return sorted(
        path
        for path in corpus_dir.rglob("*")
        if path.is_file()
        and path.name != ".gitkeep"
        and path.suffix.lower() in SUPPORTED_EXTENSIONS
    )


def _process_file(
    idx: int,
    file_path: Path,
    corpus_dir: Path,
    prev: dict[str, str],
) -> tuple[dict[str, str], str, str | None]:
    """Audite un fichier unique et construit sa ligne d'index."""
    rel_path = file_path.relative_to(corpus_dir)
    rel_posix = rel_path.as_posix()
    sha256 = compute_sha256(file_path)
    extraction = extract_document_text(file_path)
    pii = detect_pii_signals(file_path.name, extraction.text)
    inferred = infer_metadata(rel_path)

    prev_notes = prev.get(COL_NOTES) or ""
    if prev_notes.startswith(DUPLICATE_NOTE_PREFIX):
        prev_notes = ""

    row = {
        "doc_id": prev.get("doc_id") or f"DOC-{idx:03d}",
        "nom_fichier": file_path.name,
        COL_REL_PATH: rel_posix,
        "categorie": prev.get("categorie") or inferred["categorie"],
        "annee": prev.get("annee") or inferred["annee"],
        "filiere_option": prev.get("filiere_option") or inferred["filiere_option"],
        "semestre": prev.get("semestre") or inferred["semestre"],
        "date_validite": prev.get("date_validite") or "",
        "version": prev.get("version") or "1.0",
        "statut": prev.get("statut") or "recu",
        "extractible": extraction.extractible,
        "nb_pages": str(extraction.nb_pages),
        "donnees_personnelles": pii,
        "sha256": sha256[:12],
        COL_NOTES: prev_notes,
    }
    return row, sha256, extraction.error


def _annotate_duplicates(
    rows: list[dict[str, str]],
    hashes: dict[str, list[str]],
) -> dict[str, list[str]]:
    """Identifie les doublons SHA-256 et renseigne leur note si absente."""
    duplicates = {h: paths for h, paths in hashes.items() if len(paths) > 1}
    duplicate_notes = {
        dup_path: f"{DUPLICATE_NOTE_PREFIX}{paths[0]}"
        for paths in duplicates.values()
        for dup_path in paths[1:]
    }
    for row in rows:
        dup_note = duplicate_notes.get(row[COL_REL_PATH])
        if dup_note and not row[COL_NOTES]:
            row[COL_NOTES] = dup_note
    return duplicates


def _build_audit_summary(
    corpus_dir: Path,
    files: list[Path],
    index_csv: Path,
) -> AuditSummary:
    """Analyse tous les fichiers et agrège les résultats d'audit."""
    existing_by_path, pending_rows = load_existing_index(index_csv)
    hashes: dict[str, list[str]] = defaultdict(list)
    summary = AuditSummary(corpus_dir=corpus_dir, file_count=len(files))

    for idx, file_path in enumerate(files, start=1):
        rel_posix = file_path.relative_to(corpus_dir).as_posix()
        row, sha256, error = _process_file(
            idx, file_path, corpus_dir, existing_by_path.get(rel_posix, {})
        )
        summary.rows.append(row)
        hashes[sha256].append(rel_posix)
        summary.category_counts[row["categorie"]] += 1

        if error:
            summary.extraction_errors.append((rel_posix, error))
        if row["extractible"].startswith(("non", "partiel")):
            summary.ocr_needed.append(f"{rel_posix} -> {row['extractible']}")
        if row["donnees_personnelles"].startswith(STATUS_YES):
            summary.pii_flagged.append((rel_posix, row["donnees_personnelles"]))

    summary.rows.extend(
        {col: (pending.get(col) or "") for col in CSV_COLUMNS}
        for pending in pending_rows
    )
    summary.duplicates = _annotate_duplicates(summary.rows, hashes)
    return summary


def _write_index_csv(index_csv: Path, rows: list[dict[str, str]]) -> None:
    """Écrit l'index CSV du corpus."""
    index_csv.parent.mkdir(parents=True, exist_ok=True)
    with index_csv.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def _print_audit_report(summary: AuditSummary) -> None:
    """Affiche le résumé console de l'audit du corpus."""
    print("=== RAPPORT D'AUDIT DU CORPUS ===")
    print(f"Dossier analysé : {summary.corpus_dir}")
    print(f"Fichiers analysés : {summary.file_count}")
    print("Répartition par catégorie :")
    for cat, count in sorted(summary.category_counts.items()):
        print(f"  - {cat}: {count}")

    print(f"\nDoublons exacts (SHA-256) : {len(summary.duplicates)}")
    for sha, paths in summary.duplicates.items():
        print(f"  - [{sha[:12]}] : {', '.join(paths)}")

    print(
        f"\nFichiers nécessitant OCR / vérification texte : {len(summary.ocr_needed)}"
    )
    for item in summary.ocr_needed:
        print(f"  - {item}")

    print(
        f"\nFichiers avec indices de données personnelles : {len(summary.pii_flagged)}"
    )
    for path_str, reason in summary.pii_flagged:
        print(f"  - {path_str} : {reason}")

    if summary.extraction_errors:
        print(f"\nAvertissements d'extraction ({len(summary.extraction_errors)}) :")
        for path_str, err in summary.extraction_errors[:5]:
            print(f"  - {path_str} : {err}")
        if len(summary.extraction_errors) > 5:
            print(f"  ... et {len(summary.extraction_errors) - 5} autre(s).")


def audit_corpus(
    corpus_dir: Path,
    index_csv: Path,
    update_csv: bool = True,
) -> int:
    """Exécute l'audit complet sur le corpus et affiche un résumé."""
    if not corpus_dir.exists():
        print(f"[ERREUR] Dossier corpus introuvable : {corpus_dir}")
        return 1

    files = _collect_supported_files(corpus_dir)
    if not files:
        print(f"[INFO] Aucun document supporté trouvé dans {corpus_dir}")
        return 0

    summary = _build_audit_summary(corpus_dir, files, index_csv)
    if update_csv:
        _write_index_csv(index_csv, summary.rows)

    _print_audit_report(summary)
    if update_csv:
        print(f"\nIndex mis à jour : {index_csv} ({len(summary.rows)} lignes)")
    return 0


def parse_args() -> argparse.Namespace:
    """Parse les arguments CLI du script d'audit."""
    parser = argparse.ArgumentParser(description="Audit qualité du corpus EMSI.")
    parser.add_argument(
        "--corpus-dir",
        type=Path,
        default=DEFAULT_CORPUS_DIR,
        help="Dossier racine contenant les documents bruts.",
    )
    parser.add_argument(
        "--index-csv",
        type=Path,
        default=DEFAULT_INDEX_CSV,
        help="Chemin du fichier corpus_index.csv.",
    )
    parser.add_argument(
        "--no-update-csv",
        action="store_true",
        help="Affiche le rapport sans modifier corpus_index.csv.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    raise SystemExit(
        audit_corpus(
            corpus_dir=args.corpus_dir,
            index_csv=args.index_csv,
            update_csv=not args.no_update_csv,
        )
    )
