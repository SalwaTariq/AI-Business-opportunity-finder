"""AI Small Business Opportunity Finder - a single-file Streamlit app.

How it works:
1. The user fills in a form.
2. We send the details to Google Gemini and ask for 5 business ideas as JSON.
3. We show each idea with a budget table (totals added by Python), a market
   analysis, and a profit simulator.
"""
import json
import time

import streamlit as st
from google import genai
from google.genai import types

# The Gemini model to use. If Google retires it, change this one line.
MODEL = "gemini-3.8-flash"

st.set_page_config(page_title="AI Business Opportunity Finder", page_icon="💡", layout="wide")


# ======================= HELPER FUNCTIONS =======================
def get_client():
    """Create the Gemini client using the key saved in Streamlit secrets."""
    try:
        return genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
    except Exception:
        return None


def validate(country, city, budget, skills, interests):
    """Check the form. Returns a list of error messages (empty = all good)."""
    errors = []
    if not country.strip():
        errors.append("Country is required.")
    if not city.strip():
        errors.append("City or location is required.")
    if budget <= 0:
        errors.append("Budget must be greater than 0.")
    if len(skills.strip()) < 3:
        errors.append("Please describe your skills and experience.")
    if len(interests.strip()) < 3:
        errors.append("Please describe your business interests.")
    return errors


def build_prompt(u):
    """Write the instructions that we send to Gemini."""
    pakistan_note = ""
    if u["country"].strip().lower() == "pakistan":
        pakistan_note = (
            "PAKISTAN MODE: Consider local realities such as load-shedding, cash on delivery, "
            "selling via WhatsApp/Facebook/Instagram, Daraz, Foodpanda, local wholesale markets, "
            "informal rent, and prices in PKR. Prefer ideas that work in Pakistani cities and towns.\n"
        )
    return f"""You are a careful small-business consultant.
{pakistan_note}User profile: {json.dumps(u)}
Suggest exactly 5 realistic, personalised business ideas that fit the user's budget, location,
skills, interests, daily time, business type, risk tolerance and work style.
All costs must be plain numbers in {u['currency']} and each idea's total must stay within the budget.
Do NOT claim that you did live market research. All market points are AI assumptions.
Return ONLY JSON in exactly this shape:
{{"ideas":[{{"name":"","description":"","why_it_suits":"","target_customers":"",
"required_resources":"","earning_model":"","difficulty":"Easy|Medium|Hard",
"challenges":["",""],
"budget":{{"equipment":0,"materials":0,"packaging":0,"marketing":0,"transportation":0,"other":0}},
"market":{{"potential_customers":"","customer_needs":"","demand":"","competitors":"",
"advantages":"","challenges":"","differentiation":""}},
"sim_defaults":{{"price":0,"daily_sales":0,"cost_per_unit":0,"other_monthly_expenses":0}}}}]}}"""


def try_model(client, model, user, config):
    """Ask one model for ideas. If it is busy (503) wait and retry up to 4 times."""
    for attempt in range(4):
        try:
            response = client.models.generate_content(
                model=model, contents=build_prompt(user), config=config
            )
            text = response.text.strip().removeprefix("```json").removesuffix("```").strip()
            return json.loads(text)["ideas"]
        except Exception as ex:
            msg = str(ex)
            busy = "503" in msg or "UNAVAILABLE" in msg
            if busy and attempt < 3:
                time.sleep(2 ** (attempt + 1))  # wait 2s, 4s, 8s
                continue
            raise  # 429 quota or other errors: do not waste more requests


def backup_models(client, main_model):
    """Ask Google which Flash text models this key can use, so we never guess names."""
    skip = ("image", "tts", "audio", "live", "embed", "vision", "robotics", "computer", "pro")
    try:
        names = [
            m.name.replace("models/", "")
            for m in client.models.list()
            if "generateContent" in (m.supported_actions or [])
            and "flash" in m.name.lower()
            and not any(word in m.name.lower() for word in skip)
        ]
        return [n for n in names if n != main_model][:5]
    except Exception:
        return []


def generate_ideas(client, user, main_model):
    """Try the main model, then every backup Flash model, until one works.
    Each model has its own free daily quota, so switching models often fixes 429/404 errors."""
    config = types.GenerateContentConfig(response_mime_type="application/json", temperature=0.7)
    errors = []
    for model in [main_model] + backup_models(client, main_model):
        try:
            return try_model(client, model, user, config)
        except Exception as ex:
            errors.append(f"{model}: {str(ex)[:150]}")
    raise Exception(" | ".join(errors))


@st.cache_data(show_spinner=False, ttl=3600)
def cached_generate(user_json, main_model, _client):
    """Same inputs within 1 hour reuse the saved answer (saves your free daily quota)."""
    return generate_ideas(_client, json.loads(user_json), main_model)


def num(value, default=0.0):
    """Safely turn AI output into a number."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


# ======================= PAGE HEADER =======================
st.title("💡 AI Small Business Opportunity Finder")
st.caption("Get personalised business ideas, budgets, market analysis and a profit simulator.")

client = get_client()
if client is None:
    st.error("Gemini API key not found. Add GEMINI_API_KEY to .streamlit/secrets.toml "
             "(local) or to Secrets in Streamlit Cloud.")
    st.stop()

# Optional: type a different Gemini model name here if the default keeps failing.
main_model = st.sidebar.text_input("Gemini model (optional)", value=MODEL,
                                   help="If you see model or quota errors, try another model name from Google AI Studio.").strip() or MODEL

# ======================= INPUT FORM =======================
with st.form("user_form"):
    c1, c2 = st.columns(2)
    country = c1.text_input("Country", value="Pakistan")
    city = c2.text_input("City or location", placeholder="e.g. Peshawar")

    c3, c4 = st.columns(2)
    budget = c3.number_input("Available startup budget", min_value=0.0, value=100000.0, step=1000.0)
    currency = c4.selectbox("Currency", ["PKR", "USD", "INR", "GBP", "EUR", "AED", "SAR", "Other"])

    skills = st.text_area("Skills and experience", placeholder="e.g. cooking, Excel, graphic design")
    interests = st.text_area("Business interests", placeholder="e.g. food, e-commerce, education")

    c5, c6 = st.columns(2)
    hours = c5.slider("Available time per day (hours)", 0.5, 16.0, 4.0, 0.5)
    btype = c6.selectbox("Preferred business type", [
        "Any suitable business", "Online business", "Physical business",
        "Home-based business", "Service-based business", "Food business"])

    c7, c8 = st.columns(2)
    risk = c7.radio("Risk tolerance", ["Low", "Medium", "High"], horizontal=True, index=1)
    team = c8.radio("Work style", ["Alone", "With a team"], horizontal=True)

    submitted = st.form_submit_button("Generate Business Ideas", type="primary")

if submitted:
    errors = validate(country, city, budget, skills, interests)
    if errors:
        for e in errors:
            st.error(e)
    else:
        user = {"country": country, "city": city, "budget": budget, "currency": currency,
                "skills": skills, "interests": interests, "hours_per_day": hours,
                "business_type": btype, "risk_tolerance": risk, "work_style": team}
        try:
            with st.spinner("Thinking like a business consultant..."):
                st.session_state["ideas"] = cached_generate(json.dumps(user, sort_keys=True), main_model, client)
                st.session_state["user"] = user
        except Exception as ex:
            if "429" in str(ex) or "RESOURCE_EXHAUSTED" in str(ex):
                st.error("Your free Gemini daily limit is used up (about 20 requests per day per model). "
                         "Try again later, use a new API key from another Google project, or enable billing.")
            else:
                st.error(f"Something went wrong: {ex}. Please try again.")

# ======================= RESULTS =======================
# Results live in session_state so moving a slider does not erase them.
if "ideas" in st.session_state:
    user = st.session_state["user"]
    cur = user["currency"]
    st.divider()
    st.subheader("Your 5 personalised ideas")
    st.info("⚠️ Everything below is an AI-generated **assumption**. No live market research was done. "
            "Verify prices and demand locally before investing.")

    for i, idea in enumerate(st.session_state["ideas"]):
        title = f"{i + 1}. {idea.get('name', 'Business')}  •  {idea.get('difficulty', '?')}"
        with st.expander(title, expanded=(i == 0)):
            t1, t2, t3, t4 = st.tabs(["Overview", "Budget", "Market (AI assumptions)", "Profit simulator"])

            # ---- Overview ----
            with t1:
                st.write(idea.get("description", ""))
                st.markdown(f"**Why it suits you:** {idea.get('why_it_suits', '')}")
                st.markdown(f"**Target customers:** {idea.get('target_customers', '')}")
                st.markdown(f"**Required resources:** {idea.get('required_resources', '')}")
                st.markdown(f"**Earning model:** {idea.get('earning_model', '')}")
                st.markdown("**Potential challenges:**")
                for ch in idea.get("challenges", []):
                    st.write(f"- {ch}")

            # ---- Budget (Python adds the total, not the AI) ----
            with t2:
                b = idea.get("budget", {})
                labels = {"equipment": "Equipment", "materials": "Raw materials / inventory",
                          "packaging": "Packaging", "marketing": "Marketing",
                          "transportation": "Transportation", "other": "Other initial expenses"}
                rows = {labels[k]: num(b.get(k)) for k in labels}
                total = sum(rows.values())
                st.table({"Item": list(rows.keys()),
                          f"Cost ({cur})": [f"{v:,.0f}" for v in rows.values()]})
                st.metric("Estimated total investment", f"{cur} {total:,.0f}")
                if total > user["budget"]:
                    st.warning(f"This is above your budget of {cur} {user['budget']:,.0f}.")
                else:
                    st.success(f"Within your budget. Remaining: {cur} {user['budget'] - total:,.0f}")

            # ---- Market analysis ----
            with t3:
                m = idea.get("market", {})
                for key, label in [("potential_customers", "Potential customers"),
                                   ("customer_needs", "Customer needs"),
                                   ("demand", "Market demand"),
                                   ("competitors", "Possible competitors"),
                                   ("advantages", "Business advantages"),
                                   ("challenges", "Market challenges"),
                                   ("differentiation", "How to differentiate")]:
                    st.markdown(f"**{label}:** {m.get(key, '')}")

            # ---- Profit simulator ----
            with t4:
                d = idea.get("sim_defaults", {})
                s1, s2 = st.columns(2)
                price = s1.number_input("Selling price per unit", min_value=0.0,
                                        value=num(d.get("price"), 100), key=f"p{i}")
                units = s2.number_input("Expected daily sales (units)", min_value=0.0,
                                        value=num(d.get("daily_sales"), 10), key=f"u{i}")
                s3, s4 = st.columns(2)
                days = s3.slider("Operating days per month", 1, 31, 26, key=f"d{i}")
                cost = s4.number_input("Cost per unit", min_value=0.0,
                                       value=num(d.get("cost_per_unit"), 50), key=f"c{i}")
                other = st.number_input("Other monthly expenses", min_value=0.0,
                                        value=num(d.get("other_monthly_expenses"), 0), key=f"o{i}")

                revenue = price * units * days
                costs = cost * units * days + other
                profit = revenue - costs
                margin = (profit / revenue * 100) if revenue else 0

                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Monthly revenue", f"{revenue:,.0f}")
                m2.metric("Monthly costs", f"{costs:,.0f}")
                m3.metric("Monthly profit", f"{profit:,.0f}")
                m4.metric("Profit margin", f"{margin:.1f}%")

                invest = sum(num(v) for v in idea.get("budget", {}).values())
                if profit > 0 and invest > 0:
                    st.info(f"Estimated payback time: about {invest / profit:.1f} months.")
                elif profit <= 0:
                    st.warning("At these numbers the business loses money. Try a higher price or lower costs.")
