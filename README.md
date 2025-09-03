# Django POI Manager

A Django-based Point of Interest (POI) management system with support for importing data from multiple file formats (CSV, JSON, XML).

## Features

- Import POIs from CSV, JSON, and XML files
- GeoDjango integration for spatial data handling
- Django admin interface for POI management
- Batch processing for large datasets (1M+ records)
- PostgreSQL with PostGIS for geographic data
- Redis for caching and job queuing
- Docker support for easy deployment

## Requirements

- Python 3.10+
- PostgreSQL with PostGIS extension
- Redis
- GDAL/GEOS libraries (for GeoDjango)

## Installation

### Local Development

1. Clone the repository:
```bash
git clone <repository-url>
cd poi-manager
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Set up PostgreSQL database:
```bash
createdb poi_manager
psql -d poi_manager -c "CREATE EXTENSION postgis;"
```

5. Run migrations:
```bash
python manage.py migrate
```

6. Create a superuser:
```bash
python manage.py createsuperuser
```

7. Run the development server:
```bash
python manage.py runserver
```

### Docker Setup

1. Build and run with Docker Compose:
```bash
docker-compose up --build
```

The application will be available at http://localhost:8000

## Usage

### Importing POI Data

Use the management command to import POI data from files:

```bash
python manage.py import_pois /path/to/data.csv
python manage.py import_pois /path/to/data.json /path/to/data.xml
```

### Admin Interface

Access the Django admin at http://localhost:8000/admin to:
- View and search POIs by internal ID or external ID
- Filter POIs by category
- View average ratings and other POI details
- Monitor import batches

## Data Format

### CSV Format
```csv
poi_id,poi_name,poi_category,poi_latitude,poi_longitude,poi_ratings
```

### JSON Format
```json
[
  {
    "id": "123",
    "name": "POI Name",
    "category": "restaurant",
    "coordinates": {
      "latitude": 40.7128,
      "longitude": -74.0060
    },
    "ratings": [4, 5, 3]
  }
]
```

### XML Format
```xml
<DATA_RECORD>
  <pid>123</pid>
  <pname>POI Name</pname>
  <pcategory>restaurant</pcategory>
  <platitude>40.7128</platitude>
  <plongitude>-74.0060</plongitude>
  <pratings>4,5,3</pratings>
</DATA_RECORD>
```

## Project Structure

```
django-poi-manager/
├── poi_manager/           # Main Django app
│   ├── models/           # Data models
│   ├── parsers/          # File parsers (CSV, JSON, XML)
│   ├── management/       # Management commands
│   ├── admin.py          # Django admin configuration
│   └── migrations/       # Database migrations
├── poi_manager_project/   # Django project settings
├── docker-compose.yml    # Docker configuration
├── requirements.txt      # Python dependencies
└── manage.py            # Django management script
```

## License

MIT License
