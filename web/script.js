// API Configuration
const DEFAULT_LOCAL_API = 'http://localhost:8000';
const DEFAULT_PROD_API = 'https://friends-league-tracker.vercel.app';
const API_BASE_URL = window.__API_BASE_URL || (window.location.hostname === 'localhost' ? DEFAULT_LOCAL_API : DEFAULT_PROD_API);

// Global state
let leaderboardData = null;
let battlesData = null;

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, initializing app...');
    loadData();
    
    // Add initial click listeners
    addClickListeners();
});

// Load all data from the API
async function loadData() {
    try {
        await Promise.all([
            loadLeaderboard(),
            loadRecentBattles()
        ]);
    } catch (error) {
        console.error('Error loading data:', error);
        showError('Failed to load data. Please try again.');
    }
}

// Load leaderboard data
async function loadLeaderboard() {
    try {
        const response = await fetch(`${API_BASE_URL}/leaderboard`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        leaderboardData = data;
        
        renderLeaderboard(data);
        updateHeaderStats(data);
        
    } catch (error) {
        console.error('Error loading leaderboard:', error);
        showError('Failed to load leaderboard data.');
    }
}

// Load recent battles
async function loadRecentBattles() {
    try {
        const response = await fetch(`${API_BASE_URL}/battles/recent?limit=10`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        battlesData = data;
        
        renderRecentBattles(data);
        
    } catch (error) {
        console.error('Error loading battles:', error);
        showError('Failed to load battle data.');
    }
}

// Render leaderboard
function renderLeaderboard(data) {
    const leaderboard = document.getElementById('leaderboard');
    
    console.log('Rendering leaderboard with data:', data);
    
    if (!data.players || data.players.length === 0) {
        leaderboard.innerHTML = `
            <div class="loading">
                <i class="fas fa-exclamation-triangle"></i>
                No players found. Add some players to get started!
            </div>
        `;
        return;
    }
    
    const leaderboardHTML = data.players.map((player, index) => {
        const rank = index + 1;
        const rankClass = rank === 1 ? 'rank-1' : rank === 2 ? 'rank-2' : rank === 3 ? 'rank-3' : '';
        
        return `
            <div class="player-card ${rankClass}">
                <div class="rank-badge">${rank}</div>
                <div class="player-info">
                    <div class="player-name">${player.name || player.player_tag}</div>
                    <div class="player-tag">#${player.player_tag}</div>
                </div>
                <div class="player-stats">
                    <div class="stat">
                        <div class="stat-label">Record</div>
                        <div class="stat-value">${player.wins}-${player.losses}</div>
                    </div>
                    <div class="stat">
                        <div class="stat-label">Win %</div>
                        <div class="stat-value winrate">${player.winrate.toFixed(1)}%</div>
                    </div>
                    <div class="stat">
                        <div class="stat-label">ELO</div>
                        <div class="stat-value elo">${Math.round(player.elo_rating)}</div>
                    </div>
                </div>
            </div>
        `;
    }).join('');
    
    console.log('Generated leaderboard HTML:', leaderboardHTML);
    leaderboard.innerHTML = leaderboardHTML;
    
    // Add click listeners after rendering
    setTimeout(() => {
        const playerCards = document.querySelectorAll('.player-card');
        console.log('Found player cards:', playerCards.length);
        playerCards.forEach((card, index) => {
            console.log(`Card ${index}:`, card);
        });
        addClickListeners();
    }, 100);
}

// Render recent battles
function renderRecentBattles(data) {
    const battles = document.getElementById('recent-battles');
    
    if (!data || data.length === 0) {
        battles.innerHTML = `
            <div class="loading">
                <i class="fas fa-exclamation-triangle"></i>
                No recent battles found.
            </div>
        `;
        return;
    }
    
    const battlesHTML = data.map(battle => {
        const date = new Date(battle.timestamp);
        // Convert UTC to EST - add 4 hours to get 3:49 PM
        const estDate = new Date(date.getTime() + (-60 * 60 * 1000));
        const timeStr = estDate.toLocaleDateString() + ' ' + estDate.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}) + ' EST';
        
        // Get player names from leaderboard data if available
        const player1Name = getPlayerName(battle.player1);
        const player2Name = getPlayerName(battle.player2);
        const winnerName = getPlayerName(battle.winner);
        
        return `
            <div class="battle-item">
                <div class="battle-time">${timeStr}</div>
                <div class="battle-players">
                    <div class="battle-player ${battle.winner === battle.player1 ? 'battle-winner' : 'battle-loser'}">
                        ${player1Name}
                    </div>
                    <div class="battle-vs">vs</div>
                    <div class="battle-player ${battle.winner === battle.player2 ? 'battle-winner' : 'battle-loser'}">
                        ${player2Name}
                    </div>
                </div>
                <div class="battle-result">
                    <div class="battle-type">${battle.battle_type}</div>
                    ${battle.elo_change_winner !== null && battle.elo_change_loser !== null && 
                      !isNaN(battle.elo_change_winner) && !isNaN(battle.elo_change_loser) ? `
                        <div class="battle-elo-changes">
                            <div class="elo-change winner">
                                <i class="fas fa-arrow-up"></i> +${Math.round(battle.elo_change_winner)}
                            </div>
                            <div class="elo-change loser">
                                <i class="fas fa-arrow-down"></i> ${Math.round(battle.elo_change_loser)}
                            </div>
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
    }).join('');
    
    battles.innerHTML = battlesHTML;
}

// Update header statistics
function updateHeaderStats(data) {
    const totalMatches = document.getElementById('total-matches');
    const lastUpdated = document.getElementById('last-updated');
    
    if (data.total_matches !== undefined) {
        totalMatches.textContent = data.total_matches;
    }
    
    if (data.last_updated) {
        const date = new Date(data.last_updated);
        lastUpdated.textContent = date.toLocaleString();
    }
}

// Refresh data manually
function refreshData() {
    const refreshBtn = document.querySelector('.refresh-btn');
    const icon = refreshBtn.querySelector('i');
    
    // Add spinning animation
    icon.classList.add('fa-spin');
    refreshBtn.disabled = true;
    
    loadData().finally(() => {
        // Remove spinning animation
        icon.classList.remove('fa-spin');
        refreshBtn.disabled = false;
    });
}

// Show error message
function showError(message) {
    const leaderboard = document.getElementById('leaderboard');
    leaderboard.innerHTML = `
        <div class="loading">
            <i class="fas fa-exclamation-triangle"></i>
            ${message}
        </div>
    `;
}

// Utility function to format numbers
function formatNumber(num) {
    return new Intl.NumberFormat().format(num);
}

// Utility function to format percentages
function formatPercentage(num) {
    return `${num.toFixed(1)}%`;
}

// Utility function to format dates
function formatDate(dateString) {
    const date = new Date(dateString);
    // Convert UTC to EST - add 4 hours to get 3:49 PM
    const estDate = new Date(date.getTime() + (4 * 60 * 60 * 1000));
    return estDate.toLocaleDateString() + ' ' + estDate.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}) + ' EST';
}

// Get player name from tag
function getPlayerName(playerTag) {
    if (!leaderboardData || !leaderboardData.players) {
        return playerTag; // Fallback to tag if no leaderboard data
    }
    
    const player = leaderboardData.players.find(p => p.player_tag === playerTag);
    return player ? (player.name || player.player_tag) : playerTag;
}

// Add click listeners after DOM is loaded
function addClickListeners() {
    console.log('Adding click listeners...');
    
    // Remove existing listeners to avoid duplicates
    document.removeEventListener('click', handleClick);
    document.addEventListener('click', handleClick);
}

function handleClick(e) {
    console.log('Click detected on:', e.target);
    
    // Handle player card clicks
    if (e.target.closest('.player-card')) {
        console.log('Player card clicked!');
        const card = e.target.closest('.player-card');
        const playerName = card.querySelector('.player-name').textContent;
        const playerTag = card.querySelector('.player-tag').textContent.replace('#', '');
        
        console.log('Player:', playerName, 'Tag:', playerTag);
        
        // Add click effect
        card.style.transform = 'scale(0.98)';
        setTimeout(() => {
            card.style.transform = '';
        }, 150);
        
        // Show player details
        showPlayerDetails(playerTag, playerName);
        return;
    }
    
    // Add click effects to battle items
    if (e.target.closest('.battle-item')) {
        const item = e.target.closest('.battle-item');
        item.style.transform = 'scale(0.98)';
        setTimeout(() => {
            item.style.transform = '';
        }, 150);
        return;
    }
    
    // Handle modal close
    if (e.target.classList.contains('modal-overlay') || e.target.classList.contains('modal-close')) {
        closePlayerDetails();
        return;
    }
}

// Add keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // R key to refresh
    if (e.key === 'r' || e.key === 'R') {
        if (e.ctrlKey || e.metaKey) {
            e.preventDefault();
            refreshData();
        }
    }
});

// Show player details modal
async function showPlayerDetails(playerTag, playerName) {
    try {
        // Get player's head-to-head records
        const headToHeadData = await getPlayerHeadToHead(playerTag);
        
        // Create modal HTML
        const modalHTML = `
            <div class="modal-overlay">
                <div class="modal-content">
                    <div class="modal-header">
                        <h2><i class="fas fa-user"></i> ${playerName}</h2>
                        <button class="modal-close">&times;</button>
                    </div>
                    <div class="modal-body">
                        <div class="player-overview">
                            <div class="overview-stats">
                                <div class="stat-item">
                                    <span class="stat-label">Overall Record</span>
                                    <span class="stat-value">${headToHeadData.overall.wins}-${headToHeadData.overall.losses}</span>
                                </div>
                                <div class="stat-item">
                                    <span class="stat-label">Win Rate</span>
                                    <span class="stat-value">${headToHeadData.overall.winrate.toFixed(1)}%</span>
                                </div>
                                <div class="stat-item">
                                    <span class="stat-label">ELO Rating</span>
                                    <span class="stat-value">${Math.round(headToHeadData.overall.elo)}</span>
                                </div>
                            </div>
                        </div>
                        
                        <div class="head-to-head-section">
                            <h3><i class="fas fa-swords"></i> Head-to-Head Records</h3>
                            <div class="head-to-head-grid">
                                ${headToHeadData.opponents.map(opponent => `
                                    <div class="opponent-card">
                                        <div class="opponent-name">${opponent.name}</div>
                                        <div class="opponent-record">
                                            <span class="record">${opponent.wins}-${opponent.losses}</span>
                                            <span class="winrate">${opponent.winrate.toFixed(1)}%</span>
                                        </div>
                                        <div class="opponent-crowns">
                                            <i class="fas fa-crown"></i> ${opponent.crowns}
                                        </div>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                        
                        <div class="recent-battles-section">
                            <h3><i class="fas fa-history"></i> Recent Battles</h3>
                            <div class="player-battles">
                                ${headToHeadData.recentBattles.map(battle => `
                                    <div class="battle-item">
                                        <div class="battle-time">${formatDate(battle.timestamp)}</div>
                                        <div class="battle-players">
                                            <div class="battle-player ${battle.winner === playerTag ? 'battle-winner' : 'battle-loser'}">
                                                ${getPlayerName(battle.player1)}
                                            </div>
                                            <div class="battle-vs">vs</div>
                                            <div class="battle-player ${battle.winner === battle.player2 ? 'battle-winner' : 'battle-loser'}">
                                                ${getPlayerName(battle.player2)}
                                            </div>
                                        </div>
                                        <div class="battle-result">
                                            <div class="battle-crowns">
                                                <i class="fas fa-crown"></i> ${battle.crowns}
                                            </div>
                                        </div>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Add modal to page
        document.body.insertAdjacentHTML('beforeend', modalHTML);
        
    } catch (error) {
        console.error('Error showing player details:', error);
    }
}

// Close player details modal
function closePlayerDetails() {
    const modal = document.querySelector('.modal-overlay');
    if (modal) {
        modal.remove();
    }
}

// Get player head-to-head data
async function getPlayerHeadToHead(playerTag) {
    try {
        // Get player's overall stats from the database
        const playerResponse = await fetch(`${API_BASE_URL}/player/${playerTag}`);
        const playerStats = await playerResponse.json();
        
        // Get all battles for head-to-head and recent battles
        const response = await fetch(`${API_BASE_URL}/battles/recent?limit=1000`);
        const battles = await response.json();
        
        // Filter battles involving this player
        const playerBattles = battles.filter(battle => 
            battle.player1 === playerTag || battle.player2 === playerTag
        );
        
        // Calculate head-to-head records
        const opponents = {};
        
        playerBattles.forEach(battle => {
            const opponent = battle.player1 === playerTag ? battle.player2 : battle.player1;
            const opponentName = getPlayerName(opponent);
            
            if (!opponents[opponent]) {
                opponents[opponent] = {
                    name: opponentName,
                    wins: 0,
                    losses: 0,
                    crowns: 0
                };
            }
            
            if (battle.winner === playerTag) {
                opponents[opponent].wins++;
                opponents[opponent].crowns += battle.crowns;
            } else {
                opponents[opponent].losses++;
            }
        });
        
        // Calculate win rates
        Object.values(opponents).forEach(opponent => {
            const total = opponent.wins + opponent.losses;
            opponent.winrate = total > 0 ? (opponent.wins / total) * 100 : 0;
        });
        
        return {
            overall: {
                wins: playerStats.wins,
                losses: playerStats.losses,
                winrate: playerStats.winrate,
                elo: playerStats.elo_rating,
                crowns: playerStats.total_crowns
            },
            opponents: Object.values(opponents).sort((a, b) => (b.wins + b.losses) - (a.wins + a.losses)),
            recentBattles: playerBattles.slice(0, 10)
        };
        
    } catch (error) {
        console.error('Error getting head-to-head data:', error);
        return {
            overall: { wins: 0, losses: 0, winrate: 0, elo: 1200, crowns: 0 },
            opponents: [],
            recentBattles: []
        };
    }
}

// Add service worker for offline functionality (optional)
if ('serviceWorker' in navigator) {
    window.addEventListener('load', function() {
        navigator.serviceWorker.register('/sw.js')
            .then(function(registration) {
                console.log('ServiceWorker registration successful');
            })
            .catch(function(err) {
                console.log('ServiceWorker registration failed');
            });
    });
}
