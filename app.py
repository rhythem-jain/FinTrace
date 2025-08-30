from flask import Flask, request, jsonify, render_template_string, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
import networkx as nx
from collections import defaultdict, deque
import json
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import io
import base64
import re
import os
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
import time
  
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///transactions.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'supersecretkey'  # Needed for session
db = SQLAlchemy(app)

# Remove User model
# -------------------------
# Enhanced Transaction Model
# -------------------------
class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.String(50), index=True)
    transaction_id = db.Column(db.String(50))
    from_account = db.Column(db.String(50), index=True)
    to_account = db.Column(db.String(50), index=True)
    amount = db.Column(db.Float)
    date = db.Column(db.String(20))
    time = db.Column(db.String(10))
    ip = db.Column(db.String(20), index=True)
    phone = db.Column(db.String(20), index=True)
    email = db.Column(db.String(100), index=True)
    transaction_type = db.Column(db.String(20), default='transfer')

# -------------------------
# AML Detection Engine
# -------------------------
class AMLEngine:
    def __init__(self):
        self.suspicious_patterns = []
        self.layered_graphs = {}
        
    def detect_suspicious_accounts(self, df):
        """Detect suspicious accounts using multiple algorithms"""
        suspicious_accounts = set()
        
        # Layer 1: High-frequency transactions
        freq_suspicious = self._detect_high_frequency(df)
        suspicious_accounts.update(freq_suspicious)
        
        # Layer 2: Large amount transactions
        amount_suspicious = self._detect_large_amounts(df)
        suspicious_accounts.update(amount_suspicious)
        
        # Layer 3: Multiple IP/Phone/Email usage
        multi_suspicious = self._detect_multi_identity(df)
        suspicious_accounts.update(multi_suspicious)
        
        # Layer 4: Circular transactions
        circular_suspicious = self._detect_circular_transactions(df)
        suspicious_accounts.update(circular_suspicious)
        
        # Layer 5: Rapid money movement
        rapid_suspicious = self._detect_rapid_movement(df)
        suspicious_accounts.update(rapid_suspicious)
        
        return list(suspicious_accounts)
    
    def _detect_high_frequency(self, df):
        """Detect accounts with unusually high transaction frequency"""
        account_stats = df.groupby('from_account').agg({
            'transaction_id': 'count',
            'amount': ['sum', 'mean'],
            'to_account': 'nunique'
        }).reset_index()
        
        account_stats.columns = ['account', 'txn_count', 'total_amount', 'avg_amount', 'unique_recipients']
        
        # Detect outliers using IQR method
        Q1 = account_stats['txn_count'].quantile(0.25)
        Q3 = account_stats['txn_count'].quantile(0.75)
        IQR = Q3 - Q1
        high_freq_threshold = Q3 + 1.5 * IQR
        
        suspicious = account_stats[account_stats['txn_count'] > high_freq_threshold]['account'].tolist()
        return suspicious
    
    def _detect_large_amounts(self, df):
        """Detect accounts with unusually large transaction amounts"""
        # Calculate amount percentiles
        amount_95th = df['amount'].quantile(0.95)
        amount_99th = df['amount'].quantile(0.99)
        
        # Accounts with transactions above 99th percentile
        large_amount_accounts = df[df['amount'] > amount_99th]['from_account'].unique().tolist()
        
        return large_amount_accounts
    
    def _detect_multi_identity(self, df):
        """Detect accounts using multiple IPs, phones, or emails"""
        suspicious_accounts = set()
        
        # Check for accounts with multiple IPs
        multi_ip = df.groupby('from_account')['ip'].nunique()
        multi_ip_suspicious = multi_ip[multi_ip > 3].index.tolist()
        suspicious_accounts.update(multi_ip_suspicious)
        
        # Check for accounts with multiple phones
        multi_phone = df.groupby('from_account')['phone'].nunique()
        multi_phone_suspicious = multi_phone[multi_phone > 2].index.tolist()
        suspicious_accounts.update(multi_phone_suspicious)
        
        # Check for accounts with multiple emails
        multi_email = df.groupby('from_account')['email'].nunique()
        multi_email_suspicious = multi_email[multi_email > 2].index.tolist()
        suspicious_accounts.update(multi_email_suspicious)
        
        return suspicious_accounts
    
    def _detect_circular_transactions(self, df):
        """Detect circular transaction patterns"""
        suspicious_accounts = set()
        
        # Create directed graph
        G = nx.DiGraph()
        for _, row in df.iterrows():
            G.add_edge(row['from_account'], row['to_account'], weight=row['amount'])
        
        # Find cycles in the graph
        try:
            cycles = list(nx.simple_cycles(G))
            for cycle in cycles:
                if len(cycle) <= 5:  # Focus on short cycles
                    suspicious_accounts.update(cycle)
        except:
            pass
        
        return suspicious_accounts
    
    def _detect_rapid_movement(self, df):
        """Detect rapid money movement patterns"""
        suspicious_accounts = set()
        
        # Group by account and date
        df['datetime'] = pd.to_datetime(df['date'] + ' ' + df['time'])
        account_daily = df.groupby(['from_account', 'date']).agg({
            'amount': 'sum',
            'transaction_id': 'count'
        }).reset_index()
        
        # Find accounts with high daily transaction volumes
        high_volume = account_daily[account_daily['amount'] > account_daily['amount'].quantile(0.95)]
        suspicious_accounts.update(high_volume['from_account'].unique().tolist())
        
        return suspicious_accounts
    
    def build_layered_graph(self, df, case_id=None):
        """Build layered transaction graph"""
        if case_id:
            df = df[df['case_id'] == case_id]
        
        G = nx.DiGraph()
        
        # Add nodes and edges
        for _, row in df.iterrows():
            G.add_node(row['from_account'], 
                      account_type='source',
                      ip=row['ip'],
                      phone=row['phone'],
                      email=row['email'])
            G.add_node(row['to_account'], 
                      account_type='destination',
                      ip=row['ip'],
                      phone=row['phone'],
                      email=row['email'])
            G.add_edge(row['from_account'], row['to_account'], 
                      weight=row['amount'],
                      date=row['date'],
                      time=row['time'],
                      transaction_id=row['transaction_id'])
        
        return G
    
    def find_money_trail(self, df, start_account, max_depth=3):
        """Find money trail from a specific account"""
        G = self.build_layered_graph(df)
        
        if start_account not in G.nodes():
            return []
        
        trails = []
        visited = set()
        
        def dfs_trail(node, path, depth):
            if depth > max_depth or node in visited:
                return
            
            visited.add(node)
            path.append(node)
            
            if depth == max_depth:
                trails.append(path.copy())
            else:
                for neighbor in G.successors(node):
                    dfs_trail(neighbor, path, depth + 1)
            
            path.pop()
            visited.remove(node)
        
        dfs_trail(start_account, [], 0)
        return trails

def is_valid_number(val):
    try:
        if val is None or pd.isna(val):
            return False
        float(str(val).replace(',', ''))
        return True
    except Exception:
        return False

# -------------------------
# Load Data from CSV on First Request
# -------------------------
@app.before_request
def load_data():
    if Transaction.query.count() == 0:
        print("Loading transaction data from Excel...")
        df = pd.read_excel('../archive/bank.xlsx')
        txn_id = 1
        for _, row in df.iterrows():
            deposit_amt = row.get('DEPOSIT AMT')
            withdrawal_amt = row.get('WITHDRAWAL AMT')
            amount = None
            transaction_type = None
            if is_valid_number(deposit_amt) and float(str(deposit_amt).replace(',', '')) != 0.0:
                amount = float(str(deposit_amt).replace(',', ''))
                transaction_type = 'deposit'
            elif is_valid_number(withdrawal_amt) and float(str(withdrawal_amt).replace(',', '')) != 0.0:
                amount = -float(str(withdrawal_amt).replace(',', ''))
                transaction_type = 'withdrawal'
            else:
                continue  # skip rows with no amount
            from_account = str(row.get('Account No', ''))
            details = str(row.get('TRANSACTION DETAILS', ''))
            to_account = 'UNKNOWN'
            match = re.search(r'\b\d{9,}\b', details)
            if match:
                to_account = match.group(0)
            txn = Transaction(
                **{
                    'case_id': 'CASE001',
                    'transaction_id': f'TXN{txn_id:06d}',
                    'from_account': from_account,
                    'to_account': to_account,
                    'amount': amount,
                    'date': str(row.get('VALUE DATE', '')),
                    'time': '12:00:00',
                    'ip': '192.168.1.1',
                    'phone': '+1234567890',
                    'email': 'user@example.com',
                    'transaction_type': 'transfer'
                }
            )
            db.session.add(txn)
            txn_id += 1
        db.session.commit()
        print(f"Loaded {txn_id-1} transactions from Excel")

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user'):
            return redirect(url_for('get_started'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def root():
    return redirect(url_for('get_started'))

@app.route('/dashboard')
def dashboard():
    return render_template_string(HTML_TEMPLATE)

# API route decorator (no login required)
def protected_api_route(rule, **options):
    def decorator(f):
        endpoint = options.pop('endpoint', None)
        app.route(rule, **options, endpoint=endpoint)(f)
        return f
    return decorator

def get_data():
    if 'uploaded_data_file' in session:
        try:
            return pd.read_csv(session['uploaded_data_file'])
        except Exception:
            pass  # fallback to DB if file missing/corrupt
    return pd.read_sql_table('transaction', db.engine)

@protected_api_route('/api/suspicious')
def suspicious_accounts():
    try:
        df = get_data()
        # Clean data: drop rows with missing critical columns
        df = df.dropna(subset=['from_account', 'to_account', 'amount', 'date'], how='any')
        if df.empty:
            return jsonify([])
        aml_engine = AMLEngine()
        suspicious = aml_engine.detect_suspicious_accounts(df)
        suspicious_details = []
        for account in suspicious:
            account_rows = df[df['from_account'] == account]
            if account_rows.empty:
                continue
            account_data = account_rows.iloc[0]
            suspicious_details.append({
                'account': account,
                'ip': account_data.get('ip', ''),
                'phone': account_data.get('phone', ''),
                'email': account_data.get('email', ''),
                'total_transactions': len(account_rows),
                'total_amount': account_rows['amount'].sum()
            })
        return jsonify(suspicious_details)
    except Exception as e:
        print(f"Error in suspicious_accounts: {e}")
        return jsonify([])

@protected_api_route('/api/layered-analysis')
def layered_analysis():
    try:
        df = get_data()
        # Clean data: drop rows with missing critical columns
        df = df.dropna(subset=['from_account', 'to_account', 'amount', 'date'], how='any')
        if df.empty:
            return jsonify({
                'layer1_high_frequency': [],
                'layer2_large_amounts': [],
                'layer3_multi_identity': [],
                'layer4_circular': [],
                'layer5_rapid_movement': []
            })
        aml_engine = AMLEngine()
        freq_suspicious = aml_engine._detect_high_frequency(df)
        amount_suspicious = aml_engine._detect_large_amounts(df)
        multi_suspicious = aml_engine._detect_multi_identity(df)
        circular_suspicious = aml_engine._detect_circular_transactions(df)
        rapid_suspicious = aml_engine._detect_rapid_movement(df)
        return jsonify({
            'layer1_high_frequency': freq_suspicious,
            'layer2_large_amounts': amount_suspicious,
            'layer3_multi_identity': list(multi_suspicious),
            'layer4_circular': list(circular_suspicious),
            'layer5_rapid_movement': list(rapid_suspicious)
        })
    except Exception as e:
        print(f"Error in layered_analysis: {e}")
        return jsonify({
            'layer1_high_frequency': [],
            'layer2_large_amounts': [],
            'layer3_multi_identity': [],
            'layer4_circular': [],
            'layer5_rapid_movement': []
        })

@protected_api_route('/api/spider-map')
def spider_map():
    """Get spider map data for visualization with enhanced interpretation"""
    try:
        df = get_data()
        # Filter out transactions with UNKNOWN from_account or to_account
        df = df[(df['from_account'] != 'UNKNOWN') & (df['to_account'] != 'UNKNOWN')]
        
        if len(df) == 0:
            return jsonify({'nodes': [], 'edges': [], 'error': 'No valid transactions to display.'})
        
        aml_engine = AMLEngine()
        df_sample = df.head(500)  # Limit for better performance
        G = aml_engine.build_layered_graph(df_sample)

        if len(G) == 0:
            return jsonify({'nodes': [], 'edges': [], 'error': 'No valid transactions to display.'})

        # Calculate node metrics for interpretation
        node_metrics = {}
        for node in G.nodes():
            in_degree = len(list(G.in_edges(node)))
            out_degree = len(list(G.out_edges(node)))
            total_degree = in_degree + out_degree
            
            # Calculate total money flow through this node
            in_amount = sum(data.get('weight', 0) for _, _, data in G.in_edges(node, data=True))
            out_amount = sum(data.get('weight', 0) for _, _, data in G.out_edges(node, data=True))
            
            node_metrics[node] = {
                'in_degree': in_degree,
                'out_degree': out_degree,
                'total_degree': total_degree,
                'in_amount': in_amount,
                'out_amount': out_amount,
                'net_flow': out_amount - in_amount
            }

        # Build node and edge lists for Cytoscape with enhanced data
        nodes = []
        for node in G.nodes():
            node_data = G.nodes[node]
            metrics = node_metrics[node]
            
            # Determine node type for visualization
            node_type = 'normal'
            if metrics['total_degree'] > 5:
                node_type = 'hub'
            elif metrics['out_amount'] > 10000:
                node_type = 'high_value'
            elif metrics['in_degree'] == 0:
                node_type = 'source'
            elif metrics['out_degree'] == 0:
                node_type = 'sink'
            
            nodes.append({
                'data': {
                    'id': str(node),
                    'account_type': node_data.get('account_type', 'unknown'),
                    'node_type': node_type,
                    'ip': str(node_data.get('ip', '')),
                    'phone': str(node_data.get('phone', '')),
                    'email': str(node_data.get('email', '')),
                    'in_degree': metrics['in_degree'],
                    'out_degree': metrics['out_degree'],
                    'total_degree': metrics['total_degree'],
                    'in_amount': metrics['in_amount'],
                    'out_amount': metrics['out_amount'],
                    'net_flow': metrics['net_flow']
                }
            })

        edges = []
        for source, target, data in G.edges(data=True):
            edges.append({
                'data': {
                    'source': str(source),
                    'target': str(target),
                    'weight': float(data.get('weight', 0)),
                    'date': str(data.get('date', '')),
                    'time': str(data.get('time', '')),
                    'transaction_id': str(data.get('transaction_id', ''))
                }
            })

        # Calculate graph statistics for interpretation
        total_nodes = len(nodes)
        total_edges = len(edges)
        total_amount = sum(edge['data']['weight'] for edge in edges)
        
        # Find suspicious patterns
        suspicious_nodes = []
        for node in nodes:
            node_data = node['data']
            if (node_data['total_degree'] > 8 or 
                node_data['out_amount'] > 50000 or 
                node_data['in_degree'] == 0 and node_data['out_degree'] > 3):
                suspicious_nodes.append(node_data['id'])

        return jsonify({
            'nodes': nodes, 
            'edges': edges,
            'statistics': {
                'total_nodes': total_nodes,
                'total_edges': total_edges,
                'total_amount': total_amount,
                'suspicious_nodes': suspicious_nodes
            }
        })
    except Exception as e:
        print(f"Error in spider_map endpoint: {e}")
        return jsonify({'nodes': [], 'edges': [], 'error': str(e)})

@protected_api_route('/api/money-trail/<account>')
def money_trail(account):
    """Find money trail from a specific account"""
    df = get_data()
    aml_engine = AMLEngine()
    trails = aml_engine.find_money_trail(df, account, max_depth=3)
    
    return jsonify({
        'account': account,
        'trails': trails,
        'trail_count': len(trails)
    })

@protected_api_route('/api/filter', methods=['POST'])
def filter_transactions():
    """Enhanced filtering with multiple criteria"""
    data = request.get_json()
    df = get_data()
    case_id = data.get('case_id')
    ip = data.get('ip')
    phone = data.get('phone')
    email = data.get('email')
    account = data.get('account')
    min_amount = data.get('min_amount')
    max_amount = data.get('max_amount')
    date_from = data.get('date_from')
    date_to = data.get('date_to')
    
    # Use DataFrame filtering instead of SQLAlchemy
    if case_id:
        df = df[df['case_id'] == case_id]
    if ip:
        df = df[df['ip'] == ip]
    if phone:
        df = df[df['phone'] == phone]
    if email:
        df = df[df['email'] == email]
    if account:
        df = df[(df['from_account'] == account) | (df['to_account'] == account)]
    if min_amount:
        df = df[df['amount'] >= float(min_amount)]
    if max_amount:
        df = df[df['amount'] <= float(max_amount)]
    if date_from:
        df = df[df['date'] >= date_from]
    if date_to:
        df = df[df['date'] <= date_to]
    
    results = df.to_dict(orient='records')
    return jsonify(results)

@protected_api_route('/api/cases')
def get_cases():
    """Get all unique cases"""
    df = get_data()
    cases = df['case_id'].unique().tolist()
    return jsonify(cases)

@protected_api_route('/api/statistics')
def get_statistics():
    """Get overall statistics"""
    df = get_data()
    
    stats = {
        'total_transactions': len(df),
        'total_cases': df['case_id'].nunique(),
        'total_accounts': len(set(df['from_account'].tolist() + df['to_account'].tolist())),
        'total_amount': df['amount'].sum(),
        'avg_amount': df['amount'].mean(),
        'unique_ips': df['ip'].nunique(),
        'unique_phones': df['phone'].nunique(),
        'unique_emails': df['email'].nunique()
    }
    
    return jsonify(stats)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    file = request.files['file']
    if not file or not file.filename:
        return jsonify({'error': 'No selected file'}), 400
    filename = file.filename
    if not isinstance(filename, str):
        return jsonify({'error': 'Invalid filename'}), 400
    filepath = os.path.join('instance', filename)
    file.save(filepath)
    try:
        if filename.lower().endswith('.csv'):
            df = pd.read_csv(filepath)
        elif filename.lower().endswith('.xlsx'):
            df = pd.read_excel(filepath)
        else:
            return jsonify({'error': 'Unsupported file type'}), 400
        # Ensure all required columns exist
        required_cols = [
            'transaction_id', 'date', 'from_account', 'to_account', 'amount', 'transaction_type',
            'ip', 'phone', 'email', 'case_id', 'time'
        ]
        for col in required_cols:
            if col not in df.columns:
                if col == 'case_id':
                    df[col] = 'UPLOADED'
                elif col == 'time':
                    df[col] = '12:00:00'
                else:
                    df[col] = ''
    except Exception as e:
        return jsonify({'error': f'Failed to read file: {str(e)}'}), 400
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    if not numeric_cols:
        return jsonify({'error': 'No numeric columns found for anomaly detection.'}), 400
    X = df[numeric_cols].dropna()
    if len(X) < 10:
        return jsonify({'error': 'Not enough data for anomaly detection.'}), 400
    model = IsolationForest(n_estimators=100, contamination='auto', random_state=42)
    model.fit(X)
    scores = model.decision_function(X)
    anomalies = model.predict(X)
    df_anom = df.loc[X.index].copy()
    df_anom['anomaly_score'] = -scores
    df_anom['is_anomaly'] = (anomalies == -1)
    top_anomalies = df_anom[df_anom['is_anomaly']].sort_values('anomaly_score', ascending=False).head(10)
    # Save uploaded data as temp CSV and store filename in session
    temp_filename = os.path.join('instance', f"uploaded_{uuid.uuid4().hex}_{int(time.time())}.csv")
    df.to_csv(temp_filename, index=False)
    session['uploaded_data_file'] = temp_filename
    result = top_anomalies.to_dict(orient='records')
    return jsonify({'message': f'File {filename} uploaded and model trained! Top anomalies below.', 'anomalies': result})

# -------------------------
# HTML Template for Enhanced UI
# -------------------------
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>FinTrace - AML Detection Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/axios/dist/axios.min.js"></script>
    <script src="https://unpkg.com/cytoscape@3.24.0/dist/cytoscape.min.js"></script>
    <script src="https://unpkg.com/cytoscape-cose-bilkent@4.1.0/cytoscape-cose-bilkent.js"></script>
    <script>
      // Register the cose-bilkent layout extension before any Cytoscape code runs
      if (typeof cytoscape !== 'undefined' && typeof window !== 'undefined' && window.cytoscapeCoseBilkent) {
        cytoscape.use(window.cytoscapeCoseBilkent);
      }
    </script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #0f1419;
            min-height: 100vh;
            color: #ffffff;
            overflow-x: hidden;
            position: relative;
        }
        
        body::before {
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: 
                radial-gradient(circle at 20% 20%, rgba(0, 170, 255, 0.08) 0%, transparent 50%),
                radial-gradient(circle at 80% 80%, rgba(0, 255, 255, 0.06) 0%, transparent 50%);
            pointer-events: none;
            z-index: -1;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }
        
        /* Mobile-first container adjustments */
        @media (max-width: 768px) {
            .container {
                max-width: 100%;
                padding: 15px;
            }
            
            /* Fix mobile scrolling issues */
            body {
                overflow-y: auto;
                -webkit-overflow-scrolling: touch;
                position: relative;
            }
            
            html {
                overflow-y: auto;
                -webkit-overflow-scrolling: touch;
            }
        }
        /* Header Section */
        .header {
            text-align: center;
            padding: 40px 0 30px;
            color: white;
            position: relative;
        }
        
        .header h1 {
            font-size: 3.5rem;
            font-weight: 700;
            margin-bottom: 15px;
            color: #00aaff;
            text-shadow: 0 0 10px rgba(0, 170, 255, 0.4);
        }
        
        .header .subtitle {
            font-size: 1.4rem;
            margin-bottom: 20px;
            color: #00ffff;
            font-weight: 500;
        }
        
        .header .description {
            font-size: 1.1rem;
            max-width: 800px;
            margin: 0 auto;
            line-height: 1.6;
            color: #b0b8c9;
        }
        .dashboard {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            margin-bottom: 30px;
        }
        
        /* Mobile dashboard layout */
        @media (max-width: 768px) {
            .dashboard {
                grid-template-columns: 1fr;
                gap: 20px;
                margin-bottom: 20px;
            }
        }
        
        /* Cool Dark Theme Animations */
        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        @keyframes slideInLeft {
            from {
                opacity: 0;
                transform: translateX(-30px);
            }
            to {
                opacity: 1;
                transform: translateX(0);
            }
        }
        
        @keyframes slideInRight {
            from {
                opacity: 0;
                transform: translateX(30px);
            }
            to {
                opacity: 1;
                transform: translateX(0);
            }
        }
        
        @keyframes pulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.05); }
        }
        
        .card {
            animation: fadeInUp 0.6s ease forwards;
            opacity: 0;
        }
        
        .card:nth-child(1) { animation-delay: 0.1s; }
        .card:nth-child(2) { animation-delay: 0.2s; }
        .card:nth-child(3) { animation-delay: 0.3s; }
        .card:nth-child(4) { animation-delay: 0.4s; }
        .card:nth-child(5) { animation-delay: 0.5s; }
        .card:nth-child(6) { animation-delay: 0.6s; }
        
        .stat-item:nth-child(1) { animation: slideInLeft 0.6s ease forwards; opacity: 0; }
        .stat-item:nth-child(2) { animation: slideInRight 0.6s ease forwards; opacity: 0; }
        .stat-item:nth-child(3) { animation: slideInLeft 0.6s ease forwards; opacity: 0; }
        .stat-item:nth-child(4) { animation: slideInRight 0.6s ease forwards; opacity: 0; }
        .stat-item:nth-child(5) { animation: slideInLeft 0.6s ease forwards; opacity: 0; }
        .stat-item:nth-child(6) { animation: slideInRight 0.6s ease forwards; opacity: 0; }
        
        .btn:hover {
            animation: pulse 1s ease-in-out infinite;
        }
        .card {
            background: rgba(15, 20, 25, 0.95);
            border-radius: 15px;
            padding: 30px 25px;
            text-align: center;
            box-shadow: 0 8px 25px rgba(0,0,0,0.3), 0 0 0 1px rgba(0, 170, 255, 0.3);
            transition: all 0.3s ease;
            border: 2px solid #00aaff;
            position: relative;
            overflow: hidden;
            margin-bottom: 20px;
        }
        
        .card:hover {
            transform: translateY(-5px);
            border-color: #00aaff;
            box-shadow: 0 0 20px rgba(0, 170, 255, 0.2);
        }
        
        .card h3 {
            font-size: 2rem;
            margin-bottom: 25px;
            margin-top: -10px;
            color: #00ffff;
            font-weight: 600;
            line-height: 1.2;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        .stat-item {
            text-align: center;
            color: white;
            background: rgba(15, 20, 25, 0.9);
            border-radius: 12px;
            padding: 20px 15px;
            border: 2px solid #00aaff;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2), 0 0 0 1px rgba(0, 170, 255, 0.2);
            min-height: 100px;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }
        
        .stat-item:hover {
            transform: translateY(-3px);
            border-color: #00aaff;
            box-shadow: 0 0 15px rgba(0, 170, 255, 0.2);
        }
        
        .stat-value {
            font-size: 1.8rem;
            font-weight: 600;
            margin-bottom: 8px;
            margin-top: -2px;
            color: #00aaff;
            line-height: 1.1;
        }
        
        .stat-label {
            font-size: 1rem;
            font-weight: 500;
            color: #b0b8c9;
            line-height: 1.2;
        }
        .filter-section {
            background: rgba(15, 20, 25, 0.95);
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 30px;
            box-shadow: 0 8px 25px rgba(0,0,0,0.3), 0 0 0 1px rgba(0, 170, 255, 0.3);
            border: 2px solid #00aaff;
        }
        
        .filter-section h3 {
            margin-top: -10px;
            margin-bottom: 25px;
            line-height: 1.2;
            color: #00ffff;
            font-size: 2rem;
        }
        .filter-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }
        .filter-input {
            padding: 12px 15px;
            border: 1px solid #2a3441;
            background: #1a2332;
            color: #ffffff;
            border-radius: 8px;
            font-size: 14px;
            transition: all 0.3s ease;
        }
        .filter-input:focus {
            outline: none;
            border-color: #00aaff;
            background: #232b3a;
            box-shadow: 0 0 0 2px rgba(0, 170, 255, 0.2);
        }
        .btn {
            display: inline-block;
            background: linear-gradient(45deg, #00aaff, #00ffff);
            color: #000;
            padding: 12px 25px;
            border-radius: 8px;
            text-decoration: none;
            font-size: 14px;
            font-weight: 600;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(0, 170, 255, 0.2);
            border: none;
            cursor: pointer;
            text-align: center;
            margin: 0 5px;
        }
        
        /* Button container for proper spacing */
        .btn-container {
            display: flex;
            flex-wrap: wrap;
            gap: 15px;
            justify-content: center;
            align-items: center;
            margin: 20px 0;
        }
        
        /* Mobile button optimizations */
        @media (max-width: 768px) {
            .btn-container {
                flex-direction: column;
                gap: 12px;
                margin: 15px 0;
            }
            
            .btn {
                margin: 0;
                width: 100%;
                max-width: 250px;
                padding: 12px 20px;
            }
            
            /* Specific spacing for different button groups */
            #map-controls.btn-container {
                margin-top: 20px;
                gap: 15px;
            }
        }
        
        @media (max-width: 480px) {
            .btn-container {
                gap: 10px;
                margin: 12px 0;
            }
            
            .btn {
                max-width: 220px;
                padding: 10px 18px;
            }
            
            #map-controls.btn-container {
                margin-top: 15px;
                gap: 12px;
            }
        }
        
        @media (max-width: 360px) {
            /* Fix mobile scrolling for small screens */
            html, body {
                overflow-y: auto;
                -webkit-overflow-scrolling: touch;
                height: auto;
            }
            
            .btn-container {
                gap: 8px;
                margin: 10px 0;
            }
            
            .btn {
                max-width: 200px;
                padding: 8px 16px;
            }
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(0, 170, 255, 0.3);
            background: linear-gradient(45deg, #00ffff, #00aaff);
        }
        .graph-container {
            background: rgba(15, 20, 25, 0.95);
            border-radius: 15px;
            padding: 25px;
            margin-top: 10px;
            box-shadow: 0 8px 25px rgba(0,0,0,0.3), 0 0 0 1px rgba(0, 170, 255, 0.3);
            border: 2px solid #00aaff;
        }
        
        .graph-container h3 {
            margin-top: -10px;
            margin-bottom: 20px;
            line-height: 1.2;
            color: #00ffff;
            font-size: 2rem;
        }
        #spider-map {
            width: 100%;
            height: 600px;
            border: 1px solid #2a3441;
            border-radius: 10px;
            background: #1a2332;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        }
        .suspicious-list {
            max-height: 300px;
            overflow-y: auto;
        }
        .suspicious-item {
            background: #1a2332;
            border: 2px solid #00aaff;
            border-radius: 8px;
            padding: 12px;
            margin-bottom: 8px;
            color: #00ffff;
            box-shadow: 0 2px 8px rgba(0, 170, 255, 0.1), 0 0 0 1px rgba(0, 170, 255, 0.2);
        }
        .suspicious-item:hover {
            background: #232b3a;
            border-color: #00ffff;
            color: #ffffff;
        }
        .layered-analysis {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
        }
        .layer-card {
            background: #1a2332;
            border-radius: 10px;
            padding: 15px;
            border: 2px solid #00aaff;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2), 0 0 0 1px rgba(0, 170, 255, 0.2);
        }
        .layer-title {
            font-weight: 600;
            color: #00ffff;
            margin-bottom: 10px;
            margin-top: -2px;
            line-height: 1.2;
        }
        .layer-accounts {
            font-size: 0.9em;
            color: #b0b8c9;
        }
        .loading {
            text-align: center;
            padding: 20px;
            color: #b0b8c9;
        }
        /* Loading indicator (GIF + CSS fallback) */
        .loader {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
            padding: 16px;
        }
        .loader img.loader-gif {
            height: 24px;
            width: 24px;
            image-rendering: -webkit-optimize-contrast;
        }
        .spinner-fallback {
            display: inline-block;
            width: 24px;
            height: 24px;
            border: 2px solid rgba(0, 170, 255, 0.2);
            border-top-color: #00aaff;
            border-radius: 50%;
            animation: spin 0.9s linear infinite;
        }
        @keyframes spin { to { transform: rotate(360deg); } }
        .error {
            background: #2a1a1a;
            color: #ff6b6b;
            padding: 12px;
            border-radius: 8px;
            margin: 10px 0;
            border: 1px solid #ff6b6b;
            box-shadow: 0 2px 8px rgba(255, 107, 107, 0.2);
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- Header Section -->
        <div class="header">
            <h1>🚨 FinTrace</h1>
            <div class="subtitle">Advanced Money Laundering Detection with Multi-Layer Analysis</div>
            <div class="description">
                Detecting sophisticated money laundering patterns, analyzing complex transaction networks, and providing actionable insights.
            </div>
        </div>

        <!-- File Upload Card -->
        <div class="card">
          <h3>📁 Upload Transaction Dataset</h3>
          <form id="uploadForm" enctype="multipart/form-data">
            <input type="file" id="fileInput" name="file" accept=".csv,.xlsx" required>
            <div class="btn-container">
                <button type="submit" class="btn">Upload & Train</button>
            </div>
          </form>
          <div id="uploadStatus"></div>
        </div>

        <!-- Statistics Dashboard -->
        <div class="dashboard">
            <div class="card">
                <h3>📊 System Statistics</h3>
                <div class="stats-grid" id="statsGrid">
                    <div class="loading">
                    <div class="loader">
                        <img class="loader-gif" src="/static/loading.gif" alt="Loading" onerror="this.style.display='none'; this.nextElementSibling.style.display='inline-block';">
                        <span class="spinner-fallback" style="display:none"></span>
                        <span>Loading statistics...</span>
                    </div>
                </div>
                </div>
            </div>
            
            <div class="card">
                <h3>🔍 Suspicious Accounts</h3>
                <div class="suspicious-list" id="suspiciousList">
                    <div class="loading">
                    <div class="loader">
                        <img class="loader-gif" src="/static/loading.gif" alt="Loading" onerror="this.style.display='none'; this.nextElementSibling.style.display='inline-block';">
                        <span class="spinner-fallback" style="display:none"></span>
                        <span>Loading suspicious accounts...</span>
                    </div>
                </div>
                </div>
            </div>
        </div>

        <!-- Layered Analysis -->
        <div class="card">
            <h3>🔬 Layered Analysis Results</h3>
            <div class="layered-analysis" id="layeredAnalysis">
                <div class="loading">
                    <div class="loader">
                        <img class="loader-gif" src="/static/loading.gif" alt="Loading" onerror="this.style.display='none'; this.nextElementSibling.style.display='inline-block';">
                        <span class="spinner-fallback" style="display:none"></span>
                        <span>Loading layered analysis...</span>
                    </div>
                </div>
            </div>
        </div>

        <!-- Advanced Filtering -->
        <div class="filter-section">
            <h3>🔍 Advanced Filtering</h3>
            <div class="filter-grid">
                <input type="text" id="caseId" class="filter-input" placeholder="Case ID">
                <input type="text" id="account" class="filter-input" placeholder="Account Number">
                <input type="text" id="ip" class="filter-input" placeholder="IP Address">
                <input type="text" id="phone" class="filter-input" placeholder="Phone Number">
                <input type="text" id="email" class="filter-input" placeholder="Email">
                <input type="number" id="minAmount" class="filter-input" placeholder="Min Amount">
                <input type="number" id="maxAmount" class="filter-input" placeholder="Max Amount">
                <input type="date" id="dateFrom" class="filter-input" placeholder="Date From">
                <input type="date" id="dateTo" class="filter-input" placeholder="Date To">
            </div>
            <div class="btn-container">
                <button onclick="filterTransactions()" class="btn">🔍 Filter Transactions</button>
                <button onclick="findMoneyTrail()" class="btn">💰 Find Money Trail</button>
            </div>
            <div id="filterOutput" style="margin-top: 20px;"></div>
        </div>

        <!-- Spider Map -->
        <div class="graph-container">
            <h3>🕷️ Spider Map - Transaction Network</h3>
            <div id="spider-map-status" style="text-align: center; padding: 10px; background: rgba(15, 20, 25, 0.8); border-radius: 8px; margin-bottom: 10px; border: 1px solid #1a2332;">
                <span id="map-status" style="color: #ffffff; font-weight: 500;">
                    <span class="loader" style="gap:8px; padding: 6px 0;">
                        <img class="loader-gif" src="/static/loading.gif" alt="Loading" onerror="this.style.display='none'; this.nextElementSibling.style.display='inline-block';">
                        <span class="spinner-fallback" style="display:none"></span>
                        Loading spider map...
                    </span>
                </span>
            </div>
            <div id="spider-map"></div>
            <div class="btn-container" id="map-controls" style="margin-top: 15px;">
                <button onclick="resetMapView()" class="btn">🔄 Reset View</button>
                <button onclick="fitMapToScreen()" class="btn">📐 Fit to Screen</button>
                <button onclick="toggleMapLabels()" class="btn">🏷️ Toggle Labels</button>
            </div>
        </div>
    </div>

    <script>
        // Load all data on page load
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
                
                const statsGrid = document.getElementById('statsGrid');
                statsGrid.innerHTML = `
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
                    <div class="stat-item">
                        <div class="stat-value">${stats.unique_ips}</div>
                        <div class="stat-label">Unique IPs</div>
                    </div>
                `;
            } catch (error) {
                console.error('Error loading statistics:', error);
                document.getElementById('statsGrid').innerHTML = '<div class="error">Error loading statistics</div>';
            }
        }

        async function loadSuspiciousAccounts() {
            try {
                const response = await axios.get('/api/suspicious');
                const suspicious = response.data;
                
                const list = document.getElementById('suspiciousList');
                if (suspicious.length === 0) {
                    list.innerHTML = '<div style="color: #666; text-align: center; padding: 20px;">No suspicious accounts detected</div>';
                } else {
                    list.innerHTML = suspicious.map(account => `
                        <div class="suspicious-item">
                            <strong>Account: ${account.account}</strong><br>
                            IP: ${account.ip} | Phone: ${account.phone}<br>
                            Email: ${account.email}<br>
                            Transactions: ${account.total_transactions} | Total: $${account.total_amount.toLocaleString()}
                        </div>
                    `).join('');
                }
            } catch (error) {
                console.error('Error loading suspicious accounts:', error);
                document.getElementById('suspiciousList').innerHTML = '<div class="error">Error loading suspicious accounts</div>';
            }
        }

        async function loadLayeredAnalysis() {
            try {
                const response = await axios.get('/api/layered-analysis');
                const layers = response.data;
                
                const analysisDiv = document.getElementById('layeredAnalysis');
                analysisDiv.innerHTML = `
                    <div class="layer-card">
                        <div class="layer-title">🔴 Layer 1: High Frequency</div>
                        <div class="layer-accounts">${layers.layer1_high_frequency.length} accounts</div>
                    </div>
                    <div class="layer-card">
                        <div class="layer-title">🟡 Layer 2: Large Amounts</div>
                        <div class="layer-accounts">${layers.layer2_large_amounts.length} accounts</div>
                    </div>
                    <div class="layer-card">
                        <div class="layer-title">🟢 Layer 3: Multi-Identity</div>
                        <div class="layer-accounts">${layers.layer3_multi_identity.length} accounts</div>
                    </div>
                    <div class="layer-card">
                        <div class="layer-title">🔵 Layer 4: Circular</div>
                        <div class="layer-accounts">${layers.layer4_circular.length} accounts</div>
                    </div>
                    <div class="layer-card">
                        <div class="layer-title">🟣 Layer 5: Rapid Movement</div>
                        <div class="layer-accounts">${layers.layer5_rapid_movement.length} accounts</div>
                    </div>
                `;
            } catch (error) {
                console.error('Error loading layered analysis:', error);
                document.getElementById('layeredAnalysis').innerHTML = '<div class="error">Error loading layered analysis</div>';
            }
        }

        async function loadSpiderMap() {
            try {
                const response = await axios.get('/api/spider-map');
                const graphData = response.data;
                
                // Check if we have valid data
                if (!graphData.nodes || !graphData.edges || graphData.nodes.length === 0) {
                    document.getElementById('spider-map').innerHTML = '<div style="text-align: center; padding: 40px; color: #666;">No transaction data available for visualization</div>';
                    return;
                }
                
                // Add interpretation panel
                const interpretationDiv = document.createElement('div');
                interpretationDiv.innerHTML = `
                    <div style="background: #232b3a; color: #f5f7fa; padding: 15px; border-radius: 8px; margin-bottom: 15px; font-size: 1.08em; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;">
                        <h4 style='color: #7ed6ff; margin-bottom: 10px;'>📊 Spider Map Interpretation Guide</h4>
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px; margin-top: 10px;">
                            <div style="background: #2a2f4a; color: #ff7675; padding: 10px; border-radius: 5px; font-weight: 600;">🔴 Red Nodes: <span style='color:#fff;'>High-activity accounts (hubs)</span></div>
                            <div style="background: #2a2f4a; color: #ffe082; padding: 10px; border-radius: 5px; font-weight: 600;">🟡 Yellow Nodes: <span style='color:#fff;'>High-value transactions</span></div>
                            <div style="background: #2a2f4a; color: #55efc4; padding: 10px; border-radius: 5px; font-weight: 600;">🟢 Green Nodes: <span style='color:#fff;'>Source accounts (money origin)</span></div>
                            <div style="background: #2a2f4a; color: #a29bfe; padding: 10px; border-radius: 5px; font-weight: 600;">🟣 Purple Nodes: <span style='color:#fff;'>Sink accounts (money destination)</span></div>
                        </div>
                        ${graphData.statistics ? `
                        <div style="margin-top: 10px; padding: 12px; background: #101624; color: #7ed6ff; border-radius: 5px; font-size: 1.05em;">
                            <strong style='color:#7ed6ff;'>📈 Network Statistics:</strong><br>
                            <span style='color:#f5f7fa;'>• Total Accounts: <b>${graphData.statistics.total_nodes}</b></span><br>
                            <span style='color:#f5f7fa;'>• Total Transactions: <b>${graphData.statistics.total_edges}</b></span><br>
                            <span style='color:#f5f7fa;'>• Total Amount: <b>$${graphData.statistics.total_amount.toLocaleString()}</b></span><br>
                            <span style='color:#ffe082;'>• Suspicious Nodes: <b>${graphData.statistics.suspicious_nodes.length}</b></span>
                        </div>
                        ` : ''}
                    </div>
                `;
                document.getElementById('spider-map').parentNode.insertBefore(interpretationDiv, document.getElementById('spider-map'));
                
                // Check if cytoscape is available
                if (typeof cytoscape === 'undefined') {
                    document.getElementById('spider-map').innerHTML = '<div style="text-align: center; padding: 40px; color: #666;">Cytoscape library not loaded. Showing data summary instead.<br><br>Nodes: ' + graphData.nodes.length + '<br>Edges: ' + graphData.edges.length + '</div>';
                    return;
                }
                
                const cy = cytoscape({
                    container: document.getElementById('spider-map'),
                    elements: {
                        nodes: graphData.nodes,
                        edges: graphData.edges
                    },
                    style: [
                        {
                            selector: 'node',
                            style: {
                                'label': 'data(id)',
                                'color': 'white',
                                'text-valign': 'center',
                                'text-halign': 'center',
                                'width': 'mapData(total_degree, 0, 10, 20, 50)',
                                'height': 'mapData(total_degree, 0, 10, 20, 50)',
                                'font-size': '10px',
                                'font-weight': 'bold'
                            }
                        },
                        {
                            selector: 'node[node_type = "hub"]',
                            style: {
                                'background-color': '#e74c3c',
                                'width': 60,
                                'height': 60,
                                'font-size': '12px'
                            }
                        },
                        {
                            selector: 'node[node_type = "high_value"]',
                            style: {
                                'background-color': '#f39c12',
                                'width': 50,
                                'height': 50
                            }
                        },
                        {
                            selector: 'node[node_type = "source"]',
                            style: {
                                'background-color': '#27ae60',
                                'width': 40,
                                'height': 40
                            }
                        },
                        {
                            selector: 'node[node_type = "sink"]',
                            style: {
                                'background-color': '#8e44ad',
                                'width': 40,
                                'height': 40
                            }
                        },
                        {
                            selector: 'node[node_type = "normal"]',
                            style: {
                                'background-color': '#3498db'
                            }
                        },
                        {
                            selector: 'edge',
                            style: {
                                'width': 'mapData(weight, 0, 10000, 1, 5)',
                                'line-color': '#2c3e50',
                                'target-arrow-color': '#2c3e50',
                                'target-arrow-shape': 'triangle',
                                'curve-style': 'bezier',
                                'label': 'data(weight)',
                                'font-size': '8px',
                                'text-rotation': 'autorotate'
                            }
                        }
                    ],
                    layout: {
                        name: 'cose',
                        animate: true,
                        animationDuration: 1000,
                        nodeDimensionsIncludeLabels: true,
                        fit: true,
                        padding: 50
                    }
                });
                
                // Add interactive features
                cy.on('tap', 'node', function(evt) {
                    const node = evt.target;
                    const nodeData = node.data();
                    const details = `
                        <div style="background: #232b3a; color: #f5f7fa; padding: 22px; border-radius: 12px; box-shadow: 0 4px 18px #101624cc; position: absolute; z-index: 1000; min-width: 260px; font-size: 1.12em; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; border: 2px solid #4e8cff;">
                            <h4 style='color:#7ed6ff; margin-bottom: 10px;'>Account: <span style='color:#fff;'>${nodeData.id}</span></h4>
                            <p><strong>Type:</strong> <span style='color:#ffe082;'>${nodeData.node_type}</span></p>
                            <p><strong>Connections:</strong> <span style='color:#fff;'>${nodeData.total_degree}</span></p>
                            <p><strong>Money In:</strong> <span style='color:#55efc4;'>$${nodeData.in_amount.toLocaleString()}</span></p>
                            <p><strong>Money Out:</strong> <span style='color:#ff7675;'>$${nodeData.out_amount.toLocaleString()}</span></p>
                            <p><strong>Net Flow:</strong> <span style='color:#7ed6ff;'>$${nodeData.net_flow.toLocaleString()}</span></p>
                            <p><strong>IP:</strong> <span style='color:#fff;'>${nodeData.ip}</span></p>
                            <p><strong>Phone:</strong> <span style='color:#fff;'>${nodeData.phone}</span></p>
                            <p><strong>Email:</strong> <span style='color:#fff;'>${nodeData.email}</span></p>
                        </div>
                    `;
                    
                    // Remove previous tooltip
                    const existingTooltip = document.querySelector('.node-tooltip');
                    if (existingTooltip) existingTooltip.remove();
                    
                    // Add new tooltip
                    const tooltip = document.createElement('div');
                    tooltip.className = 'node-tooltip';
                    tooltip.innerHTML = details;
                    tooltip.style.position = 'absolute';
                    tooltip.style.left = evt.renderedPosition.x + 'px';
                    tooltip.style.top = (evt.renderedPosition.y - 100) + 'px';
                    document.getElementById('spider-map').appendChild(tooltip);
                });
                
                // Remove tooltip when clicking elsewhere
                cy.on('tap', function(evt) {
                    if (evt.target === cy) {
                        const tooltip = document.querySelector('.node-tooltip');
                        if (tooltip) tooltip.remove();
                    }
                });
                
                // Add zoom controls
                const zoomIn = document.createElement('button');
                zoomIn.innerHTML = '🔍+';
                zoomIn.style.position = 'absolute';
                zoomIn.style.top = '10px';
                zoomIn.style.right = '50px';
                zoomIn.style.zIndex = '1000';
                zoomIn.onclick = () => cy.zoom(cy.zoom() * 1.2);
                document.getElementById('spider-map').appendChild(zoomIn);
                
                const zoomOut = document.createElement('button');
                zoomOut.innerHTML = '🔍-';
                zoomOut.style.position = 'absolute';
                zoomOut.style.top = '10px';
                zoomOut.style.right = '10px';
                zoomOut.style.zIndex = '1000';
                zoomOut.onclick = () => cy.zoom(cy.zoom() / 1.2);
                document.getElementById('spider-map').appendChild(zoomOut);
                
                // Store cy instance globally for controls
                window.cy = cy;
                
                // Update status
                document.getElementById('map-status').innerHTML = `✅ Map loaded successfully! Showing ${graphData.nodes.length} accounts and ${graphData.edges.length} transactions.`;
        document.getElementById('map-status').style.color = '#ffffff';
        document.getElementById('map-status').style.fontWeight = '500';
                
            } catch (error) {
                console.error('Error loading spider map:', error);
                document.getElementById('spider-map').innerHTML = '<div class="error">Error loading spider map: ' + error.message + '</div>';
                document.getElementById('map-status').innerHTML = '❌ Error loading map';
        document.getElementById('map-status').style.color = '#d32f2f';
        document.getElementById('map-status').style.fontWeight = '500';
            }
        }

        // Map control functions
        function resetMapView() {
            if (window.cy) {
                window.cy.reset();
                window.cy.fit();
            }
        }

        function fitMapToScreen() {
            if (window.cy) {
                window.cy.fit();
            }
        }

        function toggleMapLabels() {
            if (window.cy) {
                const nodes = window.cy.nodes();
                const currentStyle = nodes.style('label');
                const newStyle = currentStyle === 'data(id)' ? '' : 'data(id)';
                nodes.style('label', newStyle);
                
                const edges = window.cy.edges();
                const currentEdgeStyle = edges.style('label');
                const newEdgeStyle = currentEdgeStyle === 'data(weight)' ? '' : 'data(weight)';
                edges.style('label', newEdgeStyle);
            }
        }

        async function filterTransactions() {
            try {
                const filters = {
                    case_id: document.getElementById('caseId').value || null,
                    account: document.getElementById('account').value || null,
                    ip: document.getElementById('ip').value || null,
                    phone: document.getElementById('phone').value || null,
                    email: document.getElementById('email').value || null,
                    min_amount: document.getElementById('minAmount').value || null,
                    max_amount: document.getElementById('maxAmount').value || null,
                    date_from: document.getElementById('dateFrom').value || null,
                    date_to: document.getElementById('dateTo').value || null
                };
                
                // Remove null values
                Object.keys(filters).forEach(key => {
                    if (filters[key] === null) delete filters[key];
                });
                
                const response = await axios.post('/api/filter', filters);
                const results = response.data;
                
                const output = document.getElementById('filterOutput');
                if (results.length === 0) {
                    output.innerHTML = '<div style="color: #666; text-align: center; padding: 20px;">No transactions found</div>';
                } else {
                    output.innerHTML = `
                        <h4>Found ${results.length} transactions:</h4>
                        <div style="max-height: 300px; overflow-y: auto; background: #f8f9fa; padding: 15px; border-radius: 8px;">
                            <pre>${JSON.stringify(results, null, 2)}</pre>
                        </div>
                    `;
                }
            } catch (error) {
                console.error('Error filtering transactions:', error);
                document.getElementById('filterOutput').innerHTML = '<div class="error">Error filtering transactions</div>';
            }
        }

        async function findMoneyTrail() {
            const account = document.getElementById('account').value;
            if (!account) {
                alert('Please enter an account number to find money trail');
                return;
            }
            
            try {
                const response = await axios.get(`/api/money-trail/${account}`);
                const trailData = response.data;
                
                const output = document.getElementById('filterOutput');
                output.innerHTML = `
                    <h4>Money Trail for Account: ${account}</h4>
                    <p>Found ${trailData.trail_count} possible trails:</p>
                    <div style="max-height: 300px; overflow-y: auto; background: #f8f9fa; padding: 15px; border-radius: 8px;">
                        <pre>${JSON.stringify(trailData.trails, null, 2)}</pre>
                    </div>
                `;
            } catch (error) {
                console.error('Error finding money trail:', error);
                document.getElementById('filterOutput').innerHTML = '<div class="error">Error finding money trail</div>';
            }
        }

        document.getElementById('uploadForm').onsubmit = async function(e) {
          e.preventDefault();
          const formData = new FormData();
          formData.append('file', document.getElementById('fileInput').files[0]);
          document.getElementById('uploadStatus').innerText = 'Uploading...';
          try {
            const res = await axios.post('/upload', formData, {headers: {'Content-Type': 'multipart/form-data'}});
            let msg = res.data.message;
            if (res.data.anomalies && res.data.anomalies.length > 0) {
              msg += '<br><b>Top Anomalies:</b><br>';
              msg += '<table border="1" style="width:100%;font-size:12px;"><tr>';
              Object.keys(res.data.anomalies[0]).forEach(k => { msg += `<th>${k}</th>`; });
              msg += '</tr>';
              res.data.anomalies.forEach(row => {
                msg += '<tr>';
                Object.values(row).forEach(v => { msg += `<td>${v}</td>`; });
                msg += '</tr>';
              });
              msg += '</table>';
            }
            document.getElementById('uploadStatus').innerHTML = msg;
            // Reload dashboard data after successful upload
            loadStatistics();
            loadSuspiciousAccounts();
            loadLayeredAnalysis();
            loadSpiderMap();
          } catch (err) {
            document.getElementById('uploadStatus').innerText = 'Upload failed: ' + (err.response?.data?.error || err.message);
          }
        };
    </script>
</body>
</html>
'''

# -------------------------
# Modern Welcome Page for FinTrace
# -------------------------
WELCOME_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Welcome to FinTrace - Advanced Financial Crime Detection</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #0f1419;
            min-height: 100vh;
            color: #ffffff;
            overflow-x: hidden;
            position: relative;
        }
        
        body::before {
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: 
                radial-gradient(circle at 20% 20%, rgba(0, 170, 255, 0.08) 0%, transparent 50%),
                radial-gradient(circle at 80% 80%, rgba(0, 255, 255, 0.06) 0%, transparent 50%);
            pointer-events: none;
            z-index: -1;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        /* Header Section */
        .header {
            text-align: center;
            padding: 40px 0 30px;
            color: white;
            position: relative;
        }
        
        .header h1 {
            font-size: 3.5rem;
            font-weight: 700;
            margin-bottom: 15px;
            color: #00aaff;
            text-shadow: 0 0 10px rgba(0, 170, 255, 0.4);
        }
        
        .header .subtitle {
            font-size: 1.4rem;
            margin-bottom: 20px;
            color: #00ffff;
            font-weight: 500;
        }
        
        .header .description {
            font-size: 1.1rem;
            max-width: 800px;
            margin: 0 auto;
            line-height: 1.6;
            color: #b0b8c9;
        }
        
        /* Mobile Responsive Design */
        @media (max-width: 768px) {
            .container {
                padding: 15px !important;
            }
            
            .header {
                padding: 30px 0 20px !important;
            }
            
            .header h1 {
                font-size: 4.5rem !important;
                margin-bottom: 25px !important;
            }
            
            .header .subtitle {
                font-size: 1.8rem !important;
                margin-bottom: 30px !important;
            }
            
            .header .description {
                font-size: 1.3rem !important;
                line-height: 1.8 !important;
                margin-bottom: 35px !important;
            }
        }
        
        @media (max-width: 480px) {
            .container {
                padding: 10px !important;
            }
            
            .header h1 {
                font-size: 4rem !important;
                margin-bottom: 20px !important;
            }
            
            .header .subtitle {
                font-size: 1.6rem !important;
                margin-bottom: 25px !important;
            }
            
            .header .description {
                font-size: 1.2rem !important;
                line-height: 1.7 !important;
                margin-bottom: 30px !important;
            }
        }
        
        /* Features Grid */
        .features {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 40px;
            margin: 80px 0;
        }
        
        .feature-card {
            background: rgba(15, 20, 25, 0.95);
            border-radius: 15px;
            padding: 40px 30px;
            text-align: center;
            box-shadow: 0 8px 25px rgba(0,0,0,0.3);
            transition: all 0.4s ease;
            border: 2px solid #1a2332;
            position: relative;
            overflow: hidden;
            min-height: 280px;
        }
        
        .feature-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: linear-gradient(90deg, #00aaff, #00ffff, #00aaff);
            transform: scaleX(0);
            transition: transform 0.4s ease;
        }
        
        .feature-card:hover::before {
            transform: scaleX(1);
        }
        
        .feature-card:hover {
            transform: translateY(-10px);
            border-color: #00aaff;
            box-shadow: 0 0 25px rgba(0, 170, 255, 0.4);
        }
        
        .feature-icon {
            font-size: 4rem;
            margin-bottom: 25px;
            color: #00aaff;
            text-shadow: 0 0 3px rgba(0, 170, 255, 0.2);
            transition: all 0.3s ease;
        }
        
        .feature-card:hover .feature-icon {
            transform: scale(1.1);
            color: #00ffff;
            text-shadow: 0 0 5px rgba(0, 255, 255, 0.3);
        }
        
        .feature-card h3 {
            font-size: 1.4rem;
            margin-bottom: 15px;
            color: #00ffff;
            font-weight: 600;
        }
        
        .feature-card p {
            color: #b0b8c9;
            line-height: 1.6;
            font-size: 1rem;
        }
        
        /* CTA Section */
        .cta-section {
            text-align: center;
            padding: 80px 0;
            position: relative;
        }
        
        .cta-section::before {
            content: '';
            position: absolute;
            top: 50%;
            left: 0;
            right: 0;
            height: 1px;
            background: linear-gradient(90deg, transparent, #00aaff, transparent);
        }
        
        .cta-button {
            display: inline-block;
            background: linear-gradient(45deg, #00aaff, #00ffff);
            color: #000;
            padding: 25px 50px;
            border-radius: 60px;
            text-decoration: none;
            font-size: 1.3rem;
            font-weight: 700;
            transition: all 0.4s ease;
            box-shadow: 0 0 15px rgba(0, 170, 255, 0.3);
            border: none;
            cursor: pointer;
            position: relative;
            overflow: hidden;
            text-shadow: none;
        }
        
        .cta-button::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
            transition: left 0.6s ease;
        }
        
        .cta-button:hover::before {
            left: 100%;
        }
        
        .cta-button:hover {
            transform: translateY(-5px);
            box-shadow: 0 0 20px rgba(0, 170, 255, 0.5);
            background: linear-gradient(45deg, #00ffff, #00aaff);
        }
        
        /* Stats Section */
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 40px;
            margin: 80px 0;
        }
        
        /* Mobile layout for stats - 2x2 grid */
        @media (max-width: 768px) {
            .stats {
                grid-template-columns: repeat(2, 1fr);
                gap: 20px;
                margin: 40px 0;
            }
            
            /* Mobile header improvements */
            .header h1 {
                font-size: 4rem;
                margin-bottom: 20px;
            }
            
            .header .subtitle {
                font-size: 1.6rem;
                margin-bottom: 25px;
            }
            
            .header .description {
                font-size: 1.2rem;
                line-height: 1.8;
                margin-bottom: 30px;
            }
        }
        
        @media (max-width: 480px) {
            .stats {
                grid-template-columns: repeat(2, 1fr);
                gap: 15px;
                margin: 30px 0;
            }
            
            /* Small mobile header improvements */
            .header h1 {
                font-size: 3.5rem;
                margin-bottom: 18px;
            }
            
            .header .subtitle {
                font-size: 1.4rem;
                margin-bottom: 22px;
            }
            
            .header .description {
                font-size: 1.1rem;
                line-height: 1.7;
                margin-bottom: 25px;
            }
        }
        
        .stat-item {
            text-align: center;
            color: white;
            background: rgba(20, 20, 20, 0.8);
            border-radius: 20px;
            padding: 40px 20px;
            border: 2px solid #00aaff;
            transition: all 0.4s ease;
            position: relative;
            overflow: hidden;
            box-shadow: 0 0 10px rgba(0, 170, 255, 0.2);
        }
        
        .stat-item::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(0, 170, 255, 0.2), transparent);
            transition: left 0.6s ease;
        }
        
        .stat-item:hover::before {
            left: 100%;
        }
        
        .stat-item:hover {
            transform: translateY(-8px);
            border-color: #00ffff;
            box-shadow: 0 0 15px rgba(0, 170, 255, 0.4);
        }
        
        .stat-number {
            font-size: 4rem;
            font-weight: 800;
            margin-bottom: 15px;
            color: #00aaff;
            text-shadow: 0 0 5px rgba(0, 170, 255, 0.2);
        }
        
        .stat-label {
            font-size: 1.2rem;
            font-weight: 600;
            color: #ffffff;
        }
        
        /* Mobile Responsive Design */
        @media (max-width: 768px) {
            /* Fix mobile scrolling */
            html, body {
                overflow-y: auto;
                -webkit-overflow-scrolling: touch;
                height: auto;
                min-height: 100vh;
            }
            
            .container {
                padding: 15px;
                max-width: 100%;
            }
            
            .header {
                padding: 20px 0 15px;
            }
            
            .header h1 {
                font-size: 2.5rem;
                margin-bottom: 10px;
            }
            
            .header .subtitle {
                font-size: 1.2rem;
                margin-bottom: 15px;
            }
            
            .header .description {
                font-size: 1rem;
                max-width: 100%;
            }
            
            .dashboard {
                grid-template-columns: 1fr;
                gap: 20px;
            }
            
            .card {
                padding: 20px 15px;
                margin-bottom: 15px;
            }
            
            .card h3 {
                font-size: 1.6rem;
                margin-bottom: 20px;
                margin-top: -5px;
            }
            
            .stats-grid {
                grid-template-columns: repeat(2, 1fr);
                gap: 15px;
            }
            
            .stat-item {
                padding: 15px 10px;
                min-height: 80px;
            }
            
            .stat-value {
                font-size: 1.4rem;
                margin-bottom: 6px;
            }
            
            .stat-label {
                font-size: 0.9rem;
            }
            
            .filter-section {
                padding: 20px 15px;
                margin-bottom: 20px;
            }
            
            .filter-section h3 {
                font-size: 1.6rem;
                margin-bottom: 20px;
                margin-top: -5px;
            }
            
            .filter-grid {
                grid-template-columns: 1fr;
                gap: 12px;
            }
            
            .filter-input {
                padding: 10px 12px;
                font-size: 16px; /* Prevents zoom on iOS */
            }
            
            .btn {
                padding: 10px 20px;
                font-size: 14px;
                margin: 5px 0;
                width: 100%;
                max-width: 200px;
            }
            
            .graph-container {
                padding: 20px 15px;
                margin-top: 5px;
            }
            
            .graph-container h3 {
                font-size: 1.6rem;
                margin-bottom: 20px;
                margin-top: -5px;
            }
            
            #spider-map {
                height: 400px;
            }
            
            .layered-analysis {
                grid-template-columns: 1fr;
                gap: 12px;
            }
            
            .layer-card {
                padding: 12px;
            }
            
            .suspicious-list {
                max-height: 250px;
            }
            
            .suspicious-item {
                padding: 10px;
                font-size: 0.9rem;
            }
        }
        
        @media (max-width: 480px) {
            .container {
                padding: 10px;
            }
            
            .header h1 {
                font-size: 2rem;
            }
            
            .header .subtitle {
                font-size: 1.1rem;
            }
            
            .header .description {
                font-size: 0.95rem;
            }
            
            .card h3 {
                font-size: 1.4rem;
            }
            
            .filter-section h3,
            .graph-container h3 {
                font-size: 1.4rem;
            }
            
            .stats-grid {
                grid-template-columns: 1fr;
                gap: 12px;
            }
            
            .stat-item {
                padding: 12px 8px;
            }
            
            .stat-value {
                font-size: 1.2rem;
            }
            
            .stat-label {
                font-size: 0.85rem;
            }
            
            .filter-grid {
                gap: 10px;
            }
            
            .filter-input {
                padding: 8px 10px;
                font-size: 16px;
            }
            
            .btn {
                padding: 8px 16px;
                font-size: 13px;
                max-width: 180px;
            }
            
            #spider-map {
                height: 350px;
            }
            
            .suspicious-item {
                padding: 8px;
                font-size: 0.85rem;
            }
        }
        
        @media (max-width: 360px) {
            .header h1 {
                font-size: 1.8rem;
            }
            
            .card h3 {
                font-size: 1.3rem;
            }
            
            .filter-section h3,
            .graph-container h3 {
                font-size: 1.3rem;
            }
            
            .stat-value {
                font-size: 1.1rem;
            }
            
            .btn {
                padding: 6px 14px;
                font-size: 12px;
                max-width: 160px;
            }
        }
        
        /* Cool Dark Theme Animations */
        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        @keyframes slideInLeft {
            from {
                opacity: 0;
                transform: translateX(-30px);
            }
            to {
                opacity: 1;
                transform: translateX(0);
            }
        }
        
        @keyframes slideInRight {
            from {
                opacity: 0;
                transform: translateX(30px);
            }
            to {
                opacity: 1;
                transform: translateX(0);
            }
        }
        
        @keyframes pulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.05); }
        }
        
        .feature-card {
            animation: fadeInUp 0.6s ease forwards;
            opacity: 0;
        }
        
        .feature-card:nth-child(1) { animation-delay: 0.1s; }
        .feature-card:nth-child(2) { animation-delay: 0.2s; }
        .feature-card:nth-child(3) { animation-delay: 0.3s; }
        .feature-card:nth-child(4) { animation-delay: 0.4s; }
        .feature-card:nth-child(5) { animation-delay: 0.5s; }
        .feature-card:nth-child(6) { animation-delay: 0.6s; }
        
        .stat-item:nth-child(1) { animation: slideInLeft 0.6s ease forwards; opacity: 0; }
        .stat-item:nth-child(2) { animation: slideInRight 0.6s ease forwards; opacity: 0; }
        .stat-item:nth-child(3) { animation: slideInLeft 0.6s ease forwards; opacity: 0; }
        .stat-item:nth-child(4) { animation: slideInRight 0.6s ease forwards; opacity: 0; }
        
        .cta-section {
            animation: fadeInUp 0.8s ease forwards;
            animation-delay: 0.7s;
            opacity: 0;
        }
        
        .cta-button:hover {
            animation: pulse 1s ease-in-out infinite;
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- Header Section -->
        <div class="header">
            <h1>🚨 FinTrace</h1>
            <div class="subtitle">Hackathon Project - Money Laundering Pattern Detection</div>
            <div class="description">
                Advanced AI-powered system to detect sophisticated money laundering patterns, analyze complex transaction networks, and provide actionable insights for law enforcement investigators. Built to tackle the challenges of digital banking, cryptocurrency, and cross-border financial crimes.
            </div>
        </div>
        
        <!-- Middle Section Call to Action Button -->
        <div style="margin: 0; padding: 0; text-align: center;">
            <a href="/dashboard" class="cta-button" style="margin: 0; padding: 12px 25px;">
                <i class="fas fa-rocket"></i> Launch FinTrace Detection System
            </a>
        </div>
        
        <!-- Stats Section -->
        <div class="stats">
            <div class="stat-item">
                <div class="stat-number">5</div>
                <div class="stat-label">Detection Layers</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">🔍</div>
                <div class="stat-label">Anomaly Detection</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">🕸️</div>
                <div class="stat-label">Network Analysis</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">🚨</div>
                <div class="stat-label">Alert System</div>
            </div>
        </div>
        

        
        <!-- Features Grid -->
        <div class="features">
            <div class="feature-card">
                <div class="feature-icon">
                    <i class="fas fa-shield-alt"></i>
                </div>
                <h3 style="color:#00FFFF;">Multi-Layer Detection Engine</h3>
                <p>Advanced 5-layer detection system using machine learning algorithms to identify sophisticated money laundering patterns, layering techniques, and complex transaction chains.</p>
            </div>
            
            <div class="feature-card">
                <div class="feature-icon">
                    <i class="fas fa-spider"></i>
                </div>
                <h3 style="color:#00FFFF;">Network Analysis & Visualization</h3>
                <p>Interactive spider maps showing transaction relationships, money trails, and suspicious connection patterns across multiple entities and jurisdictions.</p>
            </div>
            
            <div class="feature-card">
                <div class="feature-icon">
                    <i class="fas fa-search-dollar"></i>
                </div>
                <h3 style="color:#00FFFF;">Money Trail Tracking</h3>
                <p>Advanced path analysis algorithms to trace illicit money flows, detect round-tripping transactions, and identify complex laundering schemes.</p>
            </div>
            
            <div class="feature-card">
                <div class="feature-icon">
                    <i class="fas fa-filter"></i>
                </div>
                <h3 style="color:#00FFFF;">Intelligent Pattern Recognition</h3>
                <p>AI-powered anomaly detection to identify unusual transaction sequences, cross-border transfers, and suspicious fund movements in real-time.</p>
            </div>
            
            <div class="feature-card">
                <div class="feature-icon">
                    <i class="fas fa-robot"></i>
                </div>
                <h3 style="color:#00FFFF;">Machine Learning Algorithms</h3>
                <p>Sophisticated ML models including Isolation Forest, DBSCAN clustering, and statistical analysis for detecting hidden laundering patterns.</p>
            </div>
            
            <div class="feature-card">
                <div class="feature-icon">
                    <i class="fas fa-file-export"></i>
                </div>
                <h3 style="color:#00FFFF;">Investigation Reports</h3>
                <p>Prioritized alerts and detailed reports for law enforcement investigators, providing actionable insights to trace illicit money flows.</p>
            </div>
        </div>
        
        <!-- Call to Action -->
        <div class="cta-section">
            <a href="/dashboard" class="cta-button">
                <i class="fas fa-rocket"></i> Launch FinTrace Detection System
            </a>
        </div>
    </div>
</body>
</html>
'''

@app.route('/get-started')
def get_started():
    return render_template_string(WELCOME_TEMPLATE)

@app.route('/logout')
def logout():
    # Remove temp uploaded file if it exists
    uploaded_file = session.pop('uploaded_data_file', None)
    if uploaded_file and os.path.exists(uploaded_file):
        try:
            os.remove(uploaded_file)
        except Exception:
            pass
    return redirect(url_for('get_started'))

# -------------------------
# Main
# -------------------------
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)

