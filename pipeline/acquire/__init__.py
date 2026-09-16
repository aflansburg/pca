"""Acquisition layer: fetch each source's snapshot before staging.

Two API dialects (data.cms.gov data-api, provider-data DKAN datastore) pull DE-filtered
snapshots; `bulk` streams a pinned file. The pipeline then stages Source.path unchanged
(HISTORY 011: snapshot, don't run live APIs at query time).
"""
