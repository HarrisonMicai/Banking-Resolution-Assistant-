import re
import json
from datetime import datetime, timezone
from docx import Document
import hashlib
import os
import csv
from pathlib import Path
from docx.text.paragraph import Paragraph
from docx.table import Table

# ==========================================
# PATH CONFIGURATION
# ==========================================

RAG_DIR = Path(__file__).resolve().parent
APP_DIR = RAG_DIR.parent
PROJECT_DIR = APP_DIR.parent

MANIFEST_PATH = (
    PROJECT_DIR / "specs" / "policy-rag" / "knowledge_base_manifest(in).csv"
)

KNOWLEDGE_BASE_DIR = RAG_DIR / "data" / "knowledge_base"

PROCESSED_DIR = RAG_DIR / "data" / "processed"

ACCEPTANCE_TEST_PATH = (
    PROCESSED_DIR / "ingestion_acceptance_tests.json"
)

RUN_LOG_PATH = PROCESSED_DIR / "ingestion_run_log.json"

OUTPUT_PATH = PROCESSED_DIR / "documents.jsonl"


# ==========================================
# INGESTION SERVICE
# ==========================================

class IngestionService:

    def __init__(
        self,
        manifest_path=MANIFEST_PATH,
        knowledge_base_dir=KNOWLEDGE_BASE_DIR,
        output_path=OUTPUT_PATH,
        run_log_path=RUN_LOG_PATH,
    ):
        """
        Initialize the ingestion service.

        Store the file paths needed by the pipeline.
        """

        self.manifest_path = Path(manifest_path)
        self.knowledge_base_dir = Path(knowledge_base_dir)
        self.output_path = Path(output_path)
        self.run_log_path = Path(run_log_path)

        self.accepted_records = []
        self.rejected_records = []
        self.warnings = []

    # ======================================
    # STEP 1: LOAD MANIFEST
    # ======================================

    def _load_manifest(self):
        """
        Load the CSV manifest and validate its headers.
        """

        if not self.manifest_path.exists():
            raise FileNotFoundError(
                f"Manifest not found: {self.manifest_path}"
            )

        required_headers = {
            "source_id",
            "title",
            "document_type",
            "version",
            "effective_date",
            "access_label",
            "status",
            "relative_path",
        }

        with self.manifest_path.open(
            mode="r",
            encoding="utf-8-sig",
            newline=""
        ) as csv_file:

            reader = csv.DictReader(csv_file)

            if reader.fieldnames is None:
                raise ValueError("Manifest is empty or has no headers.")

            actual_headers = {
                header.strip() for header in reader.fieldnames if header
            }

            missing_headers = required_headers - actual_headers

            if missing_headers:
                raise ValueError(
                    f"Manifest is missing headers: "
                    f"{sorted(missing_headers)}"
                )

            manifest_records = []

            for row in reader:
                normalized_row = {
                    key.strip(): (value.strip() if value else "")
                    for key, value in row.items()
                    if key is not None
                }

                manifest_records.append(normalized_row)

        return manifest_records

    # ======================================
    # STEP 2: FIND DUPLICATE SOURCE IDS
    # ======================================

    def _find_duplicate_source_ids(self, manifest_records):
        """
        Identify duplicate source IDs.

        All records sharing a duplicate ID are rejected
        to avoid ambiguous document identity.
        """

        source_ids = [
            record.get("source_id", "").strip()
            for record in manifest_records
        ]

        seen = set()
        duplicate_ids = set()

        for source_id in source_ids:
            if source_id in seen:
                duplicate_ids.add(source_id)
            seen.add(source_id)

        # Reject every record with a duplicated source ID.
        for record in manifest_records:
            source_id = record.get("source_id", "").strip()

            if source_id in duplicate_ids:
                self.rejected_records.append({
                    "source_id": source_id,
                    "relative_path": record.get("relative_path", ""),
                    "reason": "Duplicate source_id"
                })

        return duplicate_ids

    # ======================================
    # STEP 3: CHECK REQUIRED FIELDS
    # ======================================

    def _missing_required_fields(self, record):
        """
        Identify required manifest fields that are missing.
        """

        required_fields = [
            "source_id",
            "title",
            "document_type",
            "version",
            "effective_date",
            "access_label",
            "status",
            "relative_path",
        ]

        missing_fields = []

        for field in required_fields:
            value = record.get(field)

            if value is None or not str(value).strip():
                missing_fields.append(field)

        return missing_fields

     # ======================================
    # STEP 4: VALIDATE DOCUMENT FILE PATHS
    # ======================================

    def _validate_document_file(self, record):
        """
        Validate that a manifest entry points to an existing DOCX file
        inside the knowledge base directory.

        Returns:
            (document_path, None) when valid
            (None, error_message) when invalid
        """

        relative_path = record.get("relative_path", "").strip()

        if not relative_path:
            return None, "Missing relative_path"

        # Normalize Windows and Unix path separators.
        relative_path = relative_path.replace("\\", "/")

        document_path = (
            self.knowledge_base_dir / relative_path
        ).resolve()

        knowledge_base_root = self.knowledge_base_dir.resolve()

        # Prevent paths from escaping the knowledge base directory.
        if (
            document_path != knowledge_base_root
            and knowledge_base_root not in document_path.parents
        ):
            return None, "File path is outside the knowledge base directory"

        # Confirm the file exists.
        if not document_path.exists():
            return None, f"File does not exist: {relative_path}"

        if not document_path.is_file():
            return None, f"Path is not a file: {relative_path}"

        # Only DOCX files are supported by this ingestion pipeline.
        if document_path.suffix.lower() != ".docx":
            return None, f"Unsupported file extension: {document_path.suffix}"

        return document_path, None

    # ======================================
    # STEP 5: FIND UNLISTED DOCUMENTS
    # ======================================

    def _find_unlisted_files(self, manifest_records):
        """
        Scan the knowledge base and reject DOCX files
        that are not listed in the manifest.
        """

        # Build a set of every path listed in the manifest.
        # Include all statuses, including Superseded.
        listed_paths = {
            Path(
                record.get("relative_path", "").replace("\\", "/")
            ).as_posix().casefold()
            for record in manifest_records
            if record.get("relative_path", "").strip()
        }

        # Scan all DOCX files in the knowledge base.
        for file_path in self.knowledge_base_dir.rglob("*"):

            if not file_path.is_file():
                continue

            if file_path.suffix.lower() != ".docx":
                continue

            relative_path = (
                file_path.relative_to(self.knowledge_base_dir)
                .as_posix()
                .casefold()
            )

            # Reject files that are not included in the manifest.
            if relative_path not in listed_paths:
                self.rejected_records.append({
                    "source_id": None,
                    "relative_path": relative_path,
                    "reason": "File is not listed in manifest"
                })


    # ======================================
    # STEP 6: EXTRACT DOCX TEXT
    # ======================================

    def _extract_docx_text(self, document_path):
        """
        Extract paragraphs from a DOCX document, including paragraphs
    inside tables, while preserving document order and heading styles.
    """

        document = Document(document_path)
        paragraphs = []

        def add_paragraph(paragraph):
            text = paragraph.text.strip()

            if not text:
                return

            paragraphs.append({
                "text": text,
                "style": paragraph.style.name
            })

        # Iterate through document elements in their original order.
        for element in document.element.body.iterchildren():

            if element.tag.endswith("}p"):
                paragraph = Paragraph(element, document)
                add_paragraph(paragraph)

            elif element.tag.endswith("}tbl"):
                table = Table(element, document)

                for row in table.rows:
                    for cell in row.cells:
                        for paragraph in cell.paragraphs:
                            add_paragraph(paragraph)
        return paragraphs

    # ======================================
    # STEP 7: NORMALIZE WHITESPACE
    # ======================================

    def _normalize_whitespace(self, text):
        """
        Remove unnecessary whitespace while preserving
        readable paragraph boundaries.
        """

        text = text.replace("\xa0", " ")
        text = text.replace("\t", " ")

        # Normalize spaces within lines.
        text = re.sub(r" +", " ", text)

        # Normalize excessive blank lines.
        text = re.sub(r"\n{3,}", "\n\n", text)

        return text.strip()

    # ======================================
    # STEP 8: IDENTIFY DOCUMENT HEADINGS
    # ======================================

    def _is_heading(self, paragraph):
        """
        Determine whether a DOCX paragraph is a heading using word style and numbering heading patterns.
        """

        style = paragraph.get("style", "")
        text = paragraph.get("text", "").strip()

        #Recognize heading styles based on common DOCX naming conventions.
        if style.startswith("Heading") or style == "Title":
            return True
        # Recognize numbered section headings:
        # 1. Purpose
        # 2. Decision Principles
        # 3. Financial Redress Thresholds
        # 4. Approval Authority
        if re.match(r"^\d+(\.\d+)*\.\s+\S", text):
            return True

    # ======================================
    # STEP 9: CREATE SECTION SLUGS
    # ======================================

    def _slugify(self, text):
        """
        Convert section titles into URL/chunk-friendly IDs.
        """

        text = text.lower()
        text = re.sub(r"[^a-z0-9]+", "-", text)

        return text.strip("-")

    # ======================================
    # STEP 10: EXTRACT DOCUMENT SECTIONS
    # ======================================

    def _extract_sections(self, paragraphs, source_id):
        """
        Divide extracted document text into sections
        based on DOCX heading styles.
        """

        sections = []
        current_title = "Document Content"
        current_text = []

        def save_section():
            if not current_text:
                return

            sequence = len(sections) + 1

            sections.append({
                "section_title": current_title,
                "sequence": sequence,
                "text": self._normalize_whitespace(
                    "\n".join(current_text)
                ),
                "chunk_id": (
                    f"{source_id}#"
                    f"{self._slugify(current_title)}#"
                    f"{sequence:04d}"
                )
            })

        for paragraph in paragraphs:

            paragraph_text = self._normalize_whitespace(
                paragraph["text"]
            )

            if self._is_heading(paragraph):

                # Save the previous section before starting another.
                save_section()

                current_title = paragraph_text
                current_text = []

            else:
                current_text.append(paragraph_text)

        # Save the final section.
        save_section()

        return sections

    # ======================================
    # STEP 11: GENERATE SHA-256 CHECKSUM
    # ======================================

    def _sha256(self, text):
        """
        Generate a deterministic checksum for document text.
        """

        return hashlib.sha256(
            text.encode("utf-8")
        ).hexdigest()
    
    # ======================================
    # STEP 12: PROCESS ONE DOCUMENT
    # ======================================

    def _process_document(self, record):
        source_id = record["source_id"]

        # Validate the document path and extension.
        document_path, error = self._validate_document_file(record)

        if error:
            self.rejected_records.append({
                "source_id": source_id,
                "relative_path": record.get("relative_path", ""),
                "reason": error
            })
            return

        # Extract DOCX paragraphs.
        paragraphs = self._extract_docx_text(document_path)

        if source_id == "KB-002":
            for index, paragraph in enumerate(paragraphs):
                print(
                    index,
                    repr(paragraph.get("style")),
                    repr(paragraph.get("text"))
        )

        if not paragraphs:
            self.rejected_records.append({
                "source_id": source_id,
                "relative_path": record["relative_path"],
                "reason": "Document contains no extractable paragraphs"
            })
            return

        # Combine paragraphs for the document checksum.
        full_text = "\n".join(
            paragraph["text"] for paragraph in paragraphs
        )

        normalized_text = self._normalize_whitespace(full_text)

        if not normalized_text:
            self.rejected_records.append({
                "source_id": source_id,
                "relative_path": record["relative_path"],
                "reason": "Document contains no usable text"
            })
            return

        # Generate document checksum.
        checksum = self._sha256(normalized_text)

        # Extract document sections.
        sections = self._extract_sections(paragraphs, source_id)

        if not sections:
            self.rejected_records.append({
                "source_id": source_id,
                "relative_path": record["relative_path"],
                "reason": "No sections could be extracted"
            })
            return

        # Create one output record per section.
        for section in sections:
            accepted_record = {
                "source_id": source_id,
                "title": record["title"],
                "document_type": record["document_type"],
                "version": record["version"],
                "effective_date": record["effective_date"],
                "access_label": record["access_label"],
                "status": record["status"],
                "relative_path": record["relative_path"],
                "checksum": checksum,
                "section_title": section["section_title"],
                "sequence": section["sequence"],
                "text": section["text"],
                "chunk_id": section["chunk_id"]
            }

            self.accepted_records.append(accepted_record)


    # ======================================
    # STEP 13: RUN INGESTION PIPELINE
    # ======================================

    def run(self):
        """
        Execute the complete ingestion pipeline.
        """

        # Reset state so repeated runs don't accumulate records.
        self.accepted_records = []
        self.rejected_records = []
        self.warnings = []

        start_time = datetime.now(timezone.utc).isoformat()

        print("Starting knowledge base ingestion...")

        # Step 1: Load manifest.
        manifest_records = self._load_manifest()

        print(f"Loaded {len(manifest_records)} manifest records.")

        # Step 2: Identify duplicate source IDs.
        duplicate_ids = self._find_duplicate_source_ids(
            manifest_records
        )

        print(f"Found {len(duplicate_ids)} duplicate source IDs.")

        # Step 3: Find files not listed in the manifest.
        self._find_unlisted_files(manifest_records)

        # Step 4: Process each manifest record.
        for record in manifest_records:

            source_id = record.get("source_id", "").strip()

            # Skip records with duplicate IDs.
            if source_id in duplicate_ids:
                continue

            # Validate required metadata.
            missing_fields = self._missing_required_fields(record)

            if missing_fields:
                self.rejected_records.append({
                    "source_id": source_id,
                    "relative_path": record.get("relative_path", ""),
                    "reason": (
                        "Missing required fields: "
                        + ", ".join(missing_fields)
                    )
                })
                continue

            # Process the document.
            try:
                self._process_document(record)

            except Exception as error:
                self.rejected_records.append({
                    "source_id": source_id,
                    "relative_path": record.get("relative_path", ""),
                    "reason": f"Document processing failed: {error}"
                })

        end_time = datetime.now(timezone.utc).isoformat()

        # Step 5: Build ingestion summary.
        summary = {
            "started_at": start_time,
            "completed_at": end_time,
            "manifest_records": len(manifest_records),
            "accepted_records": len(self.accepted_records),
            "rejected_records": len(self.rejected_records),
            "warnings": self.warnings,
            "status": (
                "failed" if self.rejected_records else "completed"
            )
        }

        print("Ingestion processing finished.")

        return summary


    # ======================================
    # STEP 14: WRITE INGESTION OUTPUTS
    # ======================================

    def write_outputs(self, summary):
        """
        Save accepted document records and ingestion results.
        """

        # Make sure the output directory exists.
        self.output_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        self.run_log_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        # Write accepted records to JSONL.
        with self.output_path.open(
            mode="w",
            encoding="utf-8"
        ) as output_file:

            for record in self.accepted_records:
                output_file.write(
                    json.dumps(record, ensure_ascii=False) + "\n"
                )

        # Write summary and rejected records to the run log.
        run_log = {
            "summary": summary,
            "rejected_documents": self.rejected_records
        }

        with self.run_log_path.open(
            mode="w",
            encoding="utf-8"
        ) as log_file:

            json.dump(
                run_log,
                log_file,
                indent=4,
                ensure_ascii=False
            )

        print(f"Accepted documents saved to: {self.output_path}")
        print(f"Ingestion run log saved to: {self.run_log_path}")


if __name__ == "__main__":
    service = IngestionService()

    summary = service.run()

    service.write_outputs(summary)

    print("\nIngestion Summary:")
    if summary["status"] != "completed":
        raise RuntimeError(
            "Ingestion completed with rejected records; "
            "the vector index must not be rebuilt."
        )
    print(json.dumps(summary, indent=4))

