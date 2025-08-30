# 🕷️ Spider Map Guide - FinTrace AML Dashboard

## Overview
The Spider Map is an interactive network visualization that shows how money flows between accounts, helping you identify suspicious transaction patterns and relationships in your AML detection system.

## 🚀 How to Run

### 1. Start the Application
```bash
python app.py
```
The Flask server will start on `http://localhost:5000`

### 2. Access the Dashboard
- Open your browser and go to `http://localhost:5000`
- The spider map will automatically load when the page loads

### 3. Data Loading
- The system automatically loads transaction data from the Excel file (`bank.xlsx`)
- If no data exists, it will create sample transactions from the Excel file
- The spider map displays up to 500 transactions for optimal performance

## 📊 Understanding the Spider Map

### Node Types (Color-Coded)

| Color | Node Type | Meaning | Suspicion Level |
|-------|-----------|---------|-----------------|
| 🔴 **Red** | Hub | High-activity accounts with many connections | **HIGH** - Potential layering or mule accounts |
| 🟡 **Yellow** | High-Value | Accounts with large transaction amounts | **MEDIUM** - Check for legitimate business |
| 🟢 **Green** | Source | Accounts that only send money (no incoming) | **MEDIUM** - Could be money origin |
| 🟣 **Purple** | Sink | Accounts that only receive money (no outgoing) | **MEDIUM** - Could be final destination |
| 🔵 **Blue** | Normal | Regular accounts with balanced activity | **LOW** - Normal business activity |

### Edge Information
- **Arrow Direction**: Shows money flow (from → to)
- **Edge Thickness**: Proportional to transaction amount
- **Edge Labels**: Display transaction amounts
- **Hover/Click**: Shows transaction details (date, time, ID)

## 🔍 How to Interpret Patterns

### 1. **Suspicious Patterns to Look For**

#### 🔴 **Hub Nodes (Red)**
- **What**: Accounts with many connections (>5)
- **Why Suspicious**: Could be layering accounts or money mules
- **Action**: Investigate transaction patterns and amounts

#### 🔄 **Circular Flows**
- **What**: Money that returns to the original sender
- **Why Suspicious**: Classic layering technique
- **Action**: Trace the complete cycle and check for legitimate business

#### 📈 **High-Value Nodes (Yellow)**
- **What**: Large transaction amounts (>$10,000)
- **Why Suspicious**: Could indicate structuring or large-scale laundering
- **Action**: Verify source of funds and business purpose

#### 🎯 **Source-Sink Patterns**
- **What**: Clear money flow from sources to sinks
- **Why Suspicious**: Could indicate organized laundering
- **Action**: Trace the complete money trail

### 2. **Interactive Features**

#### **Click on Nodes**
- Shows detailed account information:
  - Account number and type
  - Total connections (in/out)
  - Money flow amounts
  - IP address, phone, email
  - Net money flow

#### **Zoom Controls**
- **🔍+**: Zoom in for detailed view
- **🔍-**: Zoom out for overview
- **Drag**: Pan around the map
- **Scroll**: Zoom in/out with mouse wheel

#### **Network Statistics**
The dashboard shows:
- Total accounts in the network
- Total transactions
- Total money flow
- Number of suspicious nodes detected

## 🛠️ Technical Details

### Backend Processing
1. **Data Loading**: Reads from SQLite database
2. **Graph Construction**: Uses NetworkX to build directed graph
3. **Node Classification**: Automatically categorizes nodes by behavior
4. **Metrics Calculation**: Computes connection counts and money flows
5. **Suspicious Detection**: Identifies potential laundering patterns

### Frontend Visualization
1. **Cytoscape.js**: Renders the interactive network
2. **Cose-Bilkent Layout**: Automatically arranges nodes
3. **Color Coding**: Different colors for different node types
4. **Interactive Tooltips**: Detailed information on click
5. **Zoom Controls**: Easy navigation

## 📋 Step-by-Step Analysis Process

### 1. **Initial Scan**
- Look for red (hub) nodes - these are priority
- Check for circular patterns
- Identify source and sink accounts

### 2. **Deep Dive**
- Click on suspicious nodes for details
- Trace money flows using the arrows
- Check transaction amounts and frequencies

### 3. **Pattern Recognition**
- Look for repeated transactions between same accounts
- Check for unusual timing patterns
- Verify if amounts are structured to avoid reporting

### 4. **Documentation**
- Note suspicious account numbers
- Record transaction patterns
- Document money flow paths

## 🚨 Red Flags to Watch For

1. **Multiple Small Transactions**: Structuring to avoid reporting
2. **Rapid Money Movement**: Same day in/out transactions
3. **Circular Flows**: Money returning to origin
4. **High-Frequency Accounts**: Too many transactions
5. **Unusual Amounts**: Just below reporting thresholds
6. **Multiple Identities**: Same account with different IPs/phones

## 💡 Tips for Effective Use

1. **Start with Overview**: Zoom out to see the big picture
2. **Focus on Hubs**: Red nodes are your primary targets
3. **Follow the Money**: Use arrows to trace flows
4. **Check Details**: Click nodes for comprehensive information
5. **Compare Patterns**: Look for similar structures across accounts
6. **Document Everything**: Keep notes of suspicious patterns

## 🔧 Troubleshooting

### Common Issues

**Map Not Loading**
- Check if Flask server is running
- Verify data exists in database
- Check browser console for errors

**No Data Displayed**
- Ensure Excel file is properly loaded
- Check database connection
- Verify transaction data format

**Performance Issues**
- Reduce sample size in code (currently 500 transactions)
- Close other browser tabs
- Use zoom to focus on specific areas

## 📞 Support

If you encounter issues:
1. Check the browser console for error messages
2. Verify the Flask server is running
3. Ensure all required libraries are installed
4. Check the database file exists and has data

---

**Remember**: The spider map is a tool to help identify patterns. Always verify findings with additional investigation and follow your organization's AML procedures. 