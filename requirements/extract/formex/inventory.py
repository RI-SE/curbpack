"""Extract operations.

The bodies live in ``studio.pack.impl.extract.formex.inventory``. Callers of this module receive those same objects.
"""

from studio.pack.impl.extract.formex.inventory import (
    annotations,
    re,
    ET,
    Path,
    load_doc_package,
    collapse_ws,
    element_text,
    local_tag,
    _UNSUPPORTED_TAGS,
    inventory_package,
    _inventory_act,
    _inventory_annex,
    _record_unsupported,
    _article_number,
    _parent_map,
)
