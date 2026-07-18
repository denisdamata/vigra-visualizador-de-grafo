import os
import uuid
from datetime import datetime

UPLOAD_DIR = "uploads"

def ensure_upload_dir():
    os.makedirs(UPLOAD_DIR, exist_ok=True)

def save_uploaded_file(uploaded_file):
    """Save the uploaded file to disk and return its name and path."""
    ensure_upload_dir()
    ext = uploaded_file.name.split(".")[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    with open(filepath, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return filename, filepath

def get_entity_label(conn, entity_type, entity_id):
    """Return the label of a node or edge for display."""
    if entity_type == "node":
        result = conn.execute("SELECT label FROM nodes WHERE id = ?", (entity_id,)).fetchone()
        return result[0] if result else None
    else:  # edge
        result = conn.execute("""
            SELECT n1.label || ' → ' || n2.label
            FROM edges e
            JOIN nodes n1 ON e.source = n1.id
            JOIN nodes n2 ON e.target = n2.id
            WHERE e.id = ?
        """, (entity_id,)).fetchone()
        return result[0] if result else None
