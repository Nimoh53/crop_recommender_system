from flask import Flask, render_template, request, jsonify
from model import get_climate_context, soil_layer, recommend_crops, crop_knowledge

app = Flask(__name__)

CROP_DETAILS = {
    "maize": {
        "local_name": "Mahindi",
        "image": "/static/images/Maize.jpg",
        "description": "Maize is Meru's most widely grown staple, thriving in loamy soils with 600–900 mm of seasonal rainfall.",
        "growing_period": "90–120 days",
        "market": "High local demand; sold at Meru market and to millers",
        "planting_guide": {
            "planting": "Plant at the onset of rains in rows 75 cm apart with 25 cm between seeds. Sow 2–3 seeds per hole at 5 cm depth, then thin to one plant. Apply DAP fertiliser (1 bottle-cap per hole) at planting.",
            "care": "Top-dress with CAN fertiliser 6 weeks after germination. Weed twice — at 2 and 6 weeks. Watch for fall armyworm; spray with cypermethrin if leaves show feeding damage. Ensure soil stays moist but not waterlogged.",
            "growing_period": "90–120 days. Germination in 7–10 days, tasselling at 60–70 days, harvest when husks turn brown and dry.",
            "market_value": "Sells at KES 2,500–3,500 per 90 kg bag at Meru market. Millers pay KES 30–40 per kg. Expected yield is 30–50 bags per acre with good management."
        }
    },
    "wheat": {
        "local_name": "Ngano",
        "image": "/static/images/Wheat.jpg",
        "description": "Cool-season grain crop suited to highland areas above 1,800 m. Used for flour production.",
        "growing_period": "120–150 days",
        "market": "Purchased by large millers; stable prices",
        "planting_guide": {
            "planting": "Broadcast or drill seeds at 100–120 kg per acre on well-prepared seedbed. Apply DAP at 50 kg per acre at planting. Best planted at start of long rains in highland areas above 1,800 m.",
            "care": "Apply CAN top-dressing at tillering stage (30–40 days). Control weeds early as wheat does not compete well. Watch for rust disease — apply fungicide if orange/brown pustules appear on leaves.",
            "growing_period": "120–150 days. Tillering at 30–40 days, heading at 80–90 days, harvest when grain is hard and golden yellow.",
            "market_value": "Millers pay KES 35–45 per kg. Expected yield is 8–15 bags per acre. Prices are relatively stable due to consistent miller demand."
        }
    },
    "barley": {
        "local_name": "Shayiri",
        "image": "/static/images/Barley.jpg",
        "description": "Hardy highland cereal that tolerates cooler temperatures and moderate drought.",
        "growing_period": "90–120 days",
        "market": "Niche but growing demand from breweries",
        "planting_guide": {
            "planting": "Drill seeds at 80–100 kg per acre in rows 20 cm apart. Apply DAP at 50 kg per acre at planting. Requires well-drained loamy soils at altitudes above 1,500 m.",
            "care": "Top-dress with CAN at 30 days. Barley is relatively low-maintenance but needs one thorough weeding at 3 weeks. Avoid waterlogging — ridge fields if drainage is poor.",
            "growing_period": "90–120 days. Faster-maturing than wheat. Harvest when ears droop and grain is firm.",
            "market_value": "Breweries pay KES 40–55 per kg on contract. Animal feed buyers pay KES 25–35 per kg. Yield of 10–18 bags per acre is typical."
        }
    },
    "millets": {
        "local_name": "Uwele",
        "image": "/static/images/millets.jpg",
        "description": "Extremely drought-tolerant small-grain cereal ideal for semi-arid zones with poor soils.",
        "growing_period": "60–90 days",
        "market": "Traditional food; growing health-food market",
        "planting_guide": {
            "planting": "Broadcast seeds thinly or drill in rows 30 cm apart at 3–4 kg seed per acre. Minimal fertiliser needed — apply a small amount of DAP only if soil is very poor. Plant at first rains.",
            "care": "Thin seedlings to 15 cm apart at 2 weeks. Weed once at 3 weeks — millet is competitive once established. Very little irrigation needed. Watch for birds as grain ripens.",
            "growing_period": "60–90 days. One of the fastest-maturing cereals. Harvest when grain heads turn brown — do not delay or birds will take the crop.",
            "market_value": "Sells for KES 50–80 per kg at health food stores and local markets. Yield of 4–8 bags per acre. Low input costs make margins attractive despite modest volumes."
        }
    },
    "sugarcane": {
        "local_name": "Miwa",
        "image": "/static/images/Sugarcane.jpg",
        "description": "High-water-demand perennial crop with excellent returns in well-irrigated clay soils.",
        "growing_period": "12–18 months",
        "market": "Contract farming with sugar factories",
        "planting_guide": {
            "planting": "Plant cane cuttings (setts) with 2–3 nodes in furrows 1.2 m apart at 5–10 cm depth. Apply DAP in the furrow before covering. Irrigate immediately after planting if no rain expected.",
            "care": "Weed thoroughly for the first 3 months — sugarcane is slow to establish. Apply CAN top-dressing at 3 and 6 months. Irrigate every 2 weeks in dry periods. Ratoon for 2–3 cycles after first harvest.",
            "growing_period": "12–18 months for first harvest. Ratoon crops mature in 10–12 months. Harvest when cane is tall, firm, and joints are close together.",
            "market_value": "Sugar factories pay KES 4,500–5,500 per tonne. An acre yields 30–50 tonnes. Contract farming guarantees offtake."
        }
    },
    "paddy": {
        "local_name": "Mchele (Mpunga)",
        "image": "/static/images/Paddy.jpg",
        "description": "Flooded rice requiring heavy clay soils and consistent water supply.",
        "growing_period": "90–120 days",
        "market": "High demand; price supported by government",
        "planting_guide": {
            "planting": "Raise seedlings in a nursery for 21–25 days then transplant in rows 20×20 cm in flooded paddies. Apply DAP at transplanting. Level the field carefully to ensure even water distribution.",
            "care": "Maintain 5–10 cm water depth throughout growing season. Apply CAN top-dressing at tillering and panicle initiation. Watch for blast disease — apply fungicide if grey lesions appear.",
            "growing_period": "90–120 days from transplanting. Harvest when 80% of grains have turned golden yellow.",
            "market_value": "Paddy sells at KES 35–50 per kg. Milled rice fetches KES 80–120 per kg. Yield of 15–25 bags per acre."
        }
    },
    "cotton": {
        "local_name": "Pamba",
        "image": "/static/images/Cotton.jpg",
        "description": "Cash crop with good drought tolerance suited to warm lowland areas.",
        "growing_period": "150–180 days",
        "market": "Sold to ginneries; contract options available",
        "planting_guide": {
            "planting": "Plant 2 seeds per hole in rows 90 cm apart with 30 cm between holes at 3–4 cm depth. Thin to one plant at 2 weeks. Apply DAP at planting.",
            "care": "Top-dress with CAN at 6 weeks. Weed at 3 and 7 weeks. Spray for bollworm when flowering begins. Avoid excess nitrogen.",
            "growing_period": "150–180 days. Flowering at 60–70 days, boll opening at 130–150 days. Pick bolls as they open.",
            "market_value": "Ginneries pay KES 50–65 per kg seed cotton. Yield of 4–8 bags per acre."
        }
    },
    "ground nuts": {
        "local_name": "Karanga",
        "image": "/static/images/Groundnuts.jpg",
        "description": "Nitrogen-fixing legume ideal for sandy and loamy soils that improves soil fertility.",
        "growing_period": "90–120 days",
        "market": "Strong local demand; oil extraction potential",
        "planting_guide": {
            "planting": "Shell pods just before planting. Plant 2 seeds per hole in rows 45 cm apart with 15 cm between holes at 5 cm depth. Apply SSP phosphate fertiliser.",
            "care": "Weed at 2 and 5 weeks. Earth up around stems at flowering to encourage podding. Inoculate seeds with rhizobium for better nitrogen fixation.",
            "growing_period": "90–120 days. Leaves yellow and pods rattle when mature. Harvest by uprooting whole plant.",
            "market_value": "Fresh groundnuts sell at KES 80–120 per kg locally. Shelled dry nuts fetch KES 100–150 per kg. Yield of 4–8 bags per acre."
        }
    },
    "pulses": {
        "local_name": "Mikunde / Maharagwe",
        "image": "/static/images/Pulses.jpg",
        "description": "Protein-rich legumes that fix nitrogen and improve soil health across a wide range of conditions.",
        "growing_period": "60–90 days",
        "market": "Consistent market; good for food security",
        "planting_guide": {
            "planting": "Plant 2 seeds per hole in rows 45 cm apart with 20 cm between holes at 4–5 cm depth. Apply SSP at planting. Beans can be intercropped with maize.",
            "care": "Weed once at 3 weeks. Watch for bean fly — treat seeds with thiram before planting. Avoid overhead irrigation.",
            "growing_period": "60–90 days depending on variety. Harvest pods when dry and starting to crack.",
            "market_value": "Dry beans sell at KES 80–130 per kg at Meru market. Yield of 4–10 bags per acre."
        }
    },
    "oil seeds": {
        "local_name": "Mbegu za Mafuta",
        "image": "/static/images/Oilseeds.jpg",
        "description": "Includes sunflower and sesame — drought-tolerant crops good for oil extraction.",
        "growing_period": "90–120 days",
        "market": "Growing demand from cooking oil processors",
        "planting_guide": {
            "planting": "For sunflower: plant 1 seed per hole in rows 75 cm apart with 30 cm between holes at 3–4 cm depth. For sesame: broadcast on well-prepared seedbed at 2–3 kg per acre.",
            "care": "Weed sunflower at 2 and 5 weeks. Sesame needs one weeding at 3 weeks. Both are drought-tolerant once established.",
            "growing_period": "90–120 days for sunflower. Sesame matures in 80–100 days.",
            "market_value": "Sunflower sells at KES 40–55 per kg. Sesame fetches KES 80–120 per kg. Yield of 4–8 bags per acre."
        }
    },
    "tobacco": {
        "local_name": "Tumbaku",
        "image": "/static/images/Tobacco.jpg",
        "description": "High-value cash crop requiring well-drained loamy soils and careful management.",
        "growing_period": "90–120 days",
        "market": "Contract farming with tobacco companies",
        "planting_guide": {
            "planting": "Raise seedlings in a covered nursery for 6–8 weeks then transplant to field rows 1.2 m apart with 50 cm between plants.",
            "care": "Top-dress with CAN at 3 weeks after transplanting. Top the plant when it reaches desired leaf number. Remove suckers weekly after topping.",
            "growing_period": "90–120 days in field after transplanting. Harvest leaves from bottom upward — 3–4 pickings over 6–8 weeks.",
            "market_value": "Tobacco companies pay KES 150–300 per kg depending on leaf grade. Yield of 800–1,200 kg per acre."
        }
    },
    "sorghum": {
        "local_name": "Mtama",
        "image": "/static/images/Sorghum.jpg",
        "description": "Sorghum is one of the most drought-tolerant cereals available to Meru farmers, making it ideal for Tigania and Igembe semi-arid zones.",
        "growing_period": "90–120 days",
        "market": "Growing demand for food and animal feed; breweries also buying",
        "planting_guide": {
            "planting": "Plant 2–3 seeds per hole in rows 75 cm apart with 20 cm between holes at 3–5 cm depth. Thin to one plant at 2 weeks. Apply DAP at planting.",
            "care": "Weed at 2 and 5 weeks. Top-dress with CAN at 4 weeks. Watch for striga weed — remove immediately if seen.",
            "growing_period": "90–120 days. Harvest when grain is hard and head droops.",
            "market_value": "Sells at KES 30–50 per kg locally. Breweries pay KES 40–55 per kg. Yield of 6–12 bags per acre."
        }
    },
    "cowpeas": {
        "local_name": "Kunde",
        "image": "/static/images/Cowpeas.jpg",
        "description": "Cowpeas are a highly drought-tolerant legume widely grown across semi-arid Meru.",
        "growing_period": "60–90 days",
        "market": "Strong local demand for both grain and leaves; good food security crop",
        "planting_guide": {
            "planting": "Plant 2 seeds per hole in rows 50 cm apart with 20 cm between holes at 4 cm depth. Can be intercropped with sorghum or maize.",
            "care": "Weed once at 3 weeks. Watch for pod borers when flowering. Leaves can be harvested as vegetable while waiting for grain.",
            "growing_period": "60–90 days for grain. Harvest pods when dry and starting to split.",
            "market_value": "Dry grain sells at KES 80–120 per kg. Yield of 3–6 bags per acre."
        }
    },
    "green grams": {
        "local_name": "Ndengu",
        "image": "/static/images/GreenGrams.jpg",
        "description": "Green grams are a drought-tolerant legume and one of the most important cash crops in semi-arid Meru.",
        "growing_period": "60–75 days",
        "market": "Very strong local and export demand; consistent high prices",
        "planting_guide": {
            "planting": "Plant 2 seeds per hole in rows 40 cm apart with 20 cm between holes at 3–4 cm depth. Plant at onset of rains for best results.",
            "care": "Weed once at 2–3 weeks. Harvest pods as they ripen — multiple picks over 2 weeks.",
            "growing_period": "60–75 days. One of the fastest-maturing grain legumes.",
            "market_value": "Sells at KES 100–160 per kg. Yield of 3–5 bags per acre."
        }
    },
    "pigeon peas": {
        "local_name": "Mbaazi",
        "image": "/static/images/PigeonPeas.jpg",
        "description": "Pigeon peas are a highly drought-tolerant perennial legume with deep tap roots that access subsoil moisture.",
        "growing_period": "150–180 days",
        "market": "Strong local and regional demand; good export potential",
        "planting_guide": {
            "planting": "Plant 2 seeds per hole in rows 100 cm apart with 50 cm between holes at 5 cm depth. Apply SSP at planting.",
            "care": "Weed thoroughly for the first 6 weeks. Can be grown as a perennial for 3–5 years. Intercrop with maize or sorghum in first season.",
            "growing_period": "150–180 days for first harvest. Subsequent harvests from ratoon crop in 90–120 days.",
            "market_value": "Sells at KES 80–130 per kg dry grain. Yield of 4–8 bags per acre."
        }
    },
    "cassava": {
        "local_name": "Muhogo",
        "image": "/static/images/Cassava.jpg",
        "description": "Cassava is the most drought-tolerant starchy crop available to Meru farmers, surviving on as little as 250 mm of annual rainfall.",
        "growing_period": "9–12 months",
        "market": "Strong local food demand; growing starch and flour processing industry",
        "planting_guide": {
            "planting": "Plant stem cuttings 25–30 cm long at an angle in mounds or ridges 1 m apart. No fertiliser needed for first crop. Plant at onset of rains.",
            "care": "Weed for first 3 months. Harvest roots when leaves start to yellow. Can be left in ground as a living store for several months.",
            "growing_period": "9–12 months for sweet varieties, 12–18 months for bitter varieties.",
            "market_value": "Fresh roots sell at KES 15–25 per kg locally. Dried chips fetch KES 30–45 per kg. Yield of 80–120 bags per acre."
        }
    },
    "miraa": {
        "local_name": "Mugoka / Khat",
        "image": "/static/images/Miraa.jpg",
        "description": "Miraa is Meru's most economically significant cash crop, particularly in Igembe where it has been cultivated for generations.",
        "growing_period": "2–3 years to first harvest, then perennial",
        "market": "Very high value; exported to Somalia, UK, Netherlands and across East Africa",
        "planting_guide": {
            "planting": "Propagate from stem cuttings 20–30 cm long taken from mature plants. Plant in holes 60×60 cm filled with compost at spacing of 2×2 m. Water regularly for first 3 months.",
            "care": "Weed for first year until canopy establishes. Apply compost annually. Prune to maintain manageable height. Protect young plants from livestock.",
            "growing_period": "2–3 years to first commercial harvest. Once established produces continuously for 20–50 years. Harvest young shoots every 2–3 weeks.",
            "market_value": "Fresh shoots sell at KES 500–2,000 per bundle. A mature miraa farm of 1 acre can earn KES 200,000–500,000 per year."
        }
    },
}

SOIL_OPTIONS = [
    {
        "id": "clay",
        "name": "Clay",
        "swahili": "Udongo wa Mfinyanzi",
        "description": "Heavy, water-retaining soil. Fertile but can waterlog.",
        "image": "/static/images/clay soil.jpg",
    },
    {
        "id": "loamy",
        "name": "Loamy",
        "swahili": "Udongo Tifutifu",
        "description": "Balanced mix of sand, silt and clay. Ideal for most crops.",
        "image": "/static/images/loam soil.jpg",
    },
    {
        "id": "sandy",
        "name": "Sandy",
        "swahili": "Udongo wa Mchanga",
        "description": "Drains quickly, low nutrients. Best for drought-tolerant crops.",
        "image": "/static/images/sand soil.jpg",
    },
]

SUB_COUNTIES = [
    "Tigania East",
    "Tigania West",
    "Imenti Central",
    "Imenti North",
    "Imenti South",
    "Buuri",
    "Igembe Central",
    "Igembe North",
    "Igembe South",
]

SEASONS = [
    {"code": "MAM", "label": "Long Rains (Mar–May)",  "months": "March · April · May"},
    {"code": "OND", "label": "Short Rains (Oct–Dec)", "months": "October · November · December"},
    {"code": "JJA", "label": "Cold Dry (Jun–Aug)",    "months": "June · July · August"},
    {"code": "DJF", "label": "Hot Dry (Dec–Feb)",     "months": "December · January · February"},
]


def build_reason(crop_name, climate, soil, suitability):
    reasons = []
    ck = crop_knowledge.get(crop_name, {})

    drought_risk = climate.get("Drought_Risk", "Low")
    tolerance    = ck.get("drought_tolerance", "moderate")

    if drought_risk == "High" and tolerance in ("very_high", "high"):
        reasons.append("Excellent drought tolerance matches the high drought risk this season")
    elif drought_risk == "High" and tolerance == "moderate":
        reasons.append("Moderate drought tolerance may be stretched — irrigation recommended")
    elif drought_risk == "Low" and tolerance in ("low", "moderate"):
        reasons.append("Good seasonal rainfall supports this crop's water needs well")
    elif drought_risk == "Low" and tolerance in ("high", "very_high"):
        reasons.append("Drought-tolerant crop will thrive with the adequate rainfall this season")

    water_demand = ck.get("water_demand", "medium")
    water_level  = soil.get("Water_Retention_Level", "Moderate")
    if water_demand == "low" and water_level in ("Low", "Moderate"):
        reasons.append("Low water demand suits the soil's drainage capacity")
    elif water_demand in ("high", "very_high") and water_level == "High":
        reasons.append("High water demand is well supported by the soil's retention capacity")
    elif water_demand == "medium" and water_level == "Moderate":
        reasons.append("Moderate water needs match the soil's balanced retention")
    elif water_demand in ("high", "very_high") and water_level in ("Low", "Moderate"):
        reasons.append("Water demand is high — ensure irrigation or plant during peak rains")

    preferred = ck.get("preferred_soils", [])
    texture   = soil.get("texture_used", "")
    if texture in preferred:
        reasons.append(f"Thrives in {texture} soils — a strong textural match")
    elif preferred:
        reasons.append(f"Grows best in {', '.join(preferred)} soils — consider soil amendment")

    fertility = soil.get("Fertility_Level", "Moderate")
    if fertility == "High" and not reasons:
        reasons.append("High soil fertility provides a strong nutrient base for this crop")
    elif fertility == "Moderate" and not reasons:
        reasons.append("Moderate fertility is adequate with standard fertiliser inputs")
    elif fertility == "Low" and not reasons:
        reasons.append("Low soil fertility — apply compost and DAP to boost yields")

    if not reasons:
        reasons.append("Conditions are broadly compatible with this crop's requirements")

    return "; ".join(reasons[:2])


def suitability_to_confidence(score):
    if score >= 70:
        return "High", "high"
    elif score >= 45:
        return "Moderate", "moderate"
    return "Low", "low"


@app.route("/")
def index():
    return render_template(
        "index.html",
        sub_counties=SUB_COUNTIES,
        seasons=SEASONS,
        soil_options=SOIL_OPTIONS,
    )


@app.route("/recommend", methods=["POST"])
def recommend():
    data       = request.json
    sub_county = data.get("sub_county")
    season     = data.get("season")
    soil_type  = data.get("soil_type")

    climate = get_climate_context(sub_county, season)
    if isinstance(climate, str):
        return jsonify({"error": climate}), 400

    soil = soil_layer(soil_type, climate)
    if isinstance(soil, str):
        return jsonify({"error": soil}), 400

    soil["texture_used"] = soil_type
    recs = recommend_crops(climate, soil, soil_type)

    recs = recs[recs["Suitability_%"] >= 45].reset_index(drop=True)

    results = []
    for _, row in recs.iterrows():
        crop_name  = row["Crop"]
        score      = row["Suitability_%"]
        conf_label, conf_class = suitability_to_confidence(score)
        details    = CROP_DETAILS.get(crop_name, {})
        reason     = build_reason(crop_name, climate, soil, score)

        results.append({
            "crop":           crop_name.title(),
            "crop_key":       crop_name,
            "local_name":     details.get("local_name", ""),
            "suitability":    score,
            "confidence":     conf_label,
            "conf_class":     conf_class,
            "reason":         reason,
            "description":    details.get("description", ""),
            "growing_period": details.get("growing_period", ""),
            "market":         details.get("market", ""),
            "image":          details.get("image", ""),
            "planting_guide": details.get("planting_guide", {}),
        })

    return jsonify({
        "recommendations": results,
        "climate": {
            "zone":      climate["Agro_Zone"],
            "temp":      climate["Average_Temperature"],
            "rainfall":  climate["Seasonal_Rainfall"],
            "drought":   climate["Drought_Risk"],
            "rain_band": climate["Rainfall_Band"],
        },
        "soil": {
            "water":      soil["Water_Retention_Level"],
            "fertility":  soil["Fertility_Level"],
            "drought":    soil["Adjusted_Drought_Risk"],
            "nitrogen":   soil["Nitrogen"],
            "phosphorus": soil["Phosphorus"],
            "potassium":  soil["Potassium"],
        }
    })


if __name__ == "__main__":
    app.run(debug=True)