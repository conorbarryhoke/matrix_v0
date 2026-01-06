// Global model data
let modelData = null;

// Load model data
async function loadModel() {
    const loader = document.getElementById('loadingIndicator');
    if (loader) loader.style.display = 'block';

    try {
        const response = await fetch('model_data.json');
        modelData = await response.json();
        console.log('✅ Model loaded successfully with', modelData.feature_columns.length, 'features');

        // Update UI with model info
        document.getElementById('modelType').textContent = modelData.model_type || 'baseline_hp_model';
        document.getElementById('featureCount').textContent = modelData.feature_columns.length;

        if (loader) loader.style.display = 'none';

        // Initial calculation
        calculateHP();
    } catch (error) {
        console.error('❌ Error loading model:', error);
        alert('Error loading model data. Please ensure model_data.json is present.');
        if (loader) loader.style.display = 'none';
    }
}

// Interpolate baseline values from CR
function getBaseline(cr, valueType) {
    if (!modelData || !modelData.baseline_data) return 0;

    const crValues = modelData.baseline_data.cr_values;
    const values = modelData.baseline_data[valueType];

    // Find surrounding CR values for interpolation
    let lowerIdx = 0;
    let upperIdx = crValues.length - 1;

    for (let i = 0; i < crValues.length; i++) {
        if (crValues[i] <= cr) lowerIdx = i;
        if (crValues[i] >= cr && upperIdx === crValues.length - 1) {
            upperIdx = i;
            break;
        }
    }

    // Linear interpolation
    if (lowerIdx === upperIdx) {
        return values[lowerIdx];
    }

    const crLower = crValues[lowerIdx];
    const crUpper = crValues[upperIdx];
    const valueLower = values[lowerIdx];
    const valueUpper = values[upperIdx];

    const t = (cr - crLower) / (crUpper - crLower);
    return valueLower + t * (valueUpper - valueLower);
}

// Update baseline display
function updateBaselines() {
    const cr = parseFloat(document.getElementById('cr').value);

    const hpBaseline = getBaseline(cr, 'hp_baseline');
    const acBaseline = getBaseline(cr, 'ac_baseline');
    const attackBaseline = getBaseline(cr, 'attack_baseline');
    const dprBaseline = getBaseline(cr, 'dpr_baseline');

    document.getElementById('baselineHP').textContent = Math.round(hpBaseline);
    document.getElementById('baselineAC').textContent = Math.round(acBaseline);
    document.getElementById('baselineAttack').textContent = '+' + Math.round(attackBaseline);
    document.getElementById('baselineDPR').textContent = Math.round(dprBaseline);

    return { hpBaseline, acBaseline, attackBaseline, dprBaseline };
}

// Update deviation displays
function updateDeviations(baselines) {
    const ac = parseInt(document.getElementById('ac').value);
    const attack = parseInt(document.getElementById('attack').value);
    const dpr = parseFloat(document.getElementById('dpr').value);

    const acDev = ac - Math.round(baselines.acBaseline);
    const attackDev = attack - Math.round(baselines.attackBaseline);
    const dprDev = dpr - baselines.dprBaseline;

    updateDeviationDisplay('acDeviation', acDev, 'AC');
    updateDeviationDisplay('attackDeviation', attackDev, 'Attack');
    updateDeviationDisplay('dprDeviation', dprDev, 'DPR');

    return { acDev, attackDev, dprDev };
}

function updateDeviationDisplay(elementId, deviation, label) {
    const elem = document.getElementById(elementId);
    const rounded = Math.round(deviation * 10) / 10;

    if (rounded > 0) {
        elem.textContent = `Deviation: +${rounded} (${label} penalty: ${Math.round(deviation * getConstraint(label))} HP)`;
        elem.className = 'deviation positive';
    } else if (rounded < 0) {
        elem.textContent = `Deviation: ${rounded} (${label} bonus: ${Math.round(-deviation * getConstraint(label))} HP)`;
        elem.className = 'deviation negative';
    } else {
        elem.textContent = `Deviation: ${rounded} (no penalty)`;
        elem.className = 'deviation neutral';
    }
}

function getConstraint(label) {
    if (!modelData || !modelData.constraints) return 0;

    const constraintMap = {
        'AC': Math.abs(modelData.constraints.ac_deviation || -5),
        'Attack': Math.abs(modelData.constraints.attack_deviation || -6),
        'DPR': Math.abs(modelData.constraints.dpr_deviation || -2.5)
    };

    return constraintMap[label] || 0;
}

// Build feature vector
function buildFeatures(baselines, deviations) {
    const features = {};

    // Initialize all features to 0
    modelData.feature_columns.forEach(col => {
        features[col] = 0;
    });

    // Phase 1: Baseline HP
    features.hp_baseline = baselines.hpBaseline;

    // Phase 2: Deviations
    features.ac_deviation = deviations.acDev;
    features.attack_deviation = deviations.attackDev;
    features.dpr_deviation = deviations.dprDev;

    // Phase 2: Scaled abilities
    const hpBase = baselines.hpBaseline;
    features.has_flying_scaled = document.getElementById('hasFlying').checked ? hpBase : 0;
    features.has_legendary_resistance_scaled = document.getElementById('hasLegendaryResistance').checked ? hpBase : 0;
    features.has_magic_resistance_scaled = document.getElementById('hasMagicResistance').checked ? hpBase : 0;
    features.has_regeneration_scaled = document.getElementById('hasRegeneration').checked ? hpBase : 0;
    features.has_legendary_actions_scaled = document.getElementById('hasLegendaryActions').checked ? hpBase : 0;

    // Phase 3: Basic stats
    features.size_ordinal = parseInt(document.getElementById('size').value);
    features.speed_ground = parseInt(document.getElementById('speedGround').value);
    features.speed_fly = parseInt(document.getElementById('speedFly').value);
    features.max_speed = Math.max(features.speed_ground, features.speed_fly);
    features.movement_types_count = (features.speed_ground > 0 ? 1 : 0) + (features.speed_fly > 0 ? 1 : 0);

    features.save_proficiency_count = parseInt(document.getElementById('saveProficiencies').value);
    features.skill_proficiency_count = parseInt(document.getElementById('skillProficiencies').value);
    features.resistance_count = parseInt(document.getElementById('resistances').value);
    features.immunity_count = parseInt(document.getElementById('immunities').value);

    // Phase 3: Conditions
    const conditions = ['poisoned', 'blinded', 'charmed', 'deafened', 'frightened',
                       'incapacitated', 'paralyzed', 'petrified', 'prone', 'restrained', 'stunned'];
    conditions.forEach(condition => {
        const elem = document.getElementById(`inflicts${condition.charAt(0).toUpperCase() + condition.slice(1)}`);
        features[`inflicts_${condition}`] = elem && elem.checked ? 1 : 0;
    });

    // Phase 3: Other abilities
    if (document.getElementById('hasMultiattack')) {
        features.has_multiattack = document.getElementById('hasMultiattack').checked ? 1 : 0;
    }
    if (document.getElementById('hasGrapple')) {
        features.has_grapple = document.getElementById('hasGrapple').checked ? 1 : 0;
    }
    if (document.getElementById('hasSpellcasting')) {
        features.has_spellcasting = document.getElementById('hasSpellcasting').checked ? 1 : 0;
    }
    if (document.getElementById('hasDarkvision')) {
        features.has_darkvision = document.getElementById('hasDarkvision').checked ? 1 : 0;
    }
    if (document.getElementById('hasBlindsight')) {
        features.has_blindsight = document.getElementById('hasBlindsight').checked ? 1 : 0;
    }
    if (document.getElementById('hasTruesight')) {
        features.has_truesight = document.getElementById('hasTruesight').checked ? 1 : 0;
    }

    return features;
}

// Predict HP
function predictHP(features) {
    if (!modelData) {
        console.warn('⚠️ Model not loaded yet, returning default HP');
        return { total: 50, phase1: 50, phase2Stats: 0, phase2Abilities: 0, phase3: 0 };
    }

    // Normalize features
    const X = [];
    modelData.feature_columns.forEach(col => {
        const value = features[col] || 0;
        const mean = modelData.scaler_mean[col];
        const scale = modelData.scaler_scale[col];
        X.push((value - mean) / scale);
    });

    // Calculate prediction
    let prediction = modelData.intercept;

    for (let i = 0; i < modelData.feature_columns.length; i++) {
        const col = modelData.feature_columns[i];
        const coef = modelData.coefficients[col];
        const scaledCoef = coef * modelData.scaler_scale[col];
        prediction += X[i] * scaledCoef;
    }

    // Calculate breakdown
    const phase1 = features.hp_baseline;

    const phase2Stats = (
        features.ac_deviation * modelData.constraints.ac_deviation +
        features.attack_deviation * modelData.constraints.attack_deviation +
        features.dpr_deviation * modelData.constraints.dpr_deviation
    );

    const phase2Abilities = (
        features.has_flying_scaled * modelData.constraints.has_flying_scaled +
        features.has_legendary_resistance_scaled * modelData.constraints.has_legendary_resistance_scaled +
        features.has_magic_resistance_scaled * modelData.constraints.has_magic_resistance_scaled +
        features.has_regeneration_scaled * modelData.constraints.has_regeneration_scaled +
        features.has_legendary_actions_scaled * modelData.constraints.has_legendary_actions_scaled
    );

    const phase3 = prediction - phase1 - phase2Stats - phase2Abilities;

    return {
        total: Math.max(1, Math.round(prediction)),
        phase1: Math.round(phase1),
        phase2Stats: Math.round(phase2Stats),
        phase2Abilities: Math.round(phase2Abilities),
        phase3: Math.round(phase3)
    };
}

// Calculate and display HP
function calculateHP() {
    if (!modelData) return;

    const baselines = updateBaselines();
    const deviations = updateDeviations(baselines);
    const features = buildFeatures(baselines, deviations);
    const result = predictHP(features);

    // Update display
    document.getElementById('hpValue').textContent = result.total;
    document.getElementById('phase1Value').textContent = `+${result.phase1} HP`;

    const phase2StatText = result.phase2Stats >= 0 ? `+${result.phase2Stats}` : `${result.phase2Stats}`;
    document.getElementById('phase2StatValue').textContent = `${phase2StatText} HP`;

    const phase2AbilityText = result.phase2Abilities >= 0 ? `+${result.phase2Abilities}` : `${result.phase2Abilities}`;
    document.getElementById('phase2AbilityValue').textContent = `${phase2AbilityText} HP`;

    const phase3Text = result.phase3 >= 0 ? `+${result.phase3}` : `${result.phase3}`;
    document.getElementById('phase3Value').textContent = `${phase3Text} HP`;
}

// Event listeners
document.addEventListener('DOMContentLoaded', async () => {
    await loadModel();

    // Attach event listeners to all inputs
    const inputs = document.querySelectorAll('input, select');
    inputs.forEach(input => {
        input.addEventListener('change', calculateHP);
        input.addEventListener('input', calculateHP);
    });

    console.log('✅ Event listeners attached - app ready');
});
