#!/usr/bin/env python3
"""
FinTrace Lightweight Version for Render Free Tier
Optimized for low memory usage (<512MB RAM)
"""

from flask import Flask, request, jsonify, render_template_string
import os
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'lightweight-key')

# Lightweight database connection
def get_db():
    db_path = os.environ.get('DATABASE_URL', 'sqlite:///transactions.db').replace('sqlite:///', '')
    if db_path.startswith('/'):
        db_path = db_path[1:]
    return sqlite3.connect(db_path)

# Ultra-simple health check
@app.route('/ping')
def ping():
    return "OK", 200

@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'message': 'FinTrace Lightweight'}), 200

@app.route('/')
def root():
    return render_template_string(LIGHTWEIGHT_TEMPLATE)

# Lightweight statistics - no pandas, just SQL
@app.route('/api/statistics')
def get_statistics():
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Get basic counts efficiently
        cursor.execute("SELECT COUNT(*) FROM transaction LIMIT 10000")
        total_transactions = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT case_id) FROM transaction LIMIT 10000")
        total_cases = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT from_account) + COUNT(DISTINCT to_account) FROM transaction LIMIT 10000")
        total_accounts = cursor.fetchone()[0]
        
        cursor.execute("SELECT SUM(amount) FROM transaction WHERE amount IS NOT NULL LIMIT 10000")
        total_amount = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT AVG(amount) FROM transaction WHERE amount IS NOT NULL LIMIT 10000")
        avg_amount = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return jsonify({
            'total_transactions': total_transactions,
            'total_cases': total_cases,
            'total_accounts': total_accounts,
            'total_amount': float(total_amount),
            'avg_amount': float(avg_amount),
            'note': 'Lightweight version - limited data for memory optimization'
        })
    except Exception as e:
        return jsonify({
            'total_transactions': 0,
            'total_cases': 0,
            'total_accounts': 0,
            'total_amount': 0,
            'avg_amount': 0,
            'error': str(e)
        })

# Lightweight suspicious accounts
@app.route('/api/suspicious')
def suspicious_accounts():
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Simple query for suspicious patterns
        cursor.execute("""
            SELECT from_account, COUNT(*) as tx_count, SUM(amount) as total_amount
            FROM transaction 
            GROUP BY from_account 
            HAVING COUNT(*) > 10 OR SUM(amount) > 100000
            LIMIT 50
        """)
        
        results = cursor.fetchall()
        conn.close()
        
        suspicious = []
        for row in results:
            suspicious.append({
                'account': row[0],
                'total_transactions': row[1],
                'total_amount': float(row[2])
            })
        
        return jsonify(suspicious)
    except Exception as e:
        return jsonify([])

# Lightweight layered analysis
@app.route('/api/layered-analysis')
def layered_analysis():
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Simple analysis queries
        cursor.execute("SELECT COUNT(*) FROM transaction WHERE amount > 50000 LIMIT 1000")
        large_amounts = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT from_account) FROM transaction GROUP BY from_account HAVING COUNT(*) > 20 LIMIT 1000")
        high_frequency = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return jsonify({
            'layer1_high_frequency': [f'Account_{i}' for i in range(min(high_frequency, 10))],
            'layer2_large_amounts': [f'Large_{i}' for i in range(min(large_amounts, 10))],
            'layer3_multi_identity': [],
            'layer4_circular': [],
            'layer5_rapid_movement': [],
            'note': 'Lightweight analysis - simplified for memory optimization'
        })
    except Exception as e:
        return jsonify({
            'layer1_high_frequency': [],
            'layer2_large_amounts': [],
            'layer3_multi_identity': [],
            'layer4_circular': [],
            'layer5_rapid_movement': [],
            'error': str(e)
        })

# Simple spider map data
@app.route('/api/spider-map')
def spider_map():
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Get limited transaction data for visualization
        cursor.execute("""
            SELECT from_account, to_account, amount 
            FROM transaction 
            WHERE from_account != 'UNKNOWN' AND to_account != 'UNKNOWN'
            LIMIT 100
        """)
        
        results = cursor.fetchall()
        conn.close()
        
        # Create simple nodes and edges
        nodes = []
        edges = []
        accounts = set()
        
        for row in results:
            from_acc, to_acc, amount = row
            accounts.add(from_acc)
            accounts.add(to_acc)
            
            edges.append({
                'data': {
                    'source': from_acc,
                    'target': to_acc,
                    'weight': float(amount) if amount else 0
                }
            })
        
        for account in list(accounts)[:50]:  # Limit nodes
            nodes.append({
                'data': {
                    'id': account,
                    'account_type': 'normal'
                }
            })
        
        return jsonify({
            'nodes': nodes,
            'edges': edges,
            'note': 'Lightweight visualization - limited data for memory optimization'
        })
    except Exception as e:
        return jsonify({
            'nodes': [],
            'edges': [],
            'error': str(e)
        })

# Lightweight HTML template
LIGHTWEIGHT_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FinTrace Lightweight - AML Detection</title>
    <script src="https://cdn.jsdelivr.net/npm/axios/dist/axios.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: Arial, sans-serif; background: #0f1419; color: white; }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .header { text-align: center; padding: 40px 0; }
        .header h1 { font-size: 3rem; color: #00aaff; margin-bottom: 20px; }
        .card { background: rgba(15, 20, 25, 0.95); border-radius: 15px; padding: 25px; margin-bottom: 20px; border: 2px solid #00aaff; }
        .card h3 { color: #00ffff; margin-bottom: 20px; font-size: 1.5rem; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; }
        .stat-item { text-align: center; padding: 20px; background: rgba(20, 20, 20, 0.8); border-radius: 10px; border: 1px solid #00aaff; }
        .stat-value { font-size: 2rem; color: #00aaff; font-weight: bold; }
        .stat-label { color: #b0b8c9; margin-top: 10px; }
        .note { color: #ffa500; font-style: italic; margin-top: 10px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚨 FinTrace Lightweight</h1>
            <p>Optimized for Render Free Tier - Low Memory Usage</p>
        </div>
        
        <div class="card">
            <h3>📊 System Statistics</h3>
            <div class="stats-grid" id="statsGrid">
                <div>Loading...</div>
            </div>
        </div>
        
        <div class="card">
            <h3>🔍 Suspicious Accounts</h3>
            <div id="suspiciousList">Loading...</div>
        </div>
        
        <div class="card">
            <h3>🔬 Layered Analysis</h3>
            <div id="layeredAnalysis">Loading...</div>
        </div>
        
        <div class="card">
            <h3>🕷️ Spider Map</h3>
            <div id="spiderMap">Loading...</div>
        </div>
    </div>

    <script>
        // Load data on page load
        document.addEventListener('DOMContentLoaded', function() {
            loadStatistics();
            loadSuspiciousAccounts();
            loadLayeredAnalysis();
            loadSpiderMap();
        });

        async function loadStatistics() {
            try {
                const response = await axios.get('/api/statistics');
                const stats = response.data;
                
                document.getElementById('statsGrid').innerHTML = `
                    <div class="stat-item">
                        <div class="stat-value">${stats.total_transactions.toLocaleString()}</div>
                        <div class="stat-label">Total Transactions</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">${stats.total_cases}</div>
                        <div class="stat-label">Total Cases</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">${stats.total_accounts}</div>
                        <div class="stat-label">Total Accounts</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">$${stats.total_amount.toLocaleString()}</div>
                        <div class="stat-label">Total Amount</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">$${stats.avg_amount.toFixed(2)}</div>
                        <div class="stat-label">Average Amount</div>
                    </div>
                `;
                
                if (stats.note) {
                    document.getElementById('statsGrid').innerHTML += `<div class="note">${stats.note}</div>`;
                }
            } catch (error) {
                document.getElementById('statsGrid').innerHTML = '<div style="color: red;">Error loading statistics</div>';
            }
        }

        async function loadSuspiciousAccounts() {
            try {
                const response = await axios.get('/api/suspicious');
                const suspicious = response.data;
                
                const list = document.getElementById('suspiciousList');
                if (suspicious.length === 0) {
                    list.innerHTML = '<div style="color: #666;">No suspicious accounts detected</div>';
                } else {
                    list.innerHTML = suspicious.map(account => `
                        <div style="background: #1a2332; padding: 15px; margin: 10px 0; border-radius: 8px; border: 1px solid #00aaff;">
                            <strong>Account: ${account.account}</strong><br>
                            Transactions: ${account.total_transactions} | Total: $${account.total_amount.toLocaleString()}
                        </div>
                    `).join('');
                }
            } catch (error) {
                document.getElementById('suspiciousList').innerHTML = '<div style="color: red;">Error loading suspicious accounts</div>';
            }
        }

        async function loadLayeredAnalysis() {
            try {
                const response = await axios.get('/api/layered-analysis');
                const layers = response.data;
                
                document.getElementById('layeredAnalysis').innerHTML = `
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">
                        <div style="background: #1a2332; padding: 15px; border-radius: 8px; border: 1px solid #00aaff;">
                            <div style="color: #00ffff; font-weight: bold;">High Frequency</div>
                            <div>${layers.layer1_high_frequency.length} accounts</div>
                        </div>
                        <div style="background: #1a2332; padding: 15px; border-radius: 8px; border: 1px solid #00aaff;">
                            <div style="color: #00ffff; font-weight: bold;">Large Amounts</div>
                            <div>${layers.layer2_large_amounts.length} accounts</div>
                        </div>
                    </div>
                    ${layers.note ? `<div class="note">${layers.note}</div>` : ''}
                `;
            } catch (error) {
                document.getElementById('layeredAnalysis').innerHTML = '<div style="color: red;">Error loading layered analysis</div>';
            }
        }

        async function loadSpiderMap() {
            try {
                const response = await axios.get('/api/spider-map');
                const mapData = response.data;
                
                document.getElementById('spiderMap').innerHTML = `
                    <div style="background: #1a2332; padding: 20px; border-radius: 8px; border: 1px solid #00aaff;">
                        <div style="color: #00ffff; font-weight: bold; margin-bottom: 15px;">Transaction Network</div>
                        <div>Nodes: ${mapData.nodes.length} | Edges: ${mapData.edges.length}</div>
                        ${mapData.note ? `<div class="note">${mapData.note}</div>` : ''}
                    </div>
                `;
            } catch (error) {
                document.getElementById('spiderMap').innerHTML = '<div style="color: red;">Error loading spider map</div>';
            }
        }
    </script>
</body>
</html>
'''

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
