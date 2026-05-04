import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

# ─────────────────────────────────────────────
# 1. LOAD RAW DATA
# ─────────────────────────────────────────────
df_crop    = pd.read_csv("data/crops_data.csv")
df_weather = pd.read_csv("data/Meru weather.csv")
df_soil    = pd.read_csv("data/soil_data.csv")


# ─────────────────────────────────────────────
# 2. WEATHER PREPROCESSING
# ─────────────────────────────────────────────
df_weather["date"]  = pd.to_datetime(df_weather["date"])
df_weather["year"]  = df_weather["date"].dt.year
df_weather["month"] = df_weather["date"].dt.month

def assign_season(month):
    if month in [3, 4, 5]:   return "MAM"
    elif month in [6, 7, 8]:  return "JJA"
    elif month in [10,11,12]: return "OND"
    else:                     return "DJF"

df_weather["season"] = df_weather["month"].apply(assign_season)

seasonal_weather = df_weather.groupby(["year", "season"]).agg(
    tavg=("tavg", "mean"),
    prcp=("prcp", "sum")
).reset_index()

season_baseline = (
    seasonal_weather.groupby("season")["prcp"]
    .mean().reset_index()
    .rename(columns={"prcp": "baseline_rainfall"})
)
seasonal_weather = seasonal_weather.merge(season_baseline, on="season", how="left")
seasonal_weather["rainfall_anomaly"] = (
    seasonal_weather["prcp"] - seasonal_weather["baseline_rainfall"]
)

def classify_drought(row):
    if row["rainfall_anomaly"] < -50:   return "High"
    elif row["rainfall_anomaly"] < -20: return "Moderate"
    else:                               return "Low"

seasonal_weather["drought_risk"] = seasonal_weather.apply(classify_drought, axis=1)


# ─────────────────────────────────────────────
# 3. SOIL PREPROCESSING
# ─────────────────────────────────────────────
df_soil.drop(columns=["Location_Latitude", "Location_Longitude"], inplace=True)
df_soil["Texture"] = df_soil["Texture"].replace({"clayey": "clay"})


# ─────────────────────────────────────────────
# 4. CROP PROFILES
# ─────────────────────────────────────────────
df_crop = df_crop.rename(columns={
    "Temparature": "Temperature",
    "Soil Type":   "Soil_Type",
    "Crop Type":   "Crop",
})
df_crop = df_crop.drop(columns=["Fertilizer Name"], errors="ignore")
df_crop["Crop"]      = df_crop["Crop"].str.lower().str.strip()
df_crop["Soil_Type"] = df_crop["Soil_Type"].str.lower().str.strip()

crop_profiles = df_crop.groupby("Crop").agg({
    "Temperature": "mean",
    "Humidity":    "mean",
    "Moisture":    "mean",
    "Nitrogen":    "mean",
    "Phosphorous": "mean",
    "Potassium":   "mean",
}).round(1).reset_index()

adjustments = {
    "millets":     [32, 45, 30],
    "paddy":       [28, 75, 65],
    "maize":       [27, 60, 45],
    "wheat":       [20, 55, 35],
    "barley":      [18, 50, 30],
    "cotton":      [30, 60, 40],
    "sugarcane":   [28, 70, 60],
    "pulses":      [25, 50, 30],
    "ground nuts": [28, 55, 35],
    "oil seeds":   [27, 50, 30],
    "tobacco":     [26, 65, 45],
}

for crop, values in adjustments.items():
    crop_profiles.loc[
        crop_profiles["Crop"] == crop,
        ["Temperature", "Humidity", "Moisture"]
    ] = values

# Replaced with agronomically accurate values for semi-arid East Africa
npk_adjustments = {
    "maize":       [90,  50,  180],
    "millets":     [50,  25,  120],
    "sorghum":     [55,  25,  140],
    "barley":      [70,  40,  150],
    "wheat":       [80,  45,  160],
    "sugarcane":   [120, 60,  240],
    "paddy":       [90,  45,  130],
    "cotton":      [70,  35,  130],
    "tobacco":     [75,  40,  140],
    "ground nuts": [30,  35,  110],  # legume — fixes own N
    "pulses":      [25,  30,  100],  # legume — fixes own N
    "oil seeds":   [60,  30,  120],
    "cowpeas":     [20,  25,   90],  # legume
    "green grams": [18,  22,   85],  # legume
    "pigeon peas": [22,  28,   95],  # legume
    "cassava":     [45,  30,  130],
    "miraa":       [45, 30, 120],
}

for crop, values in npk_adjustments.items():
    mask = crop_profiles["Crop"] == crop
    if mask.any():
        crop_profiles.loc[mask, ["Nitrogen", "Phosphorous", "Potassium"]] = values

# ─────────────────────────────────────────────
# 5. SUB-COUNTY → CLIMATE ZONE MAPPING
# ─────────────────────────────────────────────
subcounty_climate = {
    "Tigania East":   {"zone": "Semi-Arid",     "rainfall_band": "Low",      "temp_profile": "High"},
    "Tigania West":   {"zone": "Semi-Arid",     "rainfall_band": "Low",      "temp_profile": "High"},
    "Imenti Central": {"zone": "Highland",      "rainfall_band": "High",     "temp_profile": "Moderate"},
    "Imenti North":   {"zone": "Highland",      "rainfall_band": "High",     "temp_profile": "Moderate"},
    "Imenti South":   {"zone": "Upper Midland", "rainfall_band": "Moderate", "temp_profile": "Moderate"},
    "Buuri":          {"zone": "Upper Midland", "rainfall_band": "Moderate", "temp_profile": "Moderate"},
    "Igembe Central": {"zone": "Semi-Arid",     "rainfall_band": "Low",      "temp_profile": "High"},
    "Igembe North":   {"zone": "Semi-Arid",     "rainfall_band": "Low",      "temp_profile": "High"},
    "Igembe South":   {"zone": "Semi-Arid",     "rainfall_band": "Low",      "temp_profile": "High"},
}


# ─────────────────────────────────────────────
# 6. CROP KNOWLEDGE BASE
# ─────────────────────────────────────────────
crop_knowledge = {
    "millets":     {"drought_tolerance": "very_high", "water_demand": "low",       "preferred_soils": ["sandy"]},
    "ground nuts": {"drought_tolerance": "high",      "water_demand": "low",       "preferred_soils": ["loamy", "sandy"]},
    "pulses":      {"drought_tolerance": "moderate",  "water_demand": "low",       "preferred_soils": ["loamy"]},
    "oil seeds":   {"drought_tolerance": "moderate",  "water_demand": "medium",    "preferred_soils": ["loamy"]},
    "maize":       {"drought_tolerance": "moderate",  "water_demand": "medium",    "preferred_soils": ["loamy"]},
    "barley":      {"drought_tolerance": "moderate",  "water_demand": "low",       "preferred_soils": ["sandy", "loamy"]},
    "wheat":       {"drought_tolerance": "low",       "water_demand": "medium",    "preferred_soils": ["loamy", "clay"]},
    "cotton":      {"drought_tolerance": "high",      "water_demand": "medium",    "preferred_soils": ["clay", "loamy"]},
    "tobacco":     {"drought_tolerance": "low",       "water_demand": "medium",    "preferred_soils": ["loamy"]},
    "sugarcane":   {"drought_tolerance": "very_low",  "water_demand": "high",      "preferred_soils": ["clay", "loamy"]},
    "paddy":       {"drought_tolerance": "very_low",  "water_demand": "very_high", "preferred_soils": ["clay"]},
    "sorghum":      {"drought_tolerance": "very_high", "water_demand": "low",    "preferred_soils": ["sandy", "loamy"]},
    "cowpeas":      {"drought_tolerance": "high",      "water_demand": "low",    "preferred_soils": ["sandy", "loamy"]},
    "green grams":  {"drought_tolerance": "high",      "water_demand": "low",    "preferred_soils": ["sandy", "loamy"]},
    "pigeon peas":  {"drought_tolerance": "very_high", "water_demand": "low",    "preferred_soils": ["loamy", "clay"]},
    "cassava":      {"drought_tolerance": "very_high", "water_demand": "low",    "preferred_soils": ["sandy", "loamy"]},
    "miraa":        {"drought_tolerance": "high", "water_demand": "low", "preferred_soils": ["loamy", "sandy"]
},
}

tolerance_num_map = {
        "very_high": 5, "high": 4, "moderate": 3,
        "low": 2,       "very_low": 1
    }
demand_num_map = {
        "very_high": 4, "high": 3, "medium": 2, "low": 1
    }

new_crops = pd.DataFrame([
    {"Crop": "sorghum",     "Temperature": 30, "Humidity": 40,
     "Moisture": 25, "Nitrogen": 55, "Phosphorous": 25, "Potassium": 140},
    {"Crop": "cowpeas",     "Temperature": 28, "Humidity": 45,
     "Moisture": 28, "Nitrogen": 40, "Phosphorous": 20, "Potassium": 120},
    {"Crop": "green grams", "Temperature": 27, "Humidity": 45,
     "Moisture": 25, "Nitrogen": 35, "Phosphorous": 18, "Potassium": 110},
    {"Crop": "pigeon peas", "Temperature": 28, "Humidity": 50,
     "Moisture": 30, "Nitrogen": 45, "Phosphorous": 22, "Potassium": 130},
    {"Crop": "cassava",     "Temperature": 30, "Humidity": 55,
     "Moisture": 35, "Nitrogen": 50, "Phosphorous": 25, "Potassium": 150},
    {"Crop": "miraa", "Temperature": 23, "Humidity": 55,
     "Moisture": 35, "Nitrogen": 45, "Phosphorous": 30, "Potassium": 120},
])
crop_profiles = pd.concat([crop_profiles, new_crops], ignore_index=True)

# ─────────────────────────────────────────────
# 7. GENERATE SYNTHETIC TRAINING DATA
# ─────────────────────────────────────────────
# Since we don't have historical yield labels, we generate
# agronomically-informed synthetic data to train the ML model.
# This is standard practice in agricultural ML research when
# real labelled farm data is unavailable.

def generate_training_data(n_samples=3000):
    np.random.seed(42)
    crops       = list(crop_knowledge.keys())
    soils       = ["clay", "loamy", "sandy"]
    drought_map = {"High": 2, "Moderate": 1, "Low": 0}
    tolerance_map = {
        "very_high": 1.0, "high": 0.75, "moderate": 0.5,
        "low": 0.25,      "very_low": 0.1
    }
    demand_map = {"low": 1.0, "medium": 0.6, "high": 0.3, "very_high": 0.1}
    
    
    rows = []
    for _ in range(n_samples):
        crop         = np.random.choice(crops)
        soil_texture = np.random.choice(soils)
        drought_risk = np.random.choice(["High", "Moderate", "Low"])
        avg_temp     = np.random.uniform(15, 35)
        rainfall     = np.random.uniform(100, 900)
        fertility    = np.random.uniform(20, 90)
        water_score  = np.random.uniform(20, 90)
        nitrogen     = np.random.uniform(20, 150)
        phosphorus   = np.random.uniform(10, 100)
        potassium    = np.random.uniform(50, 300)

        ck = crop_knowledge[crop]
        cp = crop_profiles[crop_profiles["Crop"] == crop]

        # Calculate agronomic suitability score (same logic as before)
        # but used only to LABEL the training data
        temp_diff = abs(cp["Temperature"].values[0] - avg_temp) if len(cp) else 5
        c_score = 1.0 if temp_diff <= 2 else (0.6 if temp_diff <= 4 else 0.2)

        tolerance = tolerance_map[ck["drought_tolerance"]]
        d_score = tolerance if drought_risk == "High" else (
            tolerance * 0.85 if drought_risk == "Moderate" else tolerance * 0.7
        )
        if crop == "millets":
            d_score *= 1.1

        s_score = 2.0 if soil_texture in ck["preferred_soils"] else 0.4
        w_score = demand_map[ck["water_demand"]] * (water_score / 100)

        n_diff = abs(cp["Nitrogen"].values[0]    - nitrogen)    / max(nitrogen, 1)   if len(cp) else 0.5
        p_diff = abs(cp["Phosphorous"].values[0] - phosphorus)  / max(phosphorus, 1) if len(cp) else 0.5
        k_diff = abs(cp["Potassium"].values[0]   - potassium)   / max(potassium, 1)  if len(cp) else 0.5
        n_score = max(0, 1 - (n_diff + p_diff + k_diff) / 3)

        total = (
            0.10 * c_score +
            0.20 * n_score +
            0.25 * s_score +
            0.30 * d_score +
            0.15 * w_score
        )
        suitability_pct = round(total * 100, 1)

        # Label: High / Moderate / Low
        if suitability_pct >= 70:
            label = "High"
        elif suitability_pct >= 45:
            label = "Moderate"
        else:
            label = "Low"

        rows.append({
    "crop":              crop,
    "soil_texture":      soil_texture,
    "drought_risk":      drought_map[drought_risk],
    "avg_temp":          round(avg_temp, 1),
    "rainfall":          round(rainfall, 1),
    "fertility":         round(fertility, 1),
    "water_score":       round(water_score, 1),
    "nitrogen":          round(nitrogen, 1),
    "phosphorus":        round(phosphorus, 1),
    "potassium":         round(potassium, 1),
    "drought_tolerance": tolerance_num_map[ck["drought_tolerance"]],
    "water_demand":      demand_num_map[ck["water_demand"]],
    "soil_match":        1 if soil_texture in ck["preferred_soils"] else 0,
    "suitability":       suitability_pct,
    "label":             label,
})

    return pd.DataFrame(rows)


# ─────────────────────────────────────────────
# 8. TRAIN RANDOM FOREST MODEL
# ─────────────────────────────────────────────
print("Training Random Forest model...")

training_data = generate_training_data(6000)

  # Balance classes
from sklearn.utils import resample

high_df     = training_data[training_data["label"] == "High"]
moderate_df = training_data[training_data["label"] == "Moderate"]
low_df      = training_data[training_data["label"] == "Low"]

max_size = max(len(high_df), len(moderate_df), len(low_df))

high_df     = resample(high_df,     n_samples=max_size, random_state=42)
moderate_df = resample(moderate_df, n_samples=max_size, random_state=42)
low_df      = resample(low_df,      n_samples=max_size, random_state=42)

training_data = pd.concat([high_df, moderate_df, low_df]).reset_index(drop=True)
print(f"Balanced dataset: {len(training_data)} samples")

# Encode categorical columns
crop_encoder    = LabelEncoder()
soil_encoder    = LabelEncoder()
label_encoder   = LabelEncoder()

training_data["crop_enc"]    = crop_encoder.fit_transform(training_data["crop"])
training_data["soil_enc"]    = soil_encoder.fit_transform(training_data["soil_texture"])
training_data["label_enc"]   = label_encoder.fit_transform(training_data["label"])

FEATURES = [
    "crop_enc", "soil_enc", "drought_risk",
    "avg_temp", "rainfall", "fertility",
    "water_score", "nitrogen", "phosphorus", "potassium",
    "drought_tolerance", "water_demand", "soil_match"
]

X = training_data[FEATURES]
y = training_data["label_enc"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

rf_model = RandomForestClassifier(
    n_estimators=500,
    max_depth=15,
    min_samples_split=4,
    min_samples_leaf=2,
    max_features='sqrt',
    random_state=42,
    n_jobs=-1
)
rf_model.fit(X_train, y_train)

accuracy = accuracy_score(y_test, rf_model.predict(X_test))
print(f"Model accuracy: {accuracy * 100:.1f}%")

from sklearn.metrics import classification_report, confusion_matrix
print(classification_report(y_test, rf_model.predict(X_test)))
print(confusion_matrix(y_test, rf_model.predict(X_test)))


# ─────────────────────────────────────────────
# 9. CLIMATE CONTEXT  (unchanged)
# ─────────────────────────────────────────────
def get_climate_context(sub_county, season, year=None):
    if sub_county not in subcounty_climate:
        return "Sub-county not found in mapping table."

    zone_info = subcounty_climate[sub_county]
    data = seasonal_weather[seasonal_weather["season"] == season]
    if year:
        data = data[data["year"] == year]
    if data.empty:
        return "No weather data available for this season/year."

    avg_temp   = data["tavg"].mean()
    total_rain = data["prcp"].mean()
    drought    = data["drought_risk"].iloc[0]

    return {
        "Sub-County":          sub_county,
        "Agro_Zone":           zone_info["zone"],
        "Rainfall_Band":       zone_info["rainfall_band"],
        "Temperature_Profile": zone_info["temp_profile"],
        "Season":              season,
        "Average_Temperature": round(avg_temp, 2),
        "Seasonal_Rainfall":   round(total_rain, 2),
        "Drought_Risk":        drought,
    }


# ─────────────────────────────────────────────
# 10. SOIL FUNCTIONS  (unchanged)
# ─────────────────────────────────────────────
def normalize_texture(texture):
    texture = texture.lower().strip()
    if "clay"  in texture: return "clay"
    if "sand"  in texture: return "sandy"
    if "loam"  in texture: return "loamy"
    return texture

def get_soil_profile(texture_type):
    texture_type = normalize_texture(texture_type)
    soil_subset  = df_soil[df_soil["Texture"] == texture_type]
    if soil_subset.empty:
        return f"No soil data found for texture: '{texture_type}'."
    return soil_subset.mean(numeric_only=True)

def compute_water_score(soil_data):
    whc     = soil_data["Water_Holding_Capacity_%"]
    organic = soil_data["Organic_Matter_%"]
    return round((whc / 100) * 0.6 + (organic / 10) * 0.4, 2)

def compute_fertility_score(soil_data):
    n = soil_data["Nitrogen_N_ppm"]
    p = soil_data["Phosphorus_P_ppm"]
    k = soil_data["Potassium_K_ppm"]
    return round((n / 150 + p / 100 + k / 300) / 3, 2)

def adjust_drought_risk(climate_context, water_score):
    base_risk = climate_context["Drought_Risk"]
    if base_risk == "High"     and water_score > 0.6: return "Moderate"
    if base_risk == "Moderate" and water_score > 0.7: return "Low"
    return base_risk

def soil_layer(texture_type, climate_context):
    soil_data = get_soil_profile(texture_type)
    if isinstance(soil_data, str):
        return soil_data

    water_score     = compute_water_score(soil_data)
    fertility_score = compute_fertility_score(soil_data)
    adjusted_risk   = adjust_drought_risk(climate_context, water_score)

    def interpret_score(score):
        if score >= 70:   return "High"
        elif score >= 40: return "Moderate"
        return "Low"

    return {
        "Water_Score_%":         round(float(water_score) * 100, 2),
        "Water_Retention_Level": interpret_score(water_score * 100),
        "Fertility_Score_%":     round(float(fertility_score) * 100, 2),
        "Fertility_Level":       interpret_score(fertility_score * 100),
        "Adjusted_Drought_Risk": adjusted_risk,
        "Nitrogen":              round(float(soil_data["Nitrogen_N_ppm"]), 1),
        "Phosphorus":            round(float(soil_data["Phosphorus_P_ppm"]), 1),
        "Potassium":             round(float(soil_data["Potassium_K_ppm"]), 1),
    }


# ─────────────────────────────────────────────
# 11. ML-POWERED RECOMMENDATION FUNCTION
# ─────────────────────────────────────────────
drought_num_map = {"High": 2, "Moderate": 1, "Low": 0}
label_score_map = {"High": 85.0, "Moderate": 57.5, "Low": 25.0}

def recommend_crops(climate, soil, texture):
    """
    Use the trained Random Forest model to predict suitability
    for each crop given the climate and soil conditions.
    Returns a DataFrame sorted by suitability (highest first).
    """
    texture_norm = normalize_texture(texture)
    drought_num  = drought_num_map.get(climate["Drought_Risk"], 0)

    results = []

    for _, row in crop_profiles.iterrows():
        crop_name = row["Crop"].strip().lower()
        if crop_name not in crop_encoder.classes_:
            continue

        crop_enc = crop_encoder.transform([crop_name])[0]
        soil_enc = soil_encoder.transform(
            [texture_norm if texture_norm in soil_encoder.classes_ else "loamy"]
        )[0]

        ck = crop_knowledge.get(crop_name, {})

        features = pd.DataFrame([{
    "crop_enc":          crop_enc,
    "soil_enc":          soil_enc,
    "drought_risk":      drought_num,
    "avg_temp":          climate["Average_Temperature"],
    "rainfall":          climate["Seasonal_Rainfall"],
    "fertility":         soil["Fertility_Score_%"],
    "water_score":       soil["Water_Score_%"],
    "nitrogen":          soil["Nitrogen"],
    "phosphorus":        soil["Phosphorus"],
    "potassium":         soil["Potassium"],
    "drought_tolerance": tolerance_num_map[ck.get("drought_tolerance", "moderate")],  # NEW
    "water_demand":      demand_num_map[ck.get("water_demand", "medium")],            # NEW
    "soil_match":        1 if texture_norm in ck.get("preferred_soils", []) else 0,  # NEW
}])

        pred_label_enc = rf_model.predict(features)[0]
        pred_proba     = rf_model.predict_proba(features)[0]
        pred_label     = label_encoder.inverse_transform([pred_label_enc])[0]

        classes = label_encoder.classes_
        score = 0.0
        for cls, prob in zip(classes, pred_proba):
            score += label_score_map[cls] * prob

        # Scale score based on prediction confidence
        # High confidence predictions get boosted, uncertain ones get compressed
        max_prob = max(pred_proba)
        score = score * (0.7 + (max_prob * 0.3))

        
        tolerance_scores = {
            "very_high": 5.0, "high": 4.0, "moderate": 3.0,
            "low": 2.0,       "very_low": 1.0,
        }
        demand_scores = {
            "low": 4.0, "medium": 3.0, "high": 2.0, "very_high": 1.0,
        }

        agro_zone     = climate.get("Agro_Zone", "Upper Midland")
        rainfall_band = climate.get("Rainfall_Band", "Moderate")

        tol_score = tolerance_scores.get(ck.get("drought_tolerance", "moderate"), 3.0)
        dem_score = demand_scores.get(ck.get("water_demand", "medium"), 3.0)

        if agro_zone == "Semi-Arid" or rainfall_band == "Low":
            score += (tol_score * 0.3) + (dem_score * 0.2)
        elif agro_zone == "Upper Midland" or rainfall_band == "Moderate":
            score += (tol_score * 0.2) + (dem_score * 0.1)
        else:
            score += (tol_score * 0.1) + (dem_score * 0.1)

        if texture_norm in ck.get("preferred_soils", []):
            score += 2.0
        else:
            score += 0.0

        micro_adjust = {
    "miraa":        1.2,
    "cassava":      1.0,
    "ground nuts":  0.8,
    "sorghum":      0.6,
    "millets":      0.4,
    "green grams":  0.2,
    "cowpeas":      0.0,
    "pigeon peas": -0.2,
    "pulses":      -0.4,
    "oil seeds":   -0.6,
    "maize":       -0.8,
    "barley":      -1.0,
    "cotton":      -1.2,
    "wheat":       -1.4,
    "tobacco":     -1.6,
    "sugarcane":   -1.8,
    "paddy":       -2.0,
}
        score += micro_adjust.get(crop_name, 0.0)

        results.append({
            "Crop":          crop_name,
            "Suitability_%": round(score, 2),
            "ML_Label":      pred_label,
        })

    # ← these two lines are now OUTSIDE the for loop
    rec_df = pd.DataFrame(results)
    return rec_df.sort_values("Suitability_%", ascending=False).reset_index(drop=True)