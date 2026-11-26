"""Extract operations.

The bodies live in ``studio.pack.impl.extract.formex.provisions``. Callers of this module receive those same objects.
"""

from studio.pack.impl.extract.formex.provisions import (
    annotations,
    re,
    textwrap,
    ET,
    Path,
    ModelError,
    load_doc_package,
    collapse_ws,
    element_text,
    local_tag,
    wrap_law,
    extract_section_provisions,
    _find_article,
    _provisions_from_article,
    _provisions_from_annex,
    _provisions_from_annex_item,
    _nested_alpha_items,
    _item_intro,
    _item_body,
    _marker,
    _normalize_point,
    _normalize_letter,
    _para_number,
    _top_list_items,
    _preamble_before_list,
    _alinea_preamble,
    _paragraph_body,
    _parent_map,
    _unique_loci,
)
