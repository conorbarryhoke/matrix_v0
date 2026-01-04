// Global variables for model
let modelData = null;
let currentSize = 3; // Medium

// DMG CR tables for reference
const DMG_CR_TABLE = {
    0: { hp: [1, 6], ac: 13, attack: 3, damage: [0, 1], save: 13 },
    0.125: { hp: [7, 35], ac: 13, attack: 3, damage: [2, 3], save: 13 },
    0.25: { hp: [36, 49], ac: 13, attack: 3, damage: [4, 5], save: 13 },
    0.5: { hp: [50, 70], ac: 13, attack: 3, damage: [6, 8], save: 13 },
    1: { hp: [71, 85], ac: 13, attack: 3, damage: [9, 14], save: 13 },
    2: { hp: [86, 100], ac: 13, attack: 3, damage: [15, 20], save: 13 },
    3: { hp: [101, 115], ac: 13, attack: 4, damage: [21, 26], save: 13 },
    4: { hp: [116, 130], ac: 14, attack: 5, damage: [27, 32], save: 14 },
    5: { hp: [131, 145], ac: 15, attack: 6, damage: [33, 38], save: 15 },
    6: { hp: [146, 160], ac: 15, attack: 6, damage: [39, 44], save: 15 },
    7: { hp: [161, 175], ac: 15, attack: 6, damage: [45, 50], save: 15 },
    8: { hp: [176, 190], ac: 16, attack: 7, damage: [51, 56], save: 16 },
    9: { hp: [191, 205], ac: 16, attack: 7, damage: [57, 62], save: 16 },
    10: { hp: [206, 220], ac: 17, attack: 7, damage: [63, 68], save: 16 },
    11: { hp: [221, 235], ac: 17, attack: 8, damage: [69, 74], save: 17 },
    12: { hp: [236, 250], ac: 17, attack: 8, damage: [75, 80], save: 17 },
    13: { hp: [251, 265], ac: 18, attack: 8, damage: [81, 86], save: 18 },
    14: { hp: [266, 280], ac: 18, attack: 8, damage: [87, 92], save: 18 },
    15: { hp: [281, 295], ac: 18, attack: 8, damage: [93, 98], save: 18 },
    16: { hp: [296, 310], ac: 18, attack: 9, damage: [99, 104], save: 18 },
    17: { hp: [311, 325], ac: 19, attack: 10, damage: [105, 110], save: 19 },
    18: { hp: [326, 340], ac: 19, attack: 10, damage: [111, 116], save: 19 },
    19: { hp: [341, 355], ac: 19, attack: 10, damage: [117, 122], save: 19 },
    20: { hp: [356, 400], ac: 19, attack: 10, damage: [123, 140], save: 19 },
    21: { hp: [401, 445], ac: 19, attack: 11, damage: [141, 158], save: 20 },
    22: { hp: [446, 490], ac: 19, attack: 11, damage: [159, 176], save: 20 },
    23: { hp: [491, 535], ac: 19, attack: 11, damage: [177, 194], save: 20 },
    24: { hp: [536, 580], ac: 19, attack: 12, damage: [195, 212], save: 21 },
    25: { hp: [581, 625], ac: 19, attack: 12, damage: [213, 230], save: 21 },
    26: { hp: [626, 670], ac: 19, attack: 12, damage: [231, 248], save: 21 },
    27: { hp: [671, 715], ac: 19, attack: 13, damage: [249, 266], save: 22 },
    28: { hp: [716, 760], ac: 19, attack: 13, damage: [267, 284], save: 22 },
    29: { hp: [761, 805], ac: 19, attack: 13, damage: [285, 302], save: 22 },
    30: { hp: [806, 850], ac: 19, attack: 14, damage: [303, 320], save: 23 }
};

// Load model data
async function loadModel() {
    try {
        const response = await fetch('model_data.json');
        modelData = await response.json();
        console.log('Model loaded successfully');
        calculateHP(); // Initial calculation
    } catch (error) {
        console.error('Error loading model:', error);
        alert('Error loading model data. Please ensure model_data.json is present.');
    }
}

// Predict HP using linear regression model
function predictHP(features) {
    if (!modelData) return 50; // Default if model not loaded

    let prediction = modelData.intercept;

    // Scale features and apply coefficients
    for (const feature of modelData.feature_columns) {
        const value = features[feature] || 0;
        const scaled = (value - modelData.scaler_mean[feature]) / modelData.scaler_scale[feature];
        prediction += scaled * modelData.coefficients[feature];
    }

    return Math.max(1, Math.round(prediction)); // HP can't be less than 1
}

// Calculate HP dice notation
function calculateHPDice(hp, size) {
    const hitDice = {
        1: 4,   // Tiny = d4
        2: 6,   // Small = d6
        3: 8,   // Medium = d8
        4: 10,  // Large = d10
        5: 12,  // Huge = d12
        6: 20   // Gargantuan = d20
    };

    const dieSize = hitDice[size] || 8;
    const avgPerDie = (dieSize + 1) / 2;

    // Assume CON modifier of +1 (average)
    const conMod = 1;
    const hpPerDie = avgPerDie + conMod;
    const numDice = Math.max(1, Math.round(hp / hpPerDie));
    const totalMod = numDice * conMod;

    return `${numDice}d${dieSize}${totalMod >= 0 ? '+' : ''}${totalMod}`;
}

// Get DMG baseline for CR
function getDMGBaseline(cr) {
    const crKeys = Object.keys(DMG_CR_TABLE).map(Number).sort((a, b) => a - b);
    let closestCR = crKeys[0];

    for (const key of crKeys) {
        if (Math.abs(key - cr) < Math.abs(closestCR - cr)) {
            closestCR = key;
        }
    }

    return DMG_CR_TABLE[closestCR];
}

// Main calculation function
function calculateHP() {
    // Gather all input values
    const cr = parseFloat(document.getElementById('cr').value) || 3;
    const ac = parseInt(document.getElementById('ac').value) || 14;
    const attack = parseInt(document.getElementById('attack').value) || 5;
    const saveDC = parseInt(document.getElementById('saveDC').value) || 13;
    const dpr = parseInt(document.getElementById('dpr').value) || 10;

    const groundSpeed = parseInt(document.getElementById('speed').value) || 30;
    const flySpeed = parseInt(document.getElementById('flySpeed').value) || 0;
    const swimSpeed = parseInt(document.getElementById('swimSpeed').value) || 0;
    const burrowSpeed = parseInt(document.getElementById('burrowSpeed').value) || 0;
    const climbSpeed = parseInt(document.getElementById('climbSpeed').value) || 0;

    const saveProficiency = parseInt(document.getElementById('saveProficiency').value) || 0;
    const skillProficiency = parseInt(document.getElementById('skillProficiency').value) || 0;
    const passivePerception = parseInt(document.getElementById('passivePerception').value) || 10;

    const resistances = parseInt(document.getElementById('resistances').value) || 0;
    const immunities = parseInt(document.getElementById('immunities').value) || 0;

    const hasMultiattack = document.getElementById('multiattack').checked;
    const hasLegendary = document.getElementById('legendary').checked;
    const hasLegendaryRes = document.getElementById('legendaryRes').checked;
    const hasMagicRes = document.getElementById('magicRes').checked;
    const hasRegeneration = document.getElementById('regeneration').checked;
    const isSpellcaster = document.getElementById('spellcasting').checked;
    const hasGrapple = document.getElementById('grapple').checked;

    const hasDarkvision = document.getElementById('darkvision').checked;
    const hasBlindsight = document.getElementById('blindsight').checked;
    const hasTruesight = document.getElementById('truesight').checked;
    const hasTremorsense = document.getElementById('tremorsense').checked;

    // Condition infliction
    const inflictsPoisoned = document.getElementById('inflictsPoisoned').checked;
    const inflictsBlinded = document.getElementById('inflictsBlinded').checked;
    const inflictsCharmed = document.getElementById('inflictsCharmed').checked;
    const inflictsDeafened = document.getElementById('inflictsDeafened').checked;
    const inflictsFrightened = document.getElementById('inflictsFrightened').checked;
    const inflictsIncapacitated = document.getElementById('inflictsIncapacitated').checked;
    const inflictsParalyzed = document.getElementById('inflictsParalyzed').checked;
    const inflictsPetrified = document.getElementById('inflictsPetrified').checked;
    const inflictsProne = document.getElementById('inflictsProne').checked;
    const inflictsRestrained = document.getElementById('inflictsRestrained').checked;
    const inflictsStunned = document.getElementById('inflictsStunned').checked;

    const spellcasterLevel = parseInt(document.getElementById('spellcasterLevel').value) || 0;

    // Build feature vector
    const features = {};

    // Initialize all features to 0
    if (modelData) {
        for (const feat of modelData.feature_columns) {
            features[feat] = 0;
        }
    }

    // Core features
    features['cr_numeric'] = cr;
    features['ac_value'] = ac;
    features['size_ordinal'] = currentSize;

    // Speed
    features['speed_ground'] = groundSpeed;
    features['speed_fly'] = flySpeed;
    features['speed_swim'] = swimSpeed;
    features['speed_burrow'] = burrowSpeed;
    features['speed_climb'] = climbSpeed;
    features['max_speed'] = Math.max(groundSpeed, flySpeed, swimSpeed, burrowSpeed, climbSpeed);
    features['movement_types_count'] = [groundSpeed, flySpeed, swimSpeed, burrowSpeed, climbSpeed].filter(s => s > 0).length;
    features['has_flying'] = flySpeed > 0 ? 1 : 0;

    // Combat features
    features['highest_attack_bonus'] = attack;
    features['highest_save_dc'] = saveDC;
    features['estimated_dpr'] = dpr;
    features['has_multiattack'] = hasMultiattack ? 1 : 0;

    // Defensive features
    features['resistance_count'] = resistances;
    features['immunity_count'] = immunities;

    // Special abilities
    features['has_legendary_actions'] = hasLegendary ? 1 : 0;
    features['legendary_action_count'] = hasLegendary ? 3 : 0;
    features['legendary_actions_per_round'] = hasLegendary ? 3 : 0;
    features['has_legendary_resistance'] = hasLegendaryRes ? 1 : 0;
    features['has_magic_resistance'] = hasMagicRes ? 1 : 0;
    features['has_regeneration'] = hasRegeneration ? 1 : 0;
    features['has_spellcasting'] = isSpellcaster ? 1 : 0;
    features['spellcaster_level'] = isSpellcaster ? spellcasterLevel : 0;
    features['has_grapple'] = hasGrapple ? 1 : 0;

    // Senses
    features['has_darkvision'] = hasDarkvision ? 1 : 0;
    features['darkvision_range'] = hasDarkvision ? 60 : 0;
    features['has_blindsight'] = hasBlindsight ? 1 : 0;
    features['has_truesight'] = hasTruesight ? 1 : 0;
    features['has_tremorsense'] = hasTremorsense ? 1 : 0;
    features['passive_perception'] = passivePerception;

    // Condition infliction
    features['inflicts_poisoned'] = inflictsPoisoned ? 1 : 0;
    features['inflicts_blinded'] = inflictsBlinded ? 1 : 0;
    features['inflicts_charmed'] = inflictsCharmed ? 1 : 0;
    features['inflicts_deafened'] = inflictsDeafened ? 1 : 0;
    features['inflicts_frightened'] = inflictsFrightened ? 1 : 0;
    features['inflicts_incapacitated'] = inflictsIncapacitated ? 1 : 0;
    features['inflicts_paralyzed'] = inflictsParalyzed ? 1 : 0;
    features['inflicts_petrified'] = inflictsPetrified ? 1 : 0;
    features['inflicts_prone'] = inflictsProne ? 1 : 0;
    features['inflicts_restrained'] = inflictsRestrained ? 1 : 0;
    features['inflicts_stunned'] = inflictsStunned ? 1 : 0;

    // Action economy (estimates)
    features['trait_count'] = 1 + (isSpellcaster ? 1 : 0) + (hasLegendaryRes ? 1 : 0) + (hasMagicRes ? 1 : 0);
    features['action_count'] = 1 + (hasMultiattack ? 1 : 0);
    features['skill_proficiency_count'] = skillProficiency;
    features['save_proficiency_count'] = saveProficiency;

    // Predict HP
    const hp = predictHP(features);
    const hpDice = calculateHPDice(hp, currentSize);

    // Calculate effective HP (with resistances)
    const effectiveHP = Math.round(hp * (1 + resistances * 0.5 + immunities * 0.75));

    // Get DMG baseline
    const baseline = getDMGBaseline(cr);
    const baselineHP = Math.round((baseline.hp[0] + baseline.hp[1]) / 2);
    const hpDiff = hp - baselineHP;

    const suggestedDPR = `${baseline.damage[0]}-${baseline.damage[1]}`;

    // Update display
    document.getElementById('hpValue').textContent = hp;
    document.getElementById('hpDice').textContent = `(${hpDice})`;
    document.getElementById('effectiveHP').textContent = effectiveHP;
    document.getElementById('suggestedDPR').textContent = suggestedDPR;
    document.getElementById('baselineHP').textContent = baselineHP;
    document.getElementById('hpDiff').textContent = hpDiff >= 0 ? `+${hpDiff}` : hpDiff;

    // Update stat block
    generateStatBlock(hp, hpDice, cr, ac, attack, saveDC);
}

// Generate stat block
function generateStatBlock(hp, hpDice, cr, ac, attack, saveDC) {
    const name = document.getElementById('monsterName').value || 'Custom Creature';
    const sizeNames = ['', 'Tiny', 'Small', 'Medium', 'Large', 'Huge', 'Gargantuan'];
    const sizeName = sizeNames[currentSize];

    const groundSpeed = parseInt(document.getElementById('speed').value) || 30;
    const flySpeed = parseInt(document.getElementById('flySpeed').value) || 0;
    const swimSpeed = parseInt(document.getElementById('swimSpeed').value) || 0;
    const burrowSpeed = parseInt(document.getElementById('burrowSpeed').value) || 0;
    const climbSpeed = parseInt(document.getElementById('climbSpeed').value) || 0;

    const hasMultiattack = document.getElementById('multiattack').checked;
    const hasLegendary = document.getElementById('legendary').checked;
    const hasLegendaryRes = document.getElementById('legendaryRes').checked;
    const hasMagicRes = document.getElementById('magicRes').checked;
    const hasRegeneration = document.getElementById('regeneration').checked;
    const isSpellcaster = document.getElementById('spellcasting').checked;
    const resistances = parseInt(document.getElementById('resistances').value) || 0;
    const immunities = parseInt(document.getElementById('immunities').value) || 0;

    const hasDarkvision = document.getElementById('darkvision').checked;
    const hasBlindsight = document.getElementById('blindsight').checked;
    const hasTruesight = document.getElementById('truesight').checked;

    // Build speed string
    let speedParts = [`${groundSpeed} ft.`];
    if (flySpeed > 0) speedParts.push(`fly ${flySpeed} ft.`);
    if (swimSpeed > 0) speedParts.push(`swim ${swimSpeed} ft.`);
    if (burrowSpeed > 0) speedParts.push(`burrow ${burrowSpeed} ft.`);
    if (climbSpeed > 0) speedParts.push(`climb ${climbSpeed} ft.`);
    const speedString = speedParts.join(', ');

    let statBlock = `<h3>${name}</h3>\n`;
    statBlock += `<div class="subtitle">${sizeName} creature, any alignment</div>\n`;
    statBlock += `<hr>\n`;
    statBlock += `<div class="stat-line"><span class="stat-label">Armor Class</span> ${ac}</div>\n`;
    statBlock += `<div class="stat-line"><span class="stat-label">Hit Points</span> ${hp} ${hpDice}</div>\n`;
    statBlock += `<div class="stat-line"><span class="stat-label">Speed</span> ${speedString}</div>\n`;
    statBlock += `<hr>\n`;

    // Ability scores (estimated)
    const str = 10 + Math.floor(cr * 0.5);
    const dex = 10 + Math.floor(cr * 0.5);
    const con = 10 + Math.floor(cr * 0.3);
    const int = isSpellcaster ? 14 + Math.floor(cr * 0.3) : 10;
    const wis = 10 + Math.floor(cr * 0.2);
    const cha = 10;

    statBlock += `<div class="stat-line">`;
    statBlock += `<span class="stat-label">STR</span> ${str} (+${Math.floor((str-10)/2)}) `;
    statBlock += `<span class="stat-label">DEX</span> ${dex} (+${Math.floor((dex-10)/2)}) `;
    statBlock += `<span class="stat-label">CON</span> ${con} (+${Math.floor((con-10)/2)})</div>\n`;
    statBlock += `<div class="stat-line">`;
    statBlock += `<span class="stat-label">INT</span> ${int} (+${Math.floor((int-10)/2)}) `;
    statBlock += `<span class="stat-label">WIS</span> ${wis} (+${Math.floor((wis-10)/2)}) `;
    statBlock += `<span class="stat-label">CHA</span> ${cha} (+${Math.floor((cha-10)/2)})</div>\n`;
    statBlock += `<hr>\n`;

    // Resistances/Immunities
    if (resistances > 0 || immunities > 0) {
        if (resistances > 0) {
            statBlock += `<div class="stat-line"><span class="stat-label">Damage Resistances</span> [${resistances} types]</div>\n`;
        }
        if (immunities > 0) {
            statBlock += `<div class="stat-line"><span class="stat-label">Damage Immunities</span> [${immunities} types]</div>\n`;
        }
    }

    // Senses
    const passivePerception = parseInt(document.getElementById('passivePerception').value) || 10;
    let senses = [];
    if (hasDarkvision) senses.push('darkvision 60 ft.');
    if (hasBlindsight) senses.push('blindsight 30 ft.');
    if (hasTruesight) senses.push('truesight 60 ft.');
    senses.push(`passive Perception ${passivePerception}`);
    statBlock += `<div class="stat-line"><span class="stat-label">Senses</span> ${senses.join(', ')}</div>\n`;

    statBlock += `<div class="stat-line"><span class="stat-label">Languages</span> Common</div>\n`;
    statBlock += `<div class="stat-line"><span class="stat-label">Challenge</span> ${cr} (${getCRXP(cr)} XP)</div>\n`;
    statBlock += `<hr>\n`;

    // Traits
    if (hasLegendaryRes || hasMagicRes || hasRegeneration || isSpellcaster) {
        if (hasLegendaryRes) {
            statBlock += `<div class="stat-line"><span class="stat-label">Legendary Resistance (3/Day).</span> If the creature fails a saving throw, it can choose to succeed instead.</div>\n`;
        }
        if (hasMagicRes) {
            statBlock += `<div class="stat-line"><span class="stat-label">Magic Resistance.</span> The creature has advantage on saving throws against spells and other magical effects.</div>\n`;
        }
        if (hasRegeneration) {
            statBlock += `<div class="stat-line"><span class="stat-label">Regeneration.</span> The creature regains 10 hit points at the start of its turn.</div>\n`;
        }
        if (isSpellcaster) {
            const spellLevel = parseInt(document.getElementById('spellcasterLevel').value) || 5;
            const highestSpell = parseInt(document.getElementById('highestSpellLevel').value) || 3;
            statBlock += `<div class="stat-line"><span class="stat-label">Spellcasting.</span> The creature is a ${spellLevel}th-level spellcaster (spell save DC ${saveDC}, +${attack} to hit with spell attacks). It has access to spells up to ${highestSpell}${getOrdinal(highestSpell)} level.</div>\n`;
        }
        statBlock += `<hr>\n`;
    }

    // Actions
    statBlock += `<div class="stat-line"><span class="stat-label">ACTIONS</span></div>\n`;
    if (hasMultiattack) {
        statBlock += `<div class="stat-line"><span class="stat-label">Multiattack.</span> The creature makes two attacks.</div>\n`;
    }
    statBlock += `<div class="stat-line"><span class="stat-label">Attack.</span> Melee Weapon Attack: +${attack} to hit, reach 5 ft., one target. Hit: damage.</div>\n`;

    // Legendary Actions
    if (hasLegendary) {
        statBlock += `<hr>\n`;
        statBlock += `<div class="stat-line"><span class="stat-label">LEGENDARY ACTIONS</span></div>\n`;
        statBlock += `<div class="stat-line">The creature can take 3 legendary actions, choosing from the options below. Only one legendary action can be used at a time and only at the end of another creature's turn. The creature regains spent legendary actions at the start of its turn.</div>\n`;
        statBlock += `<div class="stat-line"><span class="stat-label">Detect.</span> The creature makes a Wisdom (Perception) check.</div>\n`;
        statBlock += `<div class="stat-line"><span class="stat-label">Attack.</span> The creature makes one attack.</div>\n`;
    }

    document.getElementById('statBlock').innerHTML = statBlock;
}

// Helper functions
function getCRXP(cr) {
    const xpTable = {
        0: 0, 0.125: 25, 0.25: 50, 0.5: 100, 1: 200, 2: 450, 3: 700, 4: 1100,
        5: 1800, 6: 2300, 7: 2900, 8: 3900, 9: 5000, 10: 5900, 11: 7200,
        12: 8400, 13: 10000, 14: 11500, 15: 13000, 16: 15000, 17: 18000,
        18: 20000, 19: 22000, 20: 25000, 21: 33000, 22: 41000, 23: 50000,
        24: 62000, 25: 75000, 26: 90000, 27: 105000, 28: 120000, 29: 135000, 30: 155000
    };
    return xpTable[cr] || 0;
}

function getOrdinal(n) {
    const s = ['th', 'st', 'nd', 'rd'];
    const v = n % 100;
    return s[(v - 20) % 10] || s[v] || s[0];
}

// Export stat block to clipboard
function exportStatBlock() {
    const statBlock = document.getElementById('statBlock').innerText;
    navigator.clipboard.writeText(statBlock).then(() => {
        alert('Stat block copied to clipboard!');
    }).catch(err => {
        console.error('Failed to copy: ', err);
    });
}

// Generate random monster
function randomMonster() {
    const randomCR = [0.125, 0.25, 0.5, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10][Math.floor(Math.random() * 13)];
    const baseline = getDMGBaseline(randomCR);

    document.getElementById('cr').value = randomCR;
    document.getElementById('ac').value = baseline.ac + Math.floor(Math.random() * 5) - 2;
    document.getElementById('attack').value = baseline.attack + Math.floor(Math.random() * 3) - 1;
    document.getElementById('saveDC').value = baseline.save;
    document.getElementById('dpr').value = Math.floor((baseline.damage[0] + baseline.damage[1]) / 2);

    // Speeds
    document.getElementById('speed').value = 30 + Math.floor(Math.random() * 3) * 10;
    document.getElementById('flySpeed').value = Math.random() > 0.7 ? 30 + Math.floor(Math.random() * 3) * 10 : 0;
    document.getElementById('swimSpeed').value = Math.random() > 0.8 ? 30 + Math.floor(Math.random() * 2) * 10 : 0;
    document.getElementById('burrowSpeed').value = Math.random() > 0.9 ? 20 + Math.floor(Math.random() * 2) * 10 : 0;
    document.getElementById('climbSpeed').value = Math.random() > 0.8 ? 20 + Math.floor(Math.random() * 2) * 10 : 0;

    // Proficiencies
    document.getElementById('saveProficiency').value = randomCR >= 5 ? 2 : (randomCR >= 2 ? 1 : 0);
    document.getElementById('skillProficiency').value = Math.floor(randomCR / 2);
    document.getElementById('passivePerception').value = 10 + Math.floor(randomCR / 2);

    document.getElementById('multiattack').checked = randomCR >= 2 ? Math.random() > 0.5 : false;
    document.getElementById('legendary').checked = randomCR >= 10 ? Math.random() > 0.5 : false;
    document.getElementById('legendaryRes').checked = randomCR >= 15 ? Math.random() > 0.5 : false;
    document.getElementById('spellcasting').checked = Math.random() > 0.7;

    document.getElementById('resistances').value = randomCR >= 5 ? Math.floor(Math.random() * 3) : 0;
    document.getElementById('immunities').value = randomCR >= 10 ? Math.floor(Math.random() * 2) : 0;

    // Random size weighted towards Medium
    const sizes = [2, 3, 3, 3, 3, 4, 4, 5];
    currentSize = sizes[Math.floor(Math.random() * sizes.length)];
    updateSizeButtons();

    const names = ['Fierce', 'Ancient', 'Shadow', 'Storm', 'Fire', 'Ice', 'Dark', 'Light'];
    const types = ['Beast', 'Elemental', 'Fiend', 'Dragon', 'Aberration', 'Construct'];
    document.getElementById('monsterName').value = names[Math.floor(Math.random() * names.length)] + ' ' + types[Math.floor(Math.random() * types.length)];

    calculateHP();
}

// Size button handlers
function updateSizeButtons() {
    document.querySelectorAll('.size-btn').forEach(btn => {
        btn.classList.remove('active');
        if (parseInt(btn.dataset.size) === currentSize) {
            btn.classList.add('active');
        }
    });
}

// Event listeners
document.addEventListener('DOMContentLoaded', () => {
    loadModel();

    // Size buttons
    document.querySelectorAll('.size-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            currentSize = parseInt(btn.dataset.size);
            updateSizeButtons();
            calculateHP();
        });
    });

    // Spellcasting toggle
    document.getElementById('spellcasting').addEventListener('change', (e) => {
        document.getElementById('spellcasterOptions').style.display = e.target.checked ? 'block' : 'none';
        calculateHP();
    });

    // Auto-calculate on any input change
    const inputs = document.querySelectorAll('input, select');
    inputs.forEach(input => {
        input.addEventListener('change', calculateHP);
        input.addEventListener('input', calculateHP);
    });
});
