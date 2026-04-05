"""Walmart Transactability Engine -- Interactive Dashboard.

Four pages:
  1. Evaluation Tester  -- evaluate items against compliance rules
  2. System Overview    -- counts, rule breakdown, recent audit
  3. Live Event Stream  -- Redis Streams viewer (auto-refresh)
  4. Scenario Demo      -- one-click execution of all 10 seed scenarios
"""

from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone

import httpx
import redis
import streamlit as st

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
API_BASE = os.environ.get("API_GATEWAY_URL", "http://nginx:80")
REDIS_URL = os.environ.get("REDIS_URL", "redis://redis:6379")
HTTP_TIMEOUT = 10.0

MARKETS = ["US-CA", "US-TX", "US-CO", "US-UT", "US-MA", "US-NY", "US-HI", "US-KY"]

STATE_FROM_MARKET = {
    "US-CA": "CA",
    "US-TX": "TX",
    "US-CO": "CO",
    "US-UT": "UT",
    "US-MA": "MA",
    "US-NY": "NY",
    "US-HI": "HI",
    "US-KY": "KY",
}

ZIP_FROM_MARKET = {
    "US-CA": "90210",
    "US-TX": "75201",
    "US-CO": "80202",
    "US-UT": "84101",
    "US-MA": "02101",
    "US-NY": "10001",
    "US-HI": "96801",
    "US-KY": "40202",
}

# Known sellers from seed data (since there is no GET /v1/sellers list endpoint)
KNOWN_SELLERS = {
    "None - 1P (Walmart)": None,
    "Acme Wines (trusted)": "00000000-0000-0000-0000-000000000002",
    "TechGear Pro (trusted)": "00000000-0000-0000-0000-000000000003",
    "NewSeller123 (new)": "00000000-0000-0000-0000-000000000004",
    "ChemSupply Inc (standard)": "00000000-0000-0000-0000-000000000005",
}

REDIS_STREAMS = [
    "inventory:state_changes",
    "seller:state_changes",
    "eligibility:evaluations",
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def api_get(path: str) -> dict | list | None:
    """Synchronous GET to the API gateway. Returns parsed JSON or None on error."""
    try:
        with httpx.Client(base_url=API_BASE, timeout=HTTP_TIMEOUT) as client:
            r = client.get(path)
            r.raise_for_status()
            return r.json()
    except Exception as e:
        st.error(f"API GET {path} failed: {e}")
        return None


def api_post(path: str, payload: dict) -> dict | None:
    """Synchronous POST to the API gateway. Returns parsed JSON or None on error."""
    try:
        with httpx.Client(base_url=API_BASE, timeout=HTTP_TIMEOUT) as client:
            r = client.post(path, json=payload)
            return r.json()
    except Exception as e:
        st.error(f"API POST {path} failed: {e}")
        return None


def get_redis() -> redis.Redis | None:
    """Return a synchronous Redis connection, or None if unavailable."""
    try:
        r = redis.from_url(REDIS_URL, decode_responses=True)
        r.ping()
        return r
    except Exception:
        return None


def build_evaluate_payload(
    item_id: str,
    market_code: str,
    seller_id: str | None = None,
    customer_age: int | None = None,
    requested_quantity: int | None = None,
    timestamp_str: str | None = None,
) -> dict:
    """Build a well-formed /v1/evaluate request body."""
    state = STATE_FROM_MARKET.get(market_code, "TX")
    zip_code = ZIP_FROM_MARKET.get(market_code, "75201")
    ts = timestamp_str or datetime.now(timezone.utc).isoformat()
    payload: dict = {
        "item_id": item_id,
        "market_code": market_code,
        "customer_location": {"state": state, "zip": zip_code},
        "timestamp": ts,
    }
    if seller_id:
        payload["seller_id"] = seller_id
    ctx: dict = {}
    if customer_age is not None:
        ctx["customer_age"] = customer_age
    if requested_quantity is not None:
        ctx["requested_quantity"] = requested_quantity
    if ctx:
        payload["context"] = ctx
    return payload


def eligibility_badge(eligible: bool) -> str:
    """Return a colored HTML badge string."""
    if eligible:
        return (
            '<span style="background:#22c55e;color:#fff;padding:4px 14px;'
            'border-radius:6px;font-weight:700;font-size:1.1em;">'
            "ELIGIBLE</span>"
        )
    return (
        '<span style="background:#ef4444;color:#fff;padding:4px 14px;'
        'border-radius:6px;font-weight:700;font-size:1.1em;">'
        "NOT ELIGIBLE</span>"
    )


def path_status_color(status: str) -> str:
    colors = {
        "clear": "#22c55e",
        "conditional": "#eab308",
        "gated": "#f97316",
        "blocked": "#ef4444",
    }
    return colors.get(status, "#6b7280")


# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Transactability Dashboard",
    page_icon="W",
    layout="wide",
)

st.markdown(
    """
    <style>
    .block-container { padding-top: 1.5rem; }
    .metric-card {
        background: #1e293b; color: #e2e8f0; padding: 1.2rem;
        border-radius: 10px; text-align: center;
    }
    .metric-card h2 { margin: 0; font-size: 2.2rem; color: #38bdf8; }
    .metric-card p  { margin: 4px 0 0; font-size: 0.9rem; color: #94a3b8; }
    .event-row {
        background: #0f172a; padding: 0.6rem 1rem; border-radius: 6px;
        margin-bottom: 6px; font-family: monospace; font-size: 0.85rem;
        color: #e2e8f0; border-left: 3px solid #38bdf8;
    }
    .event-row .ts   { color: #64748b; }
    .event-row .type { color: #38bdf8; font-weight: 700; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Walmart Transactability Engine")

tab1, tab2, tab3, tab4 = st.tabs(
    [
        "Evaluation Tester",
        "System Overview",
        "Live Event Stream",
        "Scenario Demo",
    ]
)

# ===== TAB 1 -- Evaluation Tester ==========================================
with tab1:
    st.header("Evaluate Item Eligibility")

    # Fetch items for dropdown
    items_data = api_get("/v1/items")
    if not items_data:
        st.warning("Could not load items from the API. Is the system running?")
        items_data = []

    item_options = {
        f"{it['sku']} - {it['name']}": it["item_id"]
        for it in items_data
    }

    col1, col2 = st.columns(2)
    with col1:
        selected_item_label = st.selectbox(
            "Item", options=list(item_options.keys()) if item_options else ["(no items)"]
        )
        selected_market = st.selectbox("Market Code", options=MARKETS)
        selected_seller_label = st.selectbox(
            "Seller (optional)", options=list(KNOWN_SELLERS.keys())
        )

    with col2:
        customer_age = st.number_input(
            "Customer Age (optional)", min_value=0, max_value=120, value=0, step=1
        )
        requested_qty = st.number_input(
            "Requested Quantity (optional)", min_value=0, max_value=100, value=0, step=1
        )

    if st.button("Evaluate", type="primary", use_container_width=True):
        if not item_options or selected_item_label == "(no items)":
            st.error("No items available to evaluate.")
        else:
            item_id = item_options[selected_item_label]
            seller_id = KNOWN_SELLERS[selected_seller_label]
            age = customer_age if customer_age > 0 else None
            qty = requested_qty if requested_qty > 0 else None

            payload = build_evaluate_payload(
                item_id=item_id,
                market_code=selected_market,
                seller_id=seller_id,
                customer_age=age,
                requested_quantity=qty,
            )

            with st.spinner("Evaluating..."):
                t0 = time.time()
                result = api_post("/v1/evaluate", payload)
                wall_ms = int((time.time() - t0) * 1000)

            if result and "error" not in result:
                eligible = result.get("eligible", False)
                st.markdown(eligibility_badge(eligible), unsafe_allow_html=True)
                st.caption(
                    f"Evaluated {result.get('rules_evaluated', '?')} rules in "
                    f"{result.get('evaluation_ms', '?')}ms (round-trip {wall_ms}ms)"
                )

                # Path results
                paths = result.get("paths", [])
                if paths:
                    st.subheader("Path Results")
                    for p in paths:
                        status = p.get("status", "unknown")
                        color = path_status_color(status)
                        inv = p.get("inventory_available")
                        inv_text = f" | inventory: {inv}" if inv is not None else ""
                        st.markdown(
                            f'<div style="display:inline-block;background:{color};'
                            f'color:#fff;padding:3px 10px;border-radius:4px;'
                            f'font-weight:600;margin-right:8px;">{status.upper()}</div>'
                            f'<b>{p["path_code"]}</b>{inv_text}',
                            unsafe_allow_html=True,
                        )
                        # Show violations
                        for v in p.get("violations", []):
                            st.markdown(
                                f'&nbsp;&nbsp;&nbsp;&nbsp;BLOCK: {v["rule_name"]} -- {v["reason"]}'
                            )
                        for req in p.get("requirements", []):
                            sat = "satisfied" if req.get("satisfied") else "NOT satisfied"
                            st.markdown(
                                f'&nbsp;&nbsp;&nbsp;&nbsp;REQUIRE ({sat}): '
                                f'{req["rule_name"]} -- {req["reason"]}'
                            )
                        for g in p.get("gates", []):
                            st.markdown(
                                f'&nbsp;&nbsp;&nbsp;&nbsp;GATE: {g["rule_name"]} -- {g["reason"]}'
                            )

                # Warnings
                warnings = result.get("warnings", [])
                if warnings:
                    st.subheader("Warnings")
                    for w in warnings:
                        st.warning(f"[{w.get('rule_name', '?')}] {w.get('reason', '')}")

                # Errors
                errors = result.get("errors", [])
                if errors:
                    st.subheader("Errors")
                    for e in errors:
                        st.error(str(e))

                # Conflict resolutions
                conflicts = result.get("conflict_resolutions", [])
                if conflicts:
                    st.subheader("Conflict Resolutions")
                    for c in conflicts:
                        st.info(
                            f"Rule '{c.get('winner_rule_name')}' (#{c.get('winner_rule_id')}) "
                            f"suppressed '{c.get('suppressed_rule_name')}' "
                            f"(#{c.get('suppressed_rule_id')}): {c.get('reason', '')}"
                        )

                # Raw JSON expander
                with st.expander("Raw Response JSON"):
                    st.json(result)

            elif result:
                st.error(f"Evaluation error: {result.get('detail', result)}")

# ===== TAB 2 -- System Overview ============================================
with tab2:
    st.header("System Overview")

    # Fetch counts
    items_list = api_get("/v1/items")
    rules_list = api_get("/v1/rules")

    item_count = len(items_list) if items_list else 0
    rule_count = len(rules_list) if rules_list else 0
    seller_count = len(KNOWN_SELLERS) - 1  # exclude "None - 1P"
    market_count = len(MARKETS)

    # Metric cards
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(
            f'<div class="metric-card"><h2>{item_count}</h2><p>Items</p></div>',
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f'<div class="metric-card"><h2>{rule_count}</h2><p>Compliance Rules</p></div>',
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            f'<div class="metric-card"><h2>{seller_count}</h2><p>Sellers</p></div>',
            unsafe_allow_html=True,
        )
    with c4:
        st.markdown(
            f'<div class="metric-card"><h2>{market_count}</h2><p>Markets</p></div>',
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # Rules breakdown by action type
    if rules_list:
        st.subheader("Rules by Action Type")
        action_counts: dict[str, int] = {}
        for r in rules_list:
            action = r.get("action", "UNKNOWN")
            action_counts[action] = action_counts.get(action, 0) + 1

        cols = st.columns(len(action_counts))
        action_colors = {
            "BLOCK": "#ef4444",
            "WARN": "#eab308",
            "REQUIRE": "#3b82f6",
            "GATE": "#f97316",
        }
        for i, (action, count) in enumerate(sorted(action_counts.items())):
            color = action_colors.get(action, "#6b7280")
            with cols[i]:
                st.markdown(
                    f'<div style="text-align:center;padding:1rem;'
                    f'border-radius:8px;border:2px solid {color};">'
                    f'<span style="font-size:2rem;font-weight:700;color:{color};">'
                    f"{count}</span><br/>"
                    f'<span style="color:{color};font-weight:600;">{action}</span></div>',
                    unsafe_allow_html=True,
                )

        st.markdown("---")

        # Rules table
        st.subheader("All Rules")
        st.dataframe(
            [
                {
                    "ID": r["rule_id"],
                    "Name": r["rule_name"],
                    "Action": r["action"],
                    "Priority": r["priority"],
                    "Enabled": r["enabled"],
                }
                for r in rules_list
            ],
            use_container_width=True,
            hide_index=True,
        )

    # Recent audit log from Redis stream
    st.markdown("---")
    st.subheader("Recent Audit (Eligibility Evaluations)")
    rd = get_redis()
    if rd:
        try:
            entries = rd.xrevrange("eligibility:evaluations", count=10)
            if entries:
                for msg_id, data in entries:
                    ts = data.get("timestamp", "")
                    evt = data.get("event_type", "")
                    raw = data.get("data", "{}")
                    try:
                        parsed = json.loads(raw)
                    except Exception:
                        parsed = raw
                    st.markdown(
                        f'<div class="event-row">'
                        f'<span class="ts">{ts}</span> '
                        f'<span class="type">{evt}</span> '
                        f"{json.dumps(parsed, indent=None)}</div>",
                        unsafe_allow_html=True,
                    )
            else:
                st.info("No evaluation events yet. Run some evaluations first.")
        except Exception as e:
            st.warning(f"Could not read audit stream: {e}")
    else:
        st.warning("Redis not available -- cannot show audit log.")

# ===== TAB 3 -- Live Event Stream ==========================================
with tab3:
    st.header("Live Event Stream")
    st.caption("Showing the last 50 events from each Redis stream. Auto-refreshes every 5 seconds.")

    auto_refresh = st.checkbox("Auto-refresh (5s)", value=False)
    if auto_refresh:
        time.sleep(5)
        st.rerun()

    rd3 = get_redis()
    if rd3:
        for stream_name in REDIS_STREAMS:
            st.subheader(f"Stream: {stream_name}")
            try:
                entries = rd3.xrevrange(stream_name, count=50)
                if entries:
                    for msg_id, data in entries:
                        ts = data.get("timestamp", "")
                        evt = data.get("event_type", "")
                        raw = data.get("data", "{}")
                        try:
                            parsed = json.loads(raw)
                            detail = json.dumps(parsed, indent=None)
                        except Exception:
                            detail = str(raw)
                        st.markdown(
                            f'<div class="event-row">'
                            f'<span class="ts">{msg_id}</span> '
                            f'<span class="type">{evt}</span> '
                            f"{detail}</div>",
                            unsafe_allow_html=True,
                        )
                else:
                    st.info(f"No events in {stream_name} yet.")
            except Exception as e:
                st.warning(f"Error reading {stream_name}: {e}")
    else:
        st.warning("Redis not available.")

# ===== TAB 4 -- Scenario Demo ==============================================
with tab4:
    st.header("Scenario Demo")
    st.caption(
        "Click any scenario button to run the evaluation and see the result. "
        "Scenarios match the 10 demo scenarios from the seed data."
    )

    # We need item IDs -- fetch them
    items_for_demo = api_get("/v1/items")
    sku_map: dict[str, str] = {}
    if items_for_demo:
        for it in items_for_demo:
            sku_map[it["sku"]] = it["item_id"]

    if not sku_map:
        st.error(
            "Could not load items. Make sure the seed script has been run "
            "and all services are healthy."
        )
    else:
        # Helper to run a scenario
        def run_scenario(label: str, payload: dict):
            """Execute a scenario and display results inline."""
            with st.spinner(f"Running: {label}..."):
                t0 = time.time()
                result = api_post("/v1/evaluate", payload)
                wall_ms = int((time.time() - t0) * 1000)
            if result and "error" not in result:
                eligible = result.get("eligible", False)
                st.markdown(eligibility_badge(eligible), unsafe_allow_html=True)
                st.caption(
                    f"{result.get('rules_evaluated', '?')} rules, "
                    f"{result.get('evaluation_ms', '?')}ms engine, "
                    f"{wall_ms}ms round-trip"
                )
                # Path summary
                for p in result.get("paths", []):
                    status = p.get("status", "unknown")
                    color = path_status_color(status)
                    st.markdown(
                        f'&nbsp;&nbsp;<span style="background:{color};color:#fff;'
                        f'padding:2px 8px;border-radius:3px;font-size:0.85em;">'
                        f'{status.upper()}</span> **{p["path_code"]}**',
                        unsafe_allow_html=True,
                    )
                for w in result.get("warnings", []):
                    st.warning(f"{w.get('rule_name')}: {w.get('reason')}")
                for c in result.get("conflict_resolutions", []):
                    st.info(
                        f"Conflict: {c.get('winner_rule_name')} suppressed "
                        f"{c.get('suppressed_rule_name')}"
                    )
                with st.expander("Full Response"):
                    st.json(result)
            elif result:
                st.error(f"Error: {result}")

        # --- Scenario 1 ---
        st.markdown("---")
        st.subheader("Scenario 1: Wine in Utah vs Colorado")
        st.markdown(
            "**Utah** prohibits all alcohol delivery. **Colorado** allows it "
            "(with age verification)."
        )
        s1a, s1b = st.columns(2)
        with s1a:
            if st.button("Wine in Utah (BLOCKED)", key="s1a"):
                if "ALC-001" in sku_map:
                    run_scenario(
                        "Wine in Utah",
                        build_evaluate_payload(
                            sku_map["ALC-001"], "US-UT",
                            timestamp_str="2026-07-04T14:00:00-06:00",
                        ),
                    )
        with s1b:
            if st.button("Wine in Colorado (ALLOWED)", key="s1b"):
                if "ALC-001" in sku_map:
                    run_scenario(
                        "Wine in Colorado",
                        build_evaluate_payload(
                            sku_map["ALC-001"], "US-CO", customer_age=25,
                            timestamp_str="2026-07-04T14:00:00-06:00",
                        ),
                    )

        # --- Scenario 2 ---
        st.markdown("---")
        st.subheader("Scenario 2: Pool Chlorine -- Hazmat Path Restrictions")
        st.markdown(
            "Hazmat items **cannot be shipped** via standard carriers. "
            "Pickup is allowed."
        )
        if st.button("Pool Chlorine in Texas", key="s2"):
            if "CHEM-001" in sku_map:
                run_scenario(
                    "Pool Chlorine",
                    build_evaluate_payload(
                        sku_map["CHEM-001"], "US-TX",
                        timestamp_str="2026-07-04T14:00:00-05:00",
                    ),
                )

        # --- Scenario 3 ---
        st.markdown("---")
        st.subheader("Scenario 3: Fireworks -- Seasonal + Geographic Restrictions")
        st.markdown(
            "Fireworks are pickup-only, season-gated (Jun-Jul), "
            "and totally banned in **MA** and **NY**."
        )
        s3a, s3b, s3c = st.columns(3)
        with s3a:
            if st.button("TX in July (IN SEASON)", key="s3a"):
                if "FIRE-001" in sku_map:
                    run_scenario(
                        "Fireworks TX July",
                        build_evaluate_payload(
                            sku_map["FIRE-001"], "US-TX",
                            timestamp_str="2026-07-04T14:00:00-05:00",
                        ),
                    )
        with s3b:
            if st.button("TX in October (OFF SEASON)", key="s3b"):
                if "FIRE-001" in sku_map:
                    run_scenario(
                        "Fireworks TX October",
                        build_evaluate_payload(
                            sku_map["FIRE-001"], "US-TX",
                            timestamp_str="2026-10-15T14:00:00-05:00",
                        ),
                    )
        with s3c:
            if st.button("Massachusetts (TOTAL BAN)", key="s3c"):
                if "FIRE-001" in sku_map:
                    run_scenario(
                        "Fireworks MA",
                        build_evaluate_payload(
                            sku_map["FIRE-001"], "US-MA",
                            timestamp_str="2026-07-04T14:00:00-04:00",
                        ),
                    )

        # --- Scenario 4 ---
        st.markdown("---")
        st.subheader("Scenario 4: Supplement -- CA Prop 65 Warning")
        st.markdown(
            "Supplements with Prop 65 tags get a **warning** in California, "
            "but remain eligible."
        )
        if st.button("Supplement in California", key="s4"):
            if "SUPP-001" in sku_map:
                run_scenario(
                    "Supplement CA Prop 65",
                    build_evaluate_payload(
                        sku_map["SUPP-001"], "US-CA",
                        timestamp_str="2026-07-04T14:00:00-07:00",
                    ),
                )

        # --- Scenario 5 ---
        st.markdown("---")
        st.subheader("Scenario 5: Firearms -- 1P Allowed (with age), 3P Blocked")
        st.markdown(
            "Firearms are **prohibited** on the 3P marketplace. "
            "1P paths require age 21+ verification."
        )
        s5a, s5b = st.columns(2)
        with s5a:
            if st.button("Rifle, 1P, Age 25 (ALLOWED)", key="s5a"):
                if "FIRE-002" in sku_map:
                    run_scenario(
                        "Rifle 1P age 25",
                        build_evaluate_payload(
                            sku_map["FIRE-002"], "US-TX", customer_age=25,
                            timestamp_str="2026-07-04T14:00:00-05:00",
                        ),
                    )
        with s5b:
            if st.button("Rifle, No Age (REQUIRE)", key="s5b"):
                if "FIRE-002" in sku_map:
                    run_scenario(
                        "Rifle no age",
                        build_evaluate_payload(
                            sku_map["FIRE-002"], "US-TX",
                            timestamp_str="2026-07-04T14:00:00-05:00",
                        ),
                    )

        # --- Scenario 6 ---
        st.markdown("---")
        st.subheader("Scenario 6: Seller Hazmat Quality Gate")
        st.markdown(
            "ChemSupply has a 4.5% defect rate, exceeding the 3% threshold "
            "for hazmat sellers. Marketplace path is **gated**."
        )
        if st.button("Raid Spray via ChemSupply (GATED)", key="s6"):
            if "CHEM-002" in sku_map:
                run_scenario(
                    "Raid ChemSupply",
                    build_evaluate_payload(
                        sku_map["CHEM-002"], "US-TX",
                        seller_id="00000000-0000-0000-0000-000000000005",
                        timestamp_str="2026-07-04T14:00:00-05:00",
                    ),
                )

        # --- Scenario 7 ---
        st.markdown("---")
        st.subheader("Scenario 7: 3P Alcohol -- Seller Trust Gate")
        st.markdown(
            "Alcohol on the marketplace requires **trusted** or **top_rated** tier. "
            "Acme Wines (trusted) passes; NewSeller123 (new) is gated."
        )
        s7a, s7b = st.columns(2)
        with s7a:
            if st.button("White Claw via Acme Wines (ALLOWED)", key="s7a"):
                if "ALC-003" in sku_map:
                    run_scenario(
                        "White Claw Acme",
                        build_evaluate_payload(
                            sku_map["ALC-003"], "US-CO",
                            seller_id="00000000-0000-0000-0000-000000000002",
                            customer_age=25,
                            timestamp_str="2026-07-04T14:00:00-06:00",
                        ),
                    )
        with s7b:
            if st.button("Bourbon via NewSeller123 (GATED)", key="s7b"):
                if "ALC-002" in sku_map:
                    run_scenario(
                        "Bourbon NewSeller",
                        build_evaluate_payload(
                            sku_map["ALC-002"], "US-CO",
                            seller_id="00000000-0000-0000-0000-000000000004",
                            customer_age=25,
                            timestamp_str="2026-07-04T14:00:00-06:00",
                        ),
                    )

        # --- Scenario 8 ---
        st.markdown("---")
        st.subheader("Scenario 8: Electronics -- Seller Trust Gate")
        st.markdown(
            "Electronics on the marketplace require **trusted** or **top_rated** tier. "
            "TechGear Pro passes; NewSeller123 is gated."
        )
        s8a, s8b = st.columns(2)
        with s8a:
            if st.button("Samsung via TechGear (ALLOWED)", key="s8a"):
                if "ELEC-001" in sku_map:
                    run_scenario(
                        "Samsung TechGear",
                        build_evaluate_payload(
                            sku_map["ELEC-001"], "US-TX",
                            seller_id="00000000-0000-0000-0000-000000000003",
                            timestamp_str="2026-07-04T14:00:00-05:00",
                        ),
                    )
        with s8b:
            if st.button("Samsung via NewSeller123 (GATED)", key="s8b"):
                if "ELEC-001" in sku_map:
                    run_scenario(
                        "Samsung NewSeller",
                        build_evaluate_payload(
                            sku_map["ELEC-001"], "US-TX",
                            seller_id="00000000-0000-0000-0000-000000000004",
                            timestamp_str="2026-07-04T14:00:00-05:00",
                        ),
                    )

        # --- Scenario 9 ---
        st.markdown("---")
        st.subheader("Scenario 9: Pseudoephedrine -- Quantity Limit + ID Required")
        st.markdown(
            "Pseudoephedrine requires ID (18+) and is limited to 3 packages. "
            "Qty=2 passes; qty=5 is **blocked**."
        )
        s9a, s9b = st.columns(2)
        with s9a:
            if st.button("Sudafed qty=2, age 30 (ALLOWED)", key="s9a"):
                if "PHARM-001" in sku_map:
                    run_scenario(
                        "Sudafed qty 2",
                        build_evaluate_payload(
                            sku_map["PHARM-001"], "US-TX",
                            customer_age=30, requested_quantity=2,
                            timestamp_str="2026-07-04T14:00:00-05:00",
                        ),
                    )
        with s9b:
            if st.button("Sudafed qty=5, age 30 (BLOCKED)", key="s9b"):
                if "PHARM-001" in sku_map:
                    run_scenario(
                        "Sudafed qty 5",
                        build_evaluate_payload(
                            sku_map["PHARM-001"], "US-TX",
                            customer_age=30, requested_quantity=5,
                            timestamp_str="2026-07-04T14:00:00-05:00",
                        ),
                    )

        # --- Scenario 10 ---
        st.markdown("---")
        st.subheader("Scenario 10: Inventory Depletion")
        st.markdown(
            "Organic Whole Milk starts with qty=50. After depleting inventory, "
            "it should become **not eligible** on inventory-dependent paths."
        )
        s10a, s10b = st.columns(2)
        with s10a:
            if st.button("Check Milk (should be in stock)", key="s10a"):
                if "GROC-001" in sku_map:
                    run_scenario(
                        "Milk check",
                        build_evaluate_payload(
                            sku_map["GROC-001"], "US-TX",
                            timestamp_str="2026-07-04T14:00:00-05:00",
                        ),
                    )
        with s10b:
            if st.button("Deplete Milk Inventory (delta=-50)", key="s10b"):
                if "GROC-001" in sku_map:
                    with st.spinner("Depleting inventory..."):
                        depl_result = api_post(
                            "/v1/inventory/events",
                            {
                                "item_id": sku_map["GROC-001"],
                                "fulfillment_node": "FC-DAL-01",
                                "event_type": "adjustment",
                                "path_id": 1,
                                "seller_id": "00000000-0000-0000-0000-000000000001",
                                "delta": -50,
                            },
                        )
                    if depl_result:
                        new_qty = depl_result.get("new_available_qty", "?")
                        st.success(
                            f"Inventory depleted. New available qty: {new_qty}. "
                            "Now click 'Check Milk' again to see it become not eligible."
                        )
