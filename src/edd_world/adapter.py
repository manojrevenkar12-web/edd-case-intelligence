"""World cases as the case-management system exports them: no truth, transfers in export order."""

from __future__ import annotations

import hashlib

from edd.schema import CaseRecord, TransferRecord
from edd_world.cases import Case


def to_record(c: Case) -> CaseRecord:
    txs = sorted(c.transfers, key=lambda t: hashlib.md5(t.id.encode()).hexdigest())  # export order, not time order
    return CaseRecord(
        id=c.id,
        week=c.week,
        kind=c.kind,
        country=c.country,
        declared=c.declared,
        declared_monthly_eur=c.declared_monthly_eur,
        account_age_months=c.account_age_months,
        documents_on_file=c.documents_on_file,
        transfers=[TransferRecord(**t.__dict__) for t in txs],
    )
