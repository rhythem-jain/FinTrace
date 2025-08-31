 # 🚨 Layered AML Detection System

## Overview

The Layered AML (Anti-Money Laundering) Detection System is an advanced financial crime detection platform designed for law enforcement agencies. It provides multi-layer analysis of bank transactions to identify suspicious money laundering patterns and create interactive spider maps for money trail visualization.

## 🎯 Kc
- Path analysis between bank accounts
- Multi-hop transaction tracing
- Depth-limited search algorithms
- Trail visualization and reporting

## 🏗️ System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Interface │    │  Flask Backend  │    │  SQLite Database│
│   (HTML/CSS/JS) │◄──►│   (Python)      │◄──►│   (Transactions)│
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │  AML Engine     │
                       │  (Detection)    │
                       └─────────────────┘
```

## 🚀 Installation & Setup

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Installation Steps

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd layered_aml_detection_project
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   # Development mode
   python app.py
   
   # Production mode
   python runproduction.py
   ```

4. **Access the application**
   - Open your browser and navigate to `http://localhost:5000`
   - The system will automatically load transaction data from `large_sample_transactions.csv`

## 🚀 Deployment on Render

### Quick Deployment

1. **Check deployment readiness:**
   ```bash
   # Windows
   check_deployment.bat
   
   # Linux/Mac
   python deploy_to_render.py
   ```

2. **Deploy to Render:**
   - Push your code to GitHub
   - Go to [render.com](https://render.com) and create a new Blueprint
   - Connect your GitHub repository
   - Render will automatically detect the `render.yaml` configuration
   - Click "Apply" to deploy

### Manual Deployment

1. **Create a new Web Service on Render**
2. **Configure:**
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
   - **Environment:** Python 3
3. **Set Environment Variables:**
   - `FLASK_ENV`: `production`
   - `FLASK_DEBUG`: `0`

📖 **Detailed deployment guide:** See [RENDER_DEPLOYMENT.md](RENDER_DEPLOYMENT.md)

## 📊 Data Structure

The system processes transaction data with the following fields:

| Field | Description | Type |
|-------|-------------|------|
| Case_ID | Unique case identifier | String |
| Transaction_ID | Unique transaction ID | String |
| From_Account | Source account number | String |
| To_Account | Destination account number | String |
| Amount | Transaction amount | Float |
| Date | Transaction date | String |
| Time | Transaction time | String |
| IP | IP address used | String |
| Phone | Phone number | String |
| Email | Email address | String |

## 🔍 Detection Algorithms

### 1. High-Frequency Detection
- Uses IQR (Interquartile Range) method
- Identifies accounts with unusually high transaction counts
- Threshold: Q3 + 1.5 × IQR

### 2. Large Amount Detection
- Analyzes transaction amount percentiles
- Flags transactions above 99th percentile
- Identifies potential structuring activities

### 3. Multi-Identity Detection
- Tracks multiple IP addresses per account (>3)
- Monitors multiple phone numbers per account (>2)
- Detects multiple email addresses per account (>2)

### 4. Circular Transaction Detection
- Uses NetworkX to find cycles in transaction graph
- Identifies money laundering schemes
- Focuses on short cycles (≤5 nodes)

### 5. Rapid Movement Detection
- Analyzes daily transaction volumes
- Identifies accounts with high daily amounts
- Uses 95th percentile threshold

## 🕷️ Spider Map Features

### Interactive Visualization
- **Nodes**: Represent bank accounts
- **Edges**: Show transaction flows
- **Edge Weights**: Transaction amounts
- **Node Colors**: Account types (source/destination)

### Network Analysis
- **Degree Centrality**: Most connected accounts
- **Betweenness Centrality**: Key intermediary accounts
- **Closeness Centrality**: Central accounts in network

## 🔧 API Endpoints

### Core Endpoints
- `GET /` - Main dashboard
- `GET /api/suspicious` - Get suspicious accounts
- `GET /api/layered-analysis` - Get layered analysis results
- `GET /api/spider-map` - Get spider map data
- `GET /api/statistics` - Get system statistics

### Filtering Endpoints
- `POST /api/filter` - Filter transactions
- `GET /api/cases` - Get all cases
- `GET /api/money-trail/<account>` - Find money trail

## 🎨 User Interface

### Dashboard Components
1. **Statistics Panel**: System overview metrics
2. **Suspicious Accounts**: Detected suspicious accounts
3. **Layered Analysis**: Results from each detection layer
4. **Advanced Filtering**: Multi-criteria search
5. **Spider Map**: Interactive transaction network

### Features
- **Responsive Design**: Works on desktop and mobile
- **Real-time Updates**: Live data refresh
- **Interactive Graphs**: Clickable nodes and edges
- **Export Capabilities**: JSON data export
- **Error Handling**: Graceful error display

## 🔒 Security Features

### Data Protection
- SQL injection prevention
- Input validation and sanitization
- Secure database connections
- Error message sanitization

### Access Control
- Development/production mode separation
- Configurable host and port settings
- Environment-based configuration

## 📈 Performance Optimization

### Database Optimization
- Indexed database fields
- Efficient query patterns
- Connection pooling
- Query result caching

### Algorithm Optimization
- Efficient graph algorithms
- Memory-conscious data structures
- Parallel processing capabilities
- Caching mechanisms

## 🧪 Testing

### Manual Testing
1. Load the application
2. Verify data loading from CSV
3. Test suspicious account detection
4. Validate spider map rendering
5. Test filtering functionality
6. Verify money trail analysis

### Automated Testing
```bash
# Run basic functionality tests
python -c "import app; print('App imports successfully')"
```

## 🚀 Deployment

### Development Deployment
```bash
python app.py
```

### Production Deployment
```bash
python runproduction.py
```

### Docker Deployment (Optional)
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["python", "runproduction.py"]
```

## 📝 Configuration

### Environment Variables
- `FLASK_ENV`: Development/Production mode
- `DATABASE_URL`: Database connection string
- `HOST`: Server host (default: 0.0.0.0)
- `PORT`: Server port (default: 5000)

### Database Configuration
- **Type**: SQLite
- **File**: `instance/transactions.db`
- **Auto-creation**: Enabled
- **Indexing**: Optimized for queries

## 🔄 Data Import

### CSV Import Process
1. System checks for existing data
2. Reads `large_sample_transactions.csv`
3. Validates data format
4. Imports to SQLite database
5. Creates necessary indexes

### Data Validation
- Required field checking
- Data type validation
- Duplicate detection
- Format verification

## 🎯 Use Cases

### Law Enforcement
- **Case Investigation**: Track money trails across cases
- **Pattern Recognition**: Identify suspicious transaction patterns
- **Evidence Collection**: Document transaction relationships
- **Report Generation**: Create detailed analysis reports

### Financial Institutions
- **Compliance Monitoring**: Meet regulatory requirements
- **Risk Assessment**: Evaluate transaction risks
- **Alert Generation**: Flag suspicious activities
- **Audit Support**: Provide transaction audit trails

## 🔮 Future Enhancements

### Planned Features
- **Machine Learning Integration**: Advanced pattern recognition
- **Real-time Processing**: Live transaction monitoring
- **Multi-database Support**: PostgreSQL, MySQL
- **API Authentication**: Secure API access
- **Mobile App**: Native mobile application
- **Advanced Analytics**: Predictive modeling

### Technical Improvements
- **Microservices Architecture**: Scalable deployment
- **GraphQL API**: Flexible data querying
- **WebSocket Support**: Real-time updates
- **Docker Containerization**: Easy deployment
- **Kubernetes Orchestration**: Scalable infrastructure

## 🤝 Contributing

### Development Guidelines
1. Follow PEP 8 coding standards
2. Add comprehensive documentation
3. Include unit tests for new features
4. Update requirements.txt for new dependencies
5. Test thoroughly before submitting

### Code Structure
```
layered_aml_detection_project/
├── app.py                 # Main application
├── runproduction.py       # Production server
├── requirements.txt       # Dependencies
├── README.md             # Documentation
├── large_sample_transactions.csv  # Sample data
├── instance/             # Database files
└── venv/                # Virtual environment
```

## 📞 Support

### Documentation
- This README provides comprehensive system documentation
- Code comments explain complex algorithms
- API documentation available in code

### Troubleshooting
1. **Database Issues**: Check file permissions and disk space
2. **Import Errors**: Verify CSV format and data integrity
3. **Performance Issues**: Monitor memory usage and database size
4. **Visualization Problems**: Check browser compatibility

## 📄 License

This project is developed for educational and law enforcement purposes. Please ensure compliance with local regulations and data protection laws.

---

**🚨 Layered AML Detection System** - Advanced financial crime detection for law enforcement agencies. 