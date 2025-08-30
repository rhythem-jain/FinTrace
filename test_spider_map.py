#!/usr/bin/env python3
"""
Test script for Spider Map functionality
"""

import requests
import json
import time

def test_spider_map():
    """Test the spider map endpoint"""
    base_url = "http://localhost:5000"
    
    print("🧪 Testing Spider Map Functionality...")
    print("=" * 50)
    
    # Test 1: Check if server is running
    try:
        response = requests.get(f"{base_url}/")
        if response.status_code == 200:
            print("✅ Server is running")
        else:
            print("❌ Server not responding properly")
            return
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Make sure Flask app is running.")
        return
    
    # Test 2: Test spider map endpoint
    try:
        print("\n📊 Testing Spider Map Endpoint...")
        response = requests.get(f"{base_url}/api/spider-map")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Spider map endpoint working")
            
            # Check data structure
            if 'nodes' in data and 'edges' in data:
                print(f"📈 Found {len(data['nodes'])} nodes and {len(data['edges'])} edges")
                
                if 'statistics' in data:
                    stats = data['statistics']
                    print(f"💰 Total amount: ${stats.get('total_amount', 0):,.2f}")
                    print(f"🔍 Suspicious nodes: {len(stats.get('suspicious_nodes', []))}")
                
                # Show sample nodes
                if data['nodes']:
                    print("\n📋 Sample Nodes:")
                    for i, node in enumerate(data['nodes'][:3]):
                        node_data = node['data']
                        print(f"  {i+1}. Account: {node_data['id']}")
                        print(f"     Type: {node_data.get('node_type', 'unknown')}")
                        print(f"     Connections: {node_data.get('total_degree', 0)}")
                        print(f"     Money Out: ${node_data.get('out_amount', 0):,.2f}")
                
                # Show sample edges
                if data['edges']:
                    print("\n🔗 Sample Edges:")
                    for i, edge in enumerate(data['edges'][:3]):
                        edge_data = edge['data']
                        print(f"  {i+1}. {edge_data['source']} → {edge_data['target']}")
                        print(f"     Amount: ${edge_data.get('weight', 0):,.2f}")
                
            else:
                print("❌ Invalid data structure returned")
                
        else:
            print(f"❌ Spider map endpoint failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing spider map: {e}")
    
    # Test 3: Test statistics endpoint
    try:
        print("\n📈 Testing Statistics Endpoint...")
        response = requests.get(f"{base_url}/api/statistics")
        
        if response.status_code == 200:
            stats = response.json()
            print("✅ Statistics endpoint working")
            print(f"📊 Total transactions: {stats.get('total_transactions', 0)}")
            print(f"🏦 Total accounts: {stats.get('total_accounts', 0)}")
            print(f"💰 Total amount: ${stats.get('total_amount', 0):,.2f}")
        else:
            print(f"❌ Statistics endpoint failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing statistics: {e}")
    
    # Test 4: Test suspicious accounts endpoint
    try:
        print("\n🚨 Testing Suspicious Accounts Endpoint...")
        response = requests.get(f"{base_url}/api/suspicious")
        
        if response.status_code == 200:
            suspicious = response.json()
            print(f"✅ Found {len(suspicious)} suspicious accounts")
            
            if suspicious:
                print("📋 Sample suspicious accounts:")
                for i, account in enumerate(suspicious[:2]):
                    print(f"  {i+1}. Account: {account.get('account', 'N/A')}")
                    print(f"     Transactions: {account.get('total_transactions', 0)}")
                    print(f"     Total Amount: ${account.get('total_amount', 0):,.2f}")
        else:
            print(f"❌ Suspicious accounts endpoint failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing suspicious accounts: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Testing Complete!")
    print("\n📝 Next Steps:")
    print("1. Open http://localhost:5000 in your browser")
    print("2. Look for the Spider Map section")
    print("3. Use the interactive features to explore the data")
    print("4. Check the SPIDER_MAP_GUIDE.md for detailed instructions")

if __name__ == "__main__":
    test_spider_map() 