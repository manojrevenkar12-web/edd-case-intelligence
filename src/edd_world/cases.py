"""Synthetic EDD cases with a known truth. Truth side: nothing in `edd` imports this.

A case is a customer (consumer or business, with what they declared at onboarding) and 30 to 400 transfers.
Each customer follows one typology. Some typologies are suspicious (structuring, pass-through, mule accounts,
funnels, crypto off-ramps); others are legitimate but look alike (a marketplace seller receives many small
payments; a payroll provider pays out in bulk; a family sends most of its money to one relative abroad).
The truth for every case is the set of red flags whose definition is met, the risk class an experienced
reviewer would give with the customer's verified context, and the documents that review would request.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

COUNTRIES = ["GB", "DE", "FR", "ES", "IT", "NL", "PL", "US", "IN", "BR", "AE", "TR", "NG", "PH"]
HIGH_RISK = ["IR", "KP", "MM", "SY", "YE", "AF", "HT", "SS"]
EXCHANGES = ["Kraken", "Coinbase", "Bitstamp", "Binance", "Bitpanda", "OKX"]
NEW_EXCHANGES = ["Zentrix Swap", "NovaCoin Hub", "QuickBit OTC"]  # appear only with a new typology

TYPOLOGIES = {
    # typology: (suspicious?, consumer share, business share, base weight)
    "salary_household": (False, 1, 0, 0.20),
    "freelancer": (False, 1, 0, 0.12),
    "student_tuition": (False, 1, 0, 0.06),
    "remittance_family": (False, 1, 0, 0.10),
    "marketplace_seller": (False, 0, 1, 0.08),
    "payroll_provider": (False, 0, 1, 0.05),
    "small_trader": (False, 0, 1, 0.08),
    "structuring": (True, 1, 1, 0.06),
    "pass_through": (True, 1, 1, 0.06),
    "money_mule": (True, 1, 0, 0.06),
    "funnel": (True, 0, 1, 0.04),
    "crypto_offramp": (True, 1, 0, 0.05),
    "jurisdiction_routing": (True, 0, 1, 0.04),
    # Appears in production from week 7 only: mule accounts paid as "orders" and emptied to new exchanges.
    "app_fraud_mule": (True, 1, 0, 0.0),
}

OCCUPATION = {
    "salary_household": "nurse",
    "freelancer": "graphic designer",
    "student_tuition": "student",
    "remittance_family": "warehouse worker",
    "structuring": "restaurant owner",
    "pass_through": "consultant",
    "money_mule": "student",
    "crypto_offramp": "retail assistant",
    "app_fraud_mule": "student",
}
BUSINESS = {
    "marketplace_seller": "online marketplace seller",
    "payroll_provider": "payroll services",
    "small_trader": "import of furniture",
    "structuring": "cash-intensive food retail",
    "pass_through": "consulting",
    "funnel": "electronics wholesale",
    "jurisdiction_routing": "logistics and freight",
}


@dataclass
class Transfer:
    id: str
    hour: float
    direction: str  # "in" or "out"
    amount_eur: float
    counterparty: str
    country: str
    reference: str


@dataclass
class Case:
    id: str
    week: int
    kind: str  # consumer or business
    country: str
    declared: str  # occupation or business activity, free text
    declared_monthly_eur: float
    account_age_months: int
    documents_on_file: bool
    transfers: list[Transfer]
    # truth, never shown to the workbench
    typology: str = ""
    truth_flags: set[str] = field(default_factory=set)
    truth_risk: str = "low"
    truth_documents: set[str] = field(default_factory=set)


def _cp(rng: np.random.Generator, prefix: str, n: int) -> list[str]:
    return [f"{prefix}-{rng.integers(10_000, 99_999)}" for _ in range(n)]


def _transfers(rng: np.random.Generator, typology: str, days: int, case_id: str) -> list[Transfer]:
    out: list[Transfer] = []

    def add(hour: float, direction: str, amount: float, cp: str, country: str, ref: str) -> None:
        out.append(Transfer("", float(hour), direction, round(float(amount), 2), cp, country, ref))

    span = days * 24.0
    home = str(rng.choice(COUNTRIES[:7]))
    if typology in (
        "salary_household",
        "student_tuition",
        "structuring",
        "crypto_offramp",
        "pass_through",
        "money_mule",
    ):
        for m in range(days // 30):  # a salary or allowance
            add(
                m * 720 + rng.uniform(0, 48),
                "in",
                rng.normal(2600, 300) if typology != "student_tuition" else 900,
                "Employer Ltd" if typology != "student_tuition" else "Parent",
                home,
                "salary",
            )
    n_small = int(rng.integers(15, 40))
    for _ in range(n_small):  # everyday spending
        add(rng.uniform(0, span), "out", rng.lognormal(3.5, 0.8), f"Shop-{rng.integers(100, 999)}", home, "card")
    if typology == "freelancer":
        for cp in _cp(rng, "Client", int(rng.integers(3, 7))):
            for _ in range(int(rng.integers(1, 4))):
                add(rng.uniform(0, span), "in", rng.lognormal(7.0, 0.5), cp, str(rng.choice(COUNTRIES)), "invoice")
    if typology == "student_tuition":
        add(rng.uniform(0, span), "out", rng.normal(9000, 800), "University Bursar", home, "tuition fees")
    if typology == "remittance_family":
        relative = f"Relative-{rng.integers(100, 999)}"
        abroad = str(rng.choice(["IN", "PH", "NG", "BR", "TR"]))
        for m in range(days // 30):
            add(m * 720 + rng.uniform(0, 96), "in", rng.normal(2200, 200), "Employer Ltd", home, "salary")
            for _ in range(int(rng.integers(2, 4))):
                add(m * 720 + rng.uniform(100, 700), "out", rng.normal(400, 80), relative, abroad, "family support")
    if typology == "marketplace_seller":
        buyers = _cp(rng, "Buyer", int(rng.integers(60, 160)))
        for b in buyers:
            add(rng.uniform(0, span), "in", rng.lognormal(3.8, 0.6), b, str(rng.choice(COUNTRIES[:9])), "order")
        for m in range(days // 30):
            add(m * 720 + 600, "out", rng.normal(3000, 600), f"Supplier-{rng.integers(10, 99)}", "CN", "stock")
    if typology == "payroll_provider":
        clients = _cp(rng, "Client", int(rng.integers(20, 40)))
        for c in clients:
            add(rng.uniform(0, span), "in", rng.lognormal(8.0, 0.4), c, home, "payroll funding")
        add(rng.uniform(0, span), "out", rng.normal(60000, 9000), "Payroll Clearing GmbH", "DE", "salary batch")
    if typology == "small_trader":
        for _ in range(int(rng.integers(6, 14))):
            add(
                rng.uniform(0, span),
                "in",
                rng.lognormal(8.3, 0.5),
                f"Customer-{rng.integers(100, 999)}",
                home,
                "invoice",
            )
        for _ in range(int(rng.integers(3, 7))):
            add(
                rng.uniform(0, span),
                "out",
                rng.lognormal(8.5, 0.4),
                f"Factory-{rng.integers(10, 99)}",
                str(rng.choice(["CN", "VN", "IN", "TR"])),
                "goods",
            )
    if typology == "structuring":
        for _ in range(int(rng.integers(3, 7))):
            add(
                rng.uniform(0, min(span, 30 * 24)),
                "in",
                rng.uniform(9000, 9950),
                f"Cash deposit point {rng.integers(1, 9)}",
                home,
                "deposit",
            )
    if typology == "pass_through":
        for _ in range(int(rng.integers(3, 8))):
            t = rng.uniform(0, span - 48)
            amt = rng.lognormal(8.7, 0.4)
            add(t, "in", amt, f"Sender-{rng.integers(100, 999)}", str(rng.choice(COUNTRIES)), "payment")
            add(
                t + rng.uniform(1, 40),
                "out",
                amt * rng.uniform(0.85, 0.99),
                f"Beneficiary-{rng.integers(100, 999)}",
                str(rng.choice(COUNTRIES)),
                "transfer",
            )
    if typology in ("money_mule", "app_fraud_mule"):
        senders = _cp(rng, "Person", int(rng.integers(18, 40)))
        start = rng.uniform(0, max(1.0, span - 14 * 24))
        for s in senders:
            add(
                start + rng.uniform(0, 13 * 24),
                "in",
                rng.lognormal(5.6, 0.5),
                s,
                home,
                "order" if typology == "app_fraud_mule" else "rent",
            )
        total = sum(t.amount_eur for t in out if t.direction == "in" and t.counterparty.startswith("Person"))
        if typology == "money_mule":
            add(
                start + 14 * 24,
                "out",
                total * 0.9,
                f"Beneficiary-{rng.integers(100, 999)}",
                str(rng.choice(["AE", "TR"])),
                "transfer",
            )
        else:
            for _ in range(3):
                add(
                    start + rng.uniform(14 * 24, 15 * 24),
                    "out",
                    total * 0.3,
                    str(rng.choice(NEW_EXCHANGES)),
                    "MT",
                    "top up",
                )
    if typology == "funnel":
        for _ in range(int(rng.integers(15, 30))):
            add(
                rng.uniform(0, span),
                "in",
                rng.lognormal(7.5, 0.6),
                f"Customer-{rng.integers(100, 999)}",
                str(rng.choice(COUNTRIES)),
                "invoice",
            )
        total = sum(t.amount_eur for t in out if t.direction == "in")
        for _ in range(int(rng.integers(2, 5))):
            add(rng.uniform(span / 2, span), "out", total * 0.25, "Golden Sun Trading FZE", "AE", "goods")
    if typology == "crypto_offramp":
        for _ in range(int(rng.integers(4, 9))):
            add(
                rng.uniform(0, span),
                "out",
                rng.lognormal(7.2, 0.4),
                str(rng.choice(EXCHANGES)),
                str(rng.choice(["MT", "US", "LT"])),
                "top up",
            )
    if typology == "jurisdiction_routing":
        for _ in range(int(rng.integers(5, 10))):
            add(
                rng.uniform(0, span),
                "in",
                rng.lognormal(9.0, 0.4),
                f"Customer-{rng.integers(100, 999)}",
                str(rng.choice(COUNTRIES)),
                "freight",
            )
        for _ in range(int(rng.integers(1, 4))):
            add(
                rng.uniform(0, span),
                "out",
                rng.lognormal(8.8, 0.4),
                f"Agent-{rng.integers(100, 999)}",
                str(rng.choice(HIGH_RISK)),
                "freight charges",
            )
    out.sort(key=lambda t: t.hour)
    for i, t in enumerate(out):
        t.id = f"{case_id}-t{i:03d}"
    return out


def sample_case(
    rng: np.random.Generator,
    case_id: str,
    week: int,
    typology: str | None = None,
    weights: dict[str, float] | None = None,
) -> Case:
    if typology is None:
        w = weights or {k: v[3] for k, v in TYPOLOGIES.items()}
        names = [k for k in w if w[k] > 0]
        p = np.array([w[k] for k in names])
        typology = str(rng.choice(names, p=p / p.sum()))
    _, c_share, b_share, _ = TYPOLOGIES[typology]
    kind = "consumer" if rng.random() < c_share / (c_share + b_share) else "business"
    days = int(rng.choice([60, 90, 120]))
    transfers = _transfers(rng, typology, days, case_id)
    declared = BUSINESS.get(typology, "consulting") if kind == "business" else OCCUPATION.get(typology, "office worker")
    declared_monthly = {"consumer": rng.choice([1500, 2500, 3500]), "business": rng.choice([20000, 50000, 120000])}[
        kind
    ]
    if typology in ("payroll_provider", "marketplace_seller", "small_trader"):
        declared_monthly = max(declared_monthly, 120000)
    c = Case(
        case_id,
        week,
        kind,
        str(rng.choice(COUNTRIES[:7])),
        declared,
        float(declared_monthly),
        int(rng.integers(2, 60)),
        bool(rng.random() < (0.85 if not TYPOLOGIES[typology][0] else 0.3)),
        transfers,
        typology,
    )
    from edd_world.truth import label

    label(c)
    return c
