from flask import Flask, render_template, request, jsonify
import datetime
import re

app = Flask(__name__)

# ====== Biz info ======
PHONE_DISPLAY = "90820 29585"
PHONE_TEL = "+919082029585"
WHATSAPP_LINK = f"https://wa.me/{PHONE_TEL.replace('+','')}?text=Hello!%20I%27d%20like%20a%20pest%20control%20quote."
SERVICE_AREAS = ["Mumbai", "Thane", "Navi Mumbai"]
SERVICE_HOURS = "8:00 AM – 6:00 PM"

# ====== i18n strings ======
T = {
    "en": {
        "welcome": "Welcome to Pest Pal! Pick a treatment below or ask anything.",
        "areas_hours": "Serving: {areas} • Hours: {hours}",
        "call_now": "Call Now",
        "whatsapp": "WhatsApp",
        "negotiable": "Note: On call, pricing can be slightly negotiable.",
        "prices": "Prices",
        "call_for_quote": "Please call us for a quote.",
        "unknown": "Sorry, I didn’t catch that. Tap a treatment above or type again.",
    },
    "hi": {
        "welcome": "Pest Pal में आपका स्वागत है! नीचे से ट्रीटमेंट चुनें या अपना सवाल लिखें।",
        "areas_hours": "Service Areas: {areas} • समय: {hours}",
        "call_now": "कॉल करें",
        "whatsapp": "व्हाट्सऐप",
        "negotiable": "नोट: कॉल पर कीमत थोड़ी कम/नेगोशिएट हो सकती है।",
        "prices": "कीमतें",
        "call_for_quote": "कृपया कोटेशन के लिए कॉल करें।",
        "unknown": "माफ़ कीजिए, समझ नहीं आया। ऊपर से कोई ट्रीटमेंट चुनें या दोबारा लिखें।",
    },
    "mr": {
        "welcome": "Pest Pal मध्ये आपले स्वागत! खालील उपचार निवडा किंवा प्रश्न विचारा.",
        "areas_hours": "सेवा क्षेत्र: {areas} • वेळ: {hours}",
        "call_now": "कॉल करा",
        "whatsapp": "व्हॉट्सअ‍ॅप",
        "negotiable": "टीप: कॉलवर किंमत थोडी नेगोशिएबल आहे.",
        "prices": "किंमत",
        "call_for_quote": "कृपया कोटसाठी कॉल करा.",
        "unknown": "क्षमस्व, समजले नाही. वरील उपचार निवडा किंवा पुन्हा टाइप करा.",
    },
}

# ====== Services (only 4 show prices; others = call-for-quote) ======
# Termite (from PDF) 
TERMITE_PRICES = {
    "1 BHK": "₹2,500 (3 services)",
    "2 BHK": "₹3,500 (3 services)",
    "3 BHK": "₹4,500 (3 services)",
    "4 BHK": "₹5,500 (3 services)"
}
# General/Cockroaches (from PDF) 
GENERAL_SINGLE = {"1 BHK": "₹900", "2 BHK": "₹1,100", "3 BHK": "₹1,500", "4 BHK": "₹2,000"}
GENERAL_AMC = {"1 BHK": "₹2,000 (3 services)", "2 BHK": "₹2,500 (3 services)", "3 BHK": "₹3,500 (3 services)", "4 BHK": "₹3,600 (3 services)"}
# Bed Bugs (from PDF) 
BEDBUGS_1 = {"1 RK": "₹750", "1 BHK": "₹1,000", "2 BHK": "₹1,400", "3 BHK": "₹1,800"}
BEDBUGS_2 = {"1 RK": "₹1,400", "1 BHK": "₹1,800", "2 BHK": "₹2,500", "3 BHK": "₹3,200"}

SERVICES = {
    "general": {
        "icon": "🛡️",
        "title": {"en": "General Treatment", "hi": "जनरल ट्रीटमेंट", "mr": "जनरल ट्रीटमेंट"},
        "desc": {
            "en": (
                "Whole-home general pest control covering cockroaches, ants, lizards, spiders and flies. "
                "Odourless spray throughout kitchen, bedrooms and corners; gel in sensitive areas."
            ),
            "hi": (
                "पूरे घर की जनरल पेस्ट कंट्रोल सेवा—कॉकरोच, चींटी, छिपकली, मकड़ी वगैरह। "
                "किचन/कमरों में बिना गंध की स्प्रे और संवेदनशील जगहों पर जेल।"
            ),
            "mr": (
                "संपूर्ण घरासाठी जनरल पेस्ट कंट्रोल—कॉक्रोच, मुंग्या, पाल, कोळी इ. "
                "किचन/रूममध्ये बिना वासाची स्प्रे, संवेदनशील भागात जेल."
            ),
        },
        "prices": {"Single Service": GENERAL_SINGLE, "AMC": GENERAL_AMC},
        "notes": {"en":"Safe for kids & pets.","hi":"बच्चों/पालतू के लिए सुरक्षित।","mr":"मुलां/पाल्यांसाठी सुरक्षित."},
    },
    "cockroaches": {
        "icon": "🪳",
        "title": {"en": "Cockroaches", "hi": "कॉकरोच", "mr": "कॉक्रोच"},
        "desc": {
            "en": "Targeted cockroach program: odourless spray + kitchen gel bait; hits adults, nymphs and breeding points.",
            "hi": "टार्गेटेड कॉकरोच ट्रीटमेंट: बिना गंध की स्प्रे + किचन में जेल; बड़ों, निम्फ व ब्रीडिंग पॉइंट्स पर असर।",
            "mr": "लक्ष्यित कॉक्रोच उपचार: बिना वासाची स्प्रे + किचन जेल; प्रौढ, निम्फ व ब्रीडिंग पॉइंट्सवर प्रभाव."
        },
        "prices": {"Single Service": GENERAL_SINGLE, "AMC": GENERAL_AMC},
        "notes": {"en":"Result within 24–48 hrs.","hi":"24–48 घंटे में असर दिखेगा।","mr":"24–48 तासात परिणाम दिसेल."},
    },
    "bedbugs": {
        "icon": "🛏️",
        "title": {"en": "Bed Bugs", "hi": "खटमल", "mr": "खटमळ"},
        "desc": {
            "en": "Two-visit program. Spray on mattresses, bed frames/joints, sofas (top & bottom), cushions and crevices. "
                  "2nd visit after 15–20 days to break the egg cycle.",
            "hi": "दो विज़िट। गद्दे, बेड फ्रेम/जॉइन्ट्स, सोफे (ऊपर-नीचे), कुशन व दरारों में स्प्रे। 15–20 दिनों बाद दूसरी सेवा।",
            "mr": "दोन भेटी. गाद्या, बेड फ्रेम/जॉइंट्स, सोफा (वर-खाली), कुशन व फटींमध्ये स्प्रे. 15–20 दिवसांनी दुसरी सेवा."
        },
        "prices": {"1 Service": BEDBUGS_1, "2 Services (with warranty)": BEDBUGS_2},
        "notes": {"en":"Use odourless, non-staining insecticide; safe for families.","hi":"बिना गंध/दाग वाले सेफ कीटनाशक।","mr":"बिना वास/डाग नसलेला सुरक्षित कीटकनाशक."},
    },
    "termite": {
        "icon": "🪵",
        "title": {"en": "Termite", "hi": "दीमक", "mr": "उंदीर दीमक? नाही—देवमाशी"},  # Marathi title simplified below
        "title": {"en":"Termite","hi":"दीमक","mr":"टर्माईट"},
        "desc": {
            "en": "Anti-termite drilling at floor-wall junction every ~12 inches; inject non-repellent termiticide under pressure; seal holes with cement. Follow-up inspections included.",
            "hi": "फ्लोर-वॉल जंक्शन पर ~12 इंच पर ड्रिलिंग; प्रेशर से नॉन-रिपेलेंट केमिकल इंजेक्ट; बाद में सीमेंट से सील। फॉलो-अप निरीक्षण शामिल।",
            "mr": "फ्लोअर-वॉल जॉइंटवर दर ~12 इंच ड्रिल; प्रेशरने नॉन-रिपेलेंट केमिकल इंजेक्ट; सिमेंटने सील. फॉलो-अप तपासणी समाविष्ट."
        },
        "prices": {"AMC (3 services)": TERMITE_PRICES},
        "notes": {"en":"Non-destructive method; 1-year programme.","hi":"बिना तोड़-फोड़; 1-वर्षीय कार्यक्रम।","mr":"नॉन-डिस्ट्रक्टिव; 1 वर्ष कार्यक्रम."},
    },
    # ---- Others -> call for quote (short generic desc) ----
    "rodents": {
        "icon":"🐀",
        "title":{"en":"Rodents","hi":"चूहे","mr":"उंदीर"},
        "desc":{
            "en":"Bait stations + glue boards; guidance on sealing entry/exit points.",
            "hi":"बेट स्टेशन + ग्लू बोर्ड; एंट्री/एग्ज़िट पॉइंट्स सील करने की सलाह।",
            "mr":"बेट स्टेशन + ग्लू बोर्ड; प्रवेश/निर्गम पॉइंट्स सील करण्याबाबत मार्गदर्शन."
        },
        "call_only": True
    },
    "spider": {"icon":"🕷️","title":{"en":"Spiders","hi":"मकड़ी","mr":"कोळी"},
               "desc":{"en":"Web removal and residual spray on corners & balconies.",
                       "hi":"जाल हटाना और कॉर्नर/बालकनी में रेजिडुअल स्प्रे।",
                       "mr":"जाळे काढणे व कोपरे/बाल्कनीत रेसिड्युअल स्प्रे."},
               "call_only": True},
    "lizard": {"icon":"🦎","title":{"en":"Lizards","hi":"छिपकली","mr":"पाल"},
               "desc":{"en":"Repellent spray near ceilings, windows and entry points.",
                       "hi":"सीलिंग/खिड़की/एंट्री पॉइंट्स पर रिपेलेंट स्प्रे।",
                       "mr":"सीलिंग/खिडक्या/प्रवेशाजवळ रिपेलेंट स्प्रे."},
               "call_only": True},
    "mosquitoes":{"icon":"🦟","title":{"en":"Mosquitoes","hi":"मच्छर","mr":"डास"},
                  "desc":{"en":"Fogging + larvicide at breeding spots (society-safe).",
                          "hi":"फॉगिंग + ब्रिडिंग स्पॉट्स पर लार्विसाइड (सोसायटी-सेफ)।",
                          "mr":"फॉगिंग + ब्रिडिंग स्पॉट्सवर लार्विसाईड (सोसायटी-सेफ)."},
                  "call_only": True},
    "honeybees":{"icon":"🐝","title":{"en":"Honey Bees","hi":"मधुमक्खी","mr":"मधमाशी"},
                 "desc":{"en":"Safe hive removal/relocation when possible.",
                         "hi":"हाइव को सुरक्षित हटाना/स्थानांतरण (संभव हो तो)।",
                         "mr":"हायव्ह सुरक्षित काढणे/स्थानांतर (शक्य असल्यास)."},
                 "call_only": True},
    "flies":{"icon":"🪰","title":{"en":"Flies","hi":"मक्खियाँ","mr":"माशा"},
             "desc":{"en":"Baits + residual spray; sanitation advice.",
                     "hi":"बेट + रेजिडुअल स्प्रे; सफाई संबंधी सलाह।",
                     "mr":"बेट + रेसिड्युअल स्प्रे; स्वच्छता सल्ला."},
             "call_only": True},
    "fungus_mold":{"icon":"🌫️","title":{"en":"Fungus / Mold","hi":"फंगस/मोल्ड","mr":"बुरशी"},
                   "desc":{"en":"Anti-fungal treatment and moisture control tips.",
                           "hi":"एंटी-फंगल ट्रीटमेंट + नमी नियंत्रण सुझाव।",
                           "mr":"अँटी-फंगल उपचार + ओलावा नियंत्रण टिप्स."},
                   "call_only": True},
    "other":{"icon":"❓","title":{"en":"Other","hi":"अन्य","mr":"इतर"},
             "desc":{"en":"Not listed? Tell us your issue and we’ll guide you.",
                     "hi":"लिस्ट में नहीं? अपनी समस्या बताइए, हम मार्गदर्शन करेंगे।",
                     "mr":"यादीत नाही? समस्या सांगा, आम्ही मार्गदर्शन करू."},
             "call_only": True}
}

def now_greeting():
    h = datetime.datetime.now().hour
    return "Good Morning!" if h < 12 else ("Good Afternoon!" if h < 18 else "Good Evening!")

def detect_lang_from_text(txt):
    # crude: if Devanagari letters -> hi; allow manual override on UI anyway
    return "hi" if re.search(r"[\u0900-\u097F]", txt) else "en"

def format_prices(prices_dict):
    lines = []
    for block, entries in prices_dict.items():
        lines.append(f"• {block}")
        for k, v in entries.items():
            lines.append(f"  - {k}: {v}")
    return "\n".join(lines)

# ====== Routes ======
@app.route("/")
def home():
    return render_template(
        "index.html",
        phone=PHONE_DISPLAY,
        tel=PHONE_TEL,
        whatsapp=WHATSAPP_LINK,
        areas=", ".join(SERVICE_AREAS),
        hours=SERVICE_HOURS,
        greeting=now_greeting()
    )

@app.route("/api/services")
def api_services():
    # Return minimal data for building buttons
    order = ["general","cockroaches","bedbugs","termite","rodents","spider","lizard",
             "mosquitoes","honeybees","flies","fungus_mold","other"]
    items = [{"key": k, "icon": SERVICES[k]["icon"]} for k in order if k in SERVICES]
    return jsonify({"services": items})

@app.route("/get", methods=["POST"])
def get_reply():
    msg = request.form.get("msg", "").strip()
    lang = request.form.get("lang", "").strip() or detect_lang_from_text(msg)
    if lang not in T: lang = "en"

    # If message mentions a key, respond with that service
    key = None
    for k, v in SERVICES.items():
        label = v["title"]["en"].lower()
        if k in msg.lower() or label in msg.lower():
            key = k
            break

    if not key:
        # generic welcome/unknown
        return f"{T[lang]['welcome']}\n{T[lang]['areas_hours'].format(areas=', '.join(SERVICE_AREAS), hours=SERVICE_HOURS)}"

    svc = SERVICES[key]
    title = f"{svc['icon']} {svc['title'][lang]}"
    desc = svc["desc"][lang]

    if svc.get("call_only"):
        return (f"{title}\n{desc}\n\n{T[lang]['call_for_quote']}\n"
                f"📞 {PHONE_DISPLAY}  |  WhatsApp: {WHATSAPP_LINK}")
    else:
        price_text = format_prices(svc["prices"])
        return (f"{title}\n{desc}\n\n💰 {T[lang]['prices']}:\n{price_text}\n\n"
                f"📞 {PHONE_DISPLAY}  |  WhatsApp: {WHATSAPP_LINK}\n{T[lang]['negotiable']}")

if __name__ == "__main__":
    app.run(debug=True)

