"""Registered source catalog.

The operations live in ``studio.pack.impl.catalog``. Callers of this
module receive those same objects.
"""

from studio.pack.impl.catalog import (
    CATALOG_NAME,
    _DEFAULT_ROWS,
    _document_id_for,
    _section,
    add_document,
    add_section,
    add_source,
    attach_documents,
    catalog_path,
    default_sources,
    ensure_catalog,
    find_document,
    find_source,
    list_formex_adapter_choices,
    load_catalog,
    make_document_id,
    make_id,
    save_catalog,
)
