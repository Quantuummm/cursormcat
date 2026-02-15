/**
 * MCAT Mastery — Crystal Exchange (Shop)
 * 
 * Tabs: Upgrades | Cosmetics | Items
 * Uses Energy Crystals as single currency.
 */

const SHOP_ITEMS = {
    upgrades: [
        { id: 'energy_max_7',    name: 'Neural Capacity +1',    desc: 'Increase max charges to 7',   cost: 500,  icon: '⚡', category: 'energy',   oneTime: true, effect: () => { Player.neuralCharge.max = Math.max(Player.neuralCharge.max, 7); } },
        { id: 'energy_max_8',    name: 'Neural Capacity +2',    desc: 'Increase max charges to 8',   cost: 1200, icon: '⚡', category: 'energy',   oneTime: true, requires: 'energy_max_7', effect: () => { Player.neuralCharge.max = Math.max(Player.neuralCharge.max, 8); } },
        { id: 'regen_speed_1',   name: 'Fast Regen I',          desc: 'Regen charges 25% faster',    cost: 800,  icon: '⏱', category: 'energy',   oneTime: true, effect: () => { Player.neuralCharge.regenRateMs = 5400000; } },
        { id: 'regen_speed_2',   name: 'Fast Regen II',         desc: 'Regen charges 50% faster',    cost: 2000, icon: '⏱', category: 'energy',   oneTime: true, requires: 'regen_speed_1', effect: () => { Player.neuralCharge.regenRateMs = 3600000; } },
        { id: 'streak_shield',   name: 'Streak Shield',         desc: 'Protect streak for 1 missed day', cost: 300, icon: '🛡', category: 'streak', oneTime: false, effect: () => { Player._streakShields = (Player._streakShields || 0) + 1; } },
        { id: 'crystal_bonus',   name: 'Crystal Magnetism',     desc: '+20% crystals from missions', cost: 1500, icon: '🧲', category: 'earning', oneTime: true, effect: () => { Player._crystalMultiplier = 1.2; } },
    ],
    cosmetics: [
        { id: 'ship_nova',    name: 'Nova Class Ship',     desc: 'Sleek golden hull', cost: 800,  icon: '🚀', preview: 'ship-nova' },
        { id: 'ship_phantom', name: 'Phantom Class Ship',  desc: 'Dark stealth hull', cost: 800,  icon: '🛸', preview: 'ship-phantom' },
        { id: 'ship_aurora',  name: 'Aurora Class Ship',   desc: 'Iridescent hull',   cost: 1200, icon: '✨', preview: 'ship-aurora' },
        { id: 'trail_stars',  name: 'Stardust Trail',      desc: 'Sparkling trail effect',  cost: 400, icon: '⭐', preview: 'trail-stars' },
        { id: 'trail_flame',  name: 'Flame Trail',         desc: 'Fiery trail effect',      cost: 400, icon: '🔥', preview: 'trail-flame' },
        { id: 'trail_frost',  name: 'Frost Trail',         desc: 'Icy trail effect',        cost: 400, icon: '❄️', preview: 'trail-frost' },
        { id: 'badge_scholar',name: 'Scholar Badge',       desc: 'Complete 100 sections',   cost: 600, icon: '🎓', preview: 'badge-scholar' },
        { id: 'badge_fire',   name: 'Inferno Badge',       desc: '30-day streak achievement',cost: 600, icon: '🔥', preview: 'badge-fire' },
    ],
    items: [
        { id: 'quick_charge',  name: 'Quick Charge',       desc: 'Restore 1 Neural Charge instantly',  cost: 50,  icon: '⚡', stackable: true, effect: () => { Player.neuralCharge.current = Math.min(Player.neuralCharge.max, Player.neuralCharge.current + 1); } },
        { id: 'full_charge',   name: 'Full Charge',        desc: 'Restore all Neural Charges',         cost: 150, icon: '🔋', stackable: true, effect: () => { Player.neuralCharge.current = Player.neuralCharge.max; } },
        { id: 'fog_reveal',    name: 'Fog Revealer',       desc: 'Reveal 3 fogged tiles on any planet',cost: 200, icon: '👁', stackable: true },
        { id: 'xp_boost',      name: 'XP Boost (1h)',      desc: '2x XP for 1 hour',                  cost: 100, icon: '⭐', stackable: true },
    ],
};

function initShop(tab = 'upgrades') {
    _wireShopTabs(tab);
    _loadShopTab(tab);
    _updateShopBalance();
}

function _wireShopTabs(activeTab) {
    document.querySelectorAll('.shop-tabs .tab').forEach(tabEl => {
        tabEl.classList.toggle('active', tabEl.dataset.tab === activeTab);
        tabEl.onclick = () => {
            document.querySelectorAll('.shop-tabs .tab').forEach(t => t.classList.remove('active'));
            tabEl.classList.add('active');
            _loadShopTab(tabEl.dataset.tab);
        };
    });
}

function _updateShopBalance() {
    const el = document.getElementById('shop-crystal-count');
    if (el) el.textContent = Player.crystals;
}

function _loadShopTab(tab) {
    const grid = document.getElementById('shop-grid');
    if (!grid) return;
    
    const items = SHOP_ITEMS[tab] || [];
    const purchased = _getPurchasedItems();
    
    grid.innerHTML = items.map(item => {
        const owned = purchased.includes(item.id);
        const canAfford = Player.crystals >= item.cost;
        const requiresMet = !item.requires || purchased.includes(item.requires);
        const disabled = (owned && item.oneTime) || !canAfford || !requiresMet;
        
        return `
            <div class="shop-card ${owned && item.oneTime ? 'owned' : ''} ${!canAfford ? 'expensive' : ''} ${!requiresMet ? 'locked' : ''}">
                <div class="shop-icon">${item.icon}</div>
                <div class="shop-info">
                    <span class="shop-name">${item.name}</span>
                    <span class="shop-desc">${item.desc}</span>
                </div>
                <div class="shop-price-row">
                    <span class="shop-price ${canAfford ? '' : 'no-afford'}">
                        ✨ ${item.cost}
                    </span>
                    <button class="btn btn-sm ${disabled ? 'btn-disabled' : 'btn-primary'}" 
                            data-item-id="${item.id}" data-tab="${tab}"
                            ${disabled ? 'disabled' : ''}>
                        ${owned && item.oneTime ? 'Owned' : !requiresMet ? '🔒 Locked' : 'Buy'}
                    </button>
                </div>
            </div>
        `;
    }).join('');
    
    // Wire buy buttons
    grid.querySelectorAll('.btn-primary[data-item-id]').forEach(btn => {
        btn.addEventListener('click', () => {
            _purchaseItem(btn.dataset.itemId, btn.dataset.tab);
        });
    });
}

function _purchaseItem(itemId, tab) {
    const items = SHOP_ITEMS[tab] || [];
    const item = items.find(i => i.id === itemId);
    if (!item) return;
    
    if (!spendCrystals(item.cost)) {
        showToast('Not enough crystals!');
        return;
    }
    
    // Record purchase
    _recordPurchase(itemId);
    
    // Apply effect
    if (item.effect) {
        item.effect();
    }
    
    // Apply cosmetics
    if (tab === 'cosmetics') {
        if (item.id.startsWith('ship_')) {
            Player.cosmetics.shipSkin = item.preview;
        } else if (item.id.startsWith('trail_')) {
            Player.cosmetics.trailEffect = item.preview;
        } else if (item.id.startsWith('badge_')) {
            if (!Player.cosmetics.badges.includes(item.id)) {
                Player.cosmetics.badges.push(item.id);
            }
        }
    }
    
    showToast(`✅ Purchased ${item.name}!`);
    _updateShopBalance();
    _loadShopTab(tab);
    
    // Save player state
    if (typeof _saveLocal === 'function') _saveLocal();
}

function _getPurchasedItems() {
    try {
        const saved = localStorage.getItem('mcat_purchases');
        return saved ? JSON.parse(saved) : [];
    } catch (e) {
        return [];
    }
}

function _recordPurchase(itemId) {
    const purchases = _getPurchasedItems();
    if (!purchases.includes(itemId)) {
        purchases.push(itemId);
    }
    localStorage.setItem('mcat_purchases', JSON.stringify(purchases));
}
