// Global model data
let modelData = null;
let creaturesData = null;
let defaultValues = null;

// Load model data
async function loadModel() {
    const loader = document.getElementById('loadingIndicator');
    if (loader) loader.style.display = 'block';

    try {
        const response = await fetch('model_data.json');
        modelData = await response.json();
        console.log('✅ Model loaded successfully');
        console.log('   - Model type:', modelData.model_type);
        console.log('   - Phase 2 features:', modelData.phase2_features.length);
        console.log('   - Phase 3 features:', modelData.phase3_features.length);
        console.log('   - Low-CR model: R²=' + modelData.models.low_cr.test_r2.toFixed(3));
        console.log('   - Mid-CR model: R²=' + modelData.models.mid_cr.test_r2.toFixed(3));
        console.log('   - High-CR model: R²=' + modelData.models.high_cr.test_r2.toFixed(3));

        // Update UI with model info
        document.getElementById('modelType').textContent = modelData.model_type || 'baseline_hp_model';
        document.getElementById('featureCount').textContent = modelData.phase3_features.length;

        if (loader) loader.style.display = 'none';

        // Load creatures data
        await loadCreatures();

        // Save default values for reset
        saveDefaultValues();

        // Initial calculation
        calculateHP();
    } catch (error) {
        console.error('❌ Error loading model:', error);
        alert('Error loading model data. Please ensure model_data.json is present.');
        if (loader) loader.style.display = 'none';
    }
}

// Select appropriate model based on CR
function selectModel(cr) {
    if (!modelData || !modelData.models) return null;

    if (cr <= 1.0) {
        return modelData.models.low_cr;
    } else if (cr <= 12.0) {
        return modelData.models.mid_cr;
    } else {
        return modelData.models.high_cr;
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
    const dcBaseline = getBaseline(cr, 'dc_baseline');

    document.getElementById('baselineHP').textContent = Math.round(hpBaseline);
    document.getElementById('baselineAC').textContent = Math.round(acBaseline);
    document.getElementById('baselineAttack').textContent = '+' + Math.round(attackBaseline);
    document.getElementById('baselineDPR').textContent = Math.round(dprBaseline);

    return { hpBaseline, acBaseline, attackBaseline, dprBaseline, dcBaseline };
}

// Update deviation displays
function updateDeviations(baselines, cr) {
    const ac = parseInt(document.getElementById('ac').value);
    const attack = parseInt(document.getElementById('attack').value);
    const dpr = parseFloat(document.getElementById('dpr').value);
    const saveDC = parseInt(document.getElementById('saveDC').value) || 0;

    const acDev = ac - Math.round(baselines.acBaseline);
    const attackDev = attack - Math.round(baselines.attackBaseline);
    const dprDev = dpr - baselines.dprBaseline;
    const saveDcDev = saveDC - Math.round(baselines.dcBaseline);

    updateDeviationDisplay('acDeviation', acDev, 'AC', cr);
    updateDeviationDisplay('attackDeviation', attackDev, 'Attack', cr);
    updateDeviationDisplay('dprDeviation', dprDev, 'DPR', cr);
    updateDeviationDisplay('saveDcDeviation', saveDcDev, 'Save DC', cr);

    return { acDev, attackDev, dprDev, saveDcDev };
}

function updateDeviationDisplay(elementId, deviation, label, cr) {
    const elem = document.getElementById(elementId);
    const rounded = Math.round(deviation * 10) / 10;

    if (rounded > 0) {
        elem.textContent = `Deviation: +${rounded} (${label} penalty: ${Math.round(deviation * getConstraint(label, cr))} HP)`;
        elem.className = 'deviation positive';
    } else if (rounded < 0) {
        elem.textContent = `Deviation: ${rounded} (${label} bonus: ${Math.round(-deviation * getConstraint(label, cr))} HP)`;
        elem.className = 'deviation negative';
    } else {
        elem.textContent = `Deviation: ${rounded} (no penalty)`;
        elem.className = 'deviation neutral';
    }
}

function getConstraint(label, cr) {
    const selectedModel = selectModel(cr);
    if (!selectedModel || !selectedModel.phase2_penalties) return 0;

    const constraintMap = {
        'AC': Math.abs(selectedModel.phase2_penalties.ac_deviation || -5),
        'Attack': Math.abs(selectedModel.phase2_penalties.attack_deviation || -6),
        'DPR': Math.abs(selectedModel.phase2_penalties.dpr_deviation || -2.5),
        'Save DC': Math.abs(selectedModel.phase2_penalties.save_dc_deviation || -10)
    };

    return constraintMap[label] || 0;
}

// Build Phase 3 feature vector (scaled features need hp_after_phase2)
function buildPhase3Features(hp_after_phase2) {
    const features = {};

    // Initialize all Phase 3 features to 0
    modelData.phase3_features.forEach(col => {
        features[col] = 0;
    });

    // Scaled abilities using hp_after_phase2 (not hp_baseline!)
    features.has_flying_scaled = document.getElementById('hasFlying').checked ? hp_after_phase2 : 0;
    features.has_legendary_resistance_scaled = document.getElementById('hasLegendaryResistance').checked ? hp_after_phase2 : 0;
    features.has_magic_resistance_scaled = document.getElementById('hasMagicResistance').checked ? hp_after_phase2 : 0;
    features.has_regeneration_scaled = document.getElementById('hasRegeneration').checked ? hp_after_phase2 : 0;
    features.has_legendary_actions_scaled = document.getElementById('hasLegendaryActions').checked ? hp_after_phase2 : 0;

    // Basic stats
    features.size_ordinal = parseInt(document.getElementById('size').value);

    // Speed features
    features.speed_ground = parseInt(document.getElementById('speedGround').value);
    features.speed_fly = parseInt(document.getElementById('speedFly').value);
    features.speed_swim = parseInt(document.getElementById('speedSwim').value);
    features.speed_burrow = parseInt(document.getElementById('speedBurrow').value);
    features.speed_climb = parseInt(document.getElementById('speedClimb').value);

    features.max_speed = Math.max(
        features.speed_ground,
        features.speed_fly,
        features.speed_swim,
        features.speed_burrow,
        features.speed_climb
    );

    features.movement_types_count =
        (features.speed_ground > 0 ? 1 : 0) +
        (features.speed_fly > 0 ? 1 : 0) +
        (features.speed_swim > 0 ? 1 : 0) +
        (features.speed_burrow > 0 ? 1 : 0) +
        (features.speed_climb > 0 ? 1 : 0);

    // Proficiencies and resistances
    features.save_proficiency_count = parseInt(document.getElementById('saveProficiencies').value);
    features.skill_proficiency_count = parseInt(document.getElementById('skillProficiencies').value);
    features.resistance_count = parseInt(document.getElementById('resistances').value);
    features.immunity_count = parseInt(document.getElementById('immunities').value);
    features.vulnerability_count = parseInt(document.getElementById('vulnerabilities').value);
    features.condition_immunity_count = parseInt(document.getElementById('conditionImmunities').value);

    // Conditions
    const conditions = ['poisoned', 'blinded', 'charmed', 'deafened', 'frightened',
                       'incapacitated', 'paralyzed', 'petrified', 'prone', 'restrained', 'stunned'];
    conditions.forEach(condition => {
        const elem = document.getElementById(`inflicts${condition.charAt(0).toUpperCase() + condition.slice(1)}`);
        features[`inflicts_${condition}`] = elem && elem.checked ? 1 : 0;
    });

    // Vision and senses
    features.has_darkvision = document.getElementById('hasDarkvision').checked ? 1 : 0;
    features.has_blindsight = document.getElementById('hasBlindsight').checked ? 1 : 0;
    features.has_truesight = document.getElementById('hasTruesight').checked ? 1 : 0;
    features.has_tremorsense = document.getElementById('hasTremorsense').checked ? 1 : 0;
    features.darkvision_range = parseInt(document.getElementById('darkvisionRange').value);
    features.passive_perception = parseInt(document.getElementById('passivePerception').value);

    // Ability counts
    features.trait_count = parseInt(document.getElementById('traitCount').value);
    features.reaction_count = parseInt(document.getElementById('reactionCount').value);
    features.bonus_action_count = parseInt(document.getElementById('bonusActionCount').value);
    features.legendary_action_count = parseInt(document.getElementById('legendaryActionCount').value);
    features.legendary_actions_per_round = parseInt(document.getElementById('legendaryActionsPerRound').value);

    // Calculate total ability count
    features.total_ability_count =
        features.trait_count +
        features.reaction_count +
        features.bonus_action_count +
        features.legendary_action_count;

    // Other abilities
    features.has_grapple = document.getElementById('hasGrapple').checked ? 1 : 0;
    features.has_spellcasting = document.getElementById('hasSpellcasting').checked ? 1 : 0;
    features.spellcaster_level = parseInt(document.getElementById('spellcasterLevel').value);

    return features;
}

// Predict HP using sequential three-phase approach
function predictHP(baselines, deviations, cr) {
    if (!modelData) {
        console.warn('⚠️ Model not loaded yet, returning default HP');
        return { total: 50, phase1: 50, phase2: 0, phase3: 0 };
    }

    // Select appropriate model based on CR
    const selectedModel = selectModel(cr);
    if (!selectedModel || !selectedModel.phase3_model) {
        console.warn('⚠️ Could not select model for CR:', cr);
        return { total: 50, phase1: 50, phase2: 0, phase3: 0 };
    }

    // Phase 1: Get baseline HP
    const phase1_hp = baselines.hpBaseline;

    // Phase 2: Apply fixed penalties for combat stat deviations
    const phase2_penalties = selectedModel.phase2_penalties;
    const phase2_adjustment = (
        deviations.acDev * phase2_penalties.ac_deviation +
        deviations.attackDev * phase2_penalties.attack_deviation +
        deviations.dprDev * phase2_penalties.dpr_deviation +
        (deviations.saveDcDev || 0) * phase2_penalties.save_dc_deviation
    );

    const hp_after_phase2 = phase1_hp + phase2_adjustment;

    // Phase 3: Build features using hp_after_phase2 for scaling
    const phase3_features = buildPhase3Features(hp_after_phase2);

    // Normalize Phase 3 features
    const X = [];
    modelData.phase3_features.forEach(col => {
        const value = phase3_features[col] || 0;
        const mean = selectedModel.phase3_model.scaler_mean[col];
        const scale = selectedModel.phase3_model.scaler_scale[col];
        X.push((value - mean) / scale);
    });

    // Predict residual HP using Phase 3 model
    let residual_prediction = selectedModel.phase3_model.intercept;

    for (let i = 0; i < modelData.phase3_features.length; i++) {
        const col = modelData.phase3_features[i];
        const coef = selectedModel.phase3_model.coefficients[col];
        const scale = selectedModel.phase3_model.scaler_scale[col];
        const scaledCoef = coef * scale;
        residual_prediction += X[i] * scaledCoef;
    }

    // Final HP = hp_after_phase2 + residual
    const total_hp = hp_after_phase2 + residual_prediction;

    return {
        total: Math.max(1, Math.round(total_hp)),
        phase1: Math.round(phase1_hp),
        phase2: Math.round(phase2_adjustment),
        phase3: Math.round(residual_prediction)
    };
}

// Calculate and display HP
function calculateHP() {
    if (!modelData) return;

    const cr = parseFloat(document.getElementById('cr').value);
    const baselines = updateBaselines();
    const deviations = updateDeviations(baselines, cr);
    const result = predictHP(baselines, deviations, cr);

    // Update display
    document.getElementById('hpValue').textContent = result.total;
    document.getElementById('phase1Value').textContent = `+${result.phase1} HP`;

    const phase2Text = result.phase2 >= 0 ? `+${result.phase2}` : `${result.phase2}`;
    document.getElementById('phase2StatValue').textContent = `${phase2Text} HP`;

    const phase3Text = result.phase3 >= 0 ? `+${result.phase3}` : `${result.phase3}`;
    document.getElementById('phase3Value').textContent = `${phase3Text} HP`;
}

// Load creatures data
async function loadCreatures() {
    try {
        const response = await fetch('creatures_data.json');
        creaturesData = await response.json();
        console.log(`✅ Loaded ${creaturesData.length} creatures`);

        // Populate creature selector based on current CR
        updateCreatureSelector();
    } catch (error) {
        console.warn('⚠️ Could not load creatures data:', error);
    }
}

// Update creature selector when CR changes
function updateCreatureSelector() {
    if (!creaturesData) {
        console.warn('⚠️ Creatures data not loaded yet');
        return;
    }

    const cr = parseFloat(document.getElementById('cr').value);
    const select = document.getElementById('creatureSelect');

    console.log('Updating creature selector for CR:', cr);

    // Clear existing options except first
    select.innerHTML = '<option value="">-- Select a creature --</option>';

    // Filter creatures by CR (compare as floats)
    const matchingCreatures = creaturesData.filter(c => Math.abs(c.cr - cr) < 0.001);

    // Add options
    matchingCreatures.forEach((creature, index) => {
        const option = document.createElement('option');
        option.value = index;
        option.textContent = `${creature.name} (${creature.type})`;
        option.dataset.creatureIndex = creaturesData.indexOf(creature);
        select.appendChild(option);
    });

    console.log(`Found ${matchingCreatures.length} creatures for CR ${cr}`);

    // Update info
    const info = document.getElementById('creatureInfo');
    if (matchingCreatures.length > 0) {
        info.textContent = `${matchingCreatures.length} creature(s) available at CR ${cr}`;
        info.style.display = 'block';
    } else {
        info.textContent = 'No creatures found for this CR';
        info.style.display = 'block';
    }
}

// Save default values for reset
function saveDefaultValues() {
    defaultValues = {
        cr: document.getElementById('cr').value,
        ac: document.getElementById('ac').value,
        attack: document.getElementById('attack').value,
        dpr: document.getElementById('dpr').value,
        size: document.getElementById('size').value,
        speedGround: document.getElementById('speedGround').value,
        speedFly: document.getElementById('speedFly').value,
        saveProficiencies: document.getElementById('saveProficiencies').value,
        skillProficiencies: document.getElementById('skillProficiencies').value,
        resistances: document.getElementById('resistances').value,
        immunities: document.getElementById('immunities').value,
    };

    // Save checkbox states
    document.querySelectorAll('input[type="checkbox"]').forEach(cb => {
        defaultValues[cb.id] = cb.checked;
    });
}

// Reset to default values
function resetToDefaults() {
    if (!defaultValues) return;

    // Restore input values
    Object.keys(defaultValues).forEach(key => {
        const elem = document.getElementById(key);
        if (elem) {
            if (elem.type === 'checkbox') {
                elem.checked = defaultValues[key];
            } else {
                elem.value = defaultValues[key];
            }
        }
    });

    // Clear creature selector
    document.getElementById('creatureSelect').value = '';

    // Recalculate
    calculateHP();

    console.log('✅ Reset to default values');
}

// Load creature data into form
function loadCreatureData() {
    const select = document.getElementById('creatureSelect');
    const selectedOption = select.options[select.selectedIndex];

    console.log('Load button clicked, selected index:', select.selectedIndex);
    console.log('Selected option:', selectedOption);

    if (!selectedOption || selectedOption.value === '' || !creaturesData) {
        console.warn('No creature selected or data not loaded');
        return;
    }

    const creatureIndex = parseInt(selectedOption.dataset.creatureIndex);
    console.log('Creature index from dataset:', creatureIndex);

    const creature = creaturesData[creatureIndex];
    console.log('Loading creature:', creature);

    // Parse and populate creature data
    try {
        // Set CR
        console.log('Setting CR to:', creature.cr);
        document.getElementById('cr').value = creature.cr;

        // Parse AC
        console.log('Parsing AC from:', creature.ac);
        const acMatch = creature.ac.match(/(\d+)/);
        if (acMatch) {
            console.log('Setting AC to:', acMatch[1]);
            document.getElementById('ac').value = parseInt(acMatch[1]);
        }

        // Parse Actions for attack bonus and DPR
        if (creature.actions) {
            try {
                const actions = JSON.parse(creature.actions);

                // Find highest attack bonus
                let maxAttack = 0;
                let totalDpr = 0;

                actions.forEach(action => {
                    if (action['Hit Bonus']) {
                        const bonus = parseInt(action['Hit Bonus']);
                        if (bonus > maxAttack) maxAttack = bonus;
                    }

                    // Calculate DPR
                    if (action.Damage && action.Name !== 'Multiattack') {
                        const damageMatch = action.Damage.match(/(\d+)d(\d+)(?:\s*\+\s*(\d+))?/);
                        if (damageMatch) {
                            const numDice = parseInt(damageMatch[1]);
                            const dieSize = parseInt(damageMatch[2]);
                            const modifier = damageMatch[3] ? parseInt(damageMatch[3]) : 0;
                            const avgDmg = numDice * (dieSize + 1) / 2 + modifier;
                            totalDpr += avgDmg;
                        }
                    }
                });

                if (maxAttack > 0) {
                    document.getElementById('attack').value = maxAttack;
                }

                // Check for multiattack
                const hasMultiattack = actions.some(a => a.Name === 'Multiattack');
                if (hasMultiattack && totalDpr > 0) {
                    totalDpr *= 1.5; // Simple heuristic
                }

                if (totalDpr > 0) {
                    document.getElementById('dpr').value = Math.round(totalDpr);
                }
            } catch (e) {
                console.warn('Could not parse actions:', e);
            }
        }

        // Parse speed
        if (creature.speed) {
            const groundMatch = creature.speed.match(/^(\d+)\s*ft/);
            const flyMatch = creature.speed.match(/fly\s+(\d+)\s*ft/i);

            if (groundMatch) {
                document.getElementById('speedGround').value = parseInt(groundMatch[1]);
            }
            if (flyMatch) {
                document.getElementById('speedFly').value = parseInt(flyMatch[1]);
                document.getElementById('hasFlying').checked = true;
            } else {
                document.getElementById('speedFly').value = 0;
                document.getElementById('hasFlying').checked = false;
            }
        }

        // Parse size
        const sizeMap = {
            'Tiny': 0, 'Small': 1, 'Medium': 2,
            'Large': 3, 'Huge': 4, 'Gargantuan': 5
        };
        if (creature.size && sizeMap[creature.size] !== undefined) {
            document.getElementById('size').value = sizeMap[creature.size];
        }

        // Check for special abilities in traits and legendary actions
        const allText = (creature.traits || '') + ' ' + (creature.legendary_actions || '');
        const lowerText = allText.toLowerCase();

        document.getElementById('hasLegendaryResistance').checked = lowerText.includes('legendary resistance');
        document.getElementById('hasMagicResistance').checked = lowerText.includes('magic resistance');
        document.getElementById('hasRegeneration').checked = lowerText.includes('regeneration');
        document.getElementById('hasLegendaryActions').checked = creature.legendary_actions && creature.legendary_actions.trim() !== '';

        // Recalculate HP
        calculateHP();

        console.log(`✅ Loaded ${creature.name}`);

    } catch (error) {
        console.error('Error loading creature:', error);
        alert('Error loading creature data');
    }
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

    // CR selector updates creature list
    document.getElementById('cr').addEventListener('change', updateCreatureSelector);

    // Load creature button
    document.getElementById('loadCreatureBtn').addEventListener('click', loadCreatureData);

    // Reset button
    document.getElementById('resetBtn').addEventListener('click', resetToDefaults);

    console.log('✅ Event listeners attached - app ready');
});
