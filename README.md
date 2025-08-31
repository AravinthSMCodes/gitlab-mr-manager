# GitLab MR Manager

A modern, web-based interface for managing GitLab merge requests efficiently. Built with Flask and featuring a beautiful, responsive UI with advanced filtering and badge counting capabilities.

## Features

### 🎯 Core Functionality
- **Dashboard Overview**: Get a quick view of all MR statuses with real-time badge counts
- **All Open MRs**: View and manage all open merge requests with advanced filtering
- **To Be Reviewed MRs**: MRs that have all 3 review labels ("Self Reviewed", "Peer reviewed", "Ready to be Reviewed")
- **Reviewed MRs**: MRs that have all 4 review labels (including "Reviewed")
- **Good to Merge MRs**: MRs that have all 5 review labels (including "Good To Merge")
- **Merged MRs**: View recently merged changes with filtering options

### 🏷️ Smart Badge System
- **Real-time Counts**: Live badge counts showing MRs in each category
- **Label-based Logic**: 
  - **To Be Reviewed**: Requires ALL 3 labels ("Self Reviewed", "Peer reviewed", "Ready to be Reviewed")
  - **Reviewed MRs**: Requires ALL 4 labels (including "Reviewed")
  - **Good to Merge**: Requires ALL 5 labels (including "Good To Merge")
- **Accurate Filtering**: Uses GitLab API to fetch actual MR data and labels

### 🔍 Advanced Filtering & Search
- **Author Filter**: Filter MRs by specific authors
- **Reviewer Filter**: Filter MRs by assigned reviewers (not assignees)
- **Label Filter**: Filter MRs by GitLab labels with color coding
- **AND Logic**: All filters work with AND conditions for precise results
- **Clear Filters**: One-click option to clear all applied filters
- **URL-based State**: Filter state is preserved in URL for sharing/bookmarking

### 🎨 Modern UI/UX
- **Responsive Design**: Works perfectly on desktop, tablet, and mobile devices
- **Mobile Menu**: Collapsible sidebar with hamburger menu for mobile
- **Beautiful Interface**: Clean, modern design with gradient backgrounds
- **Interactive Elements**: Hover effects, loading states, and real-time updates
- **Color-coded Labels**: Labels display with actual GitLab colors
- **Branch Information**: Shows source and destination branches for each MR

### 🔧 Advanced Features
- **GitLab API Integration**: Real integration with GitLab API using python-gitlab
- **Redis Caching**: 24-hour cache for labels, reviewers, and authors lists for faster rendering
- **Label Management**: Add/remove labels directly from the interface
- **MR Actions**: 
  - "Mark as Reviewed" button adds "Reviewed" label
  - "Mark as GTM" button adds "Good To Merge" label
  - "Merge MR" button for merging approved MRs
- **Pagination**: Efficient pagination for large MR lists
- **Real-time Updates**: Live badge counts and status updates

## Screenshots

### Dashboard with Badge Counts
![Dashboard](https://via.placeholder.com/800x400/667eea/ffffff?text=Dashboard+with+Real-time+Badges)

### All Open MRs with Filters
![Open MRs](https://via.placeholder.com/800x400/10b981/ffffff?text=Open+MRs+with+Advanced+Filtering)

### Mobile Responsive Design
![Mobile View](https://via.placeholder.com/400x600/f59e0b/ffffff?text=Mobile+Responsive+Design)

## Installation

### Prerequisites
- Python 3.7 or higher
- Git
- GitLab instance (self-hosted or GitLab.com)
- GitLab Personal Access Token
- Redis (for caching functionality)

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/gitlab-mr-manager.git
   cd gitlab-mr-manager
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Setup Redis (for caching)**
   ```bash
   # Option 1: Use the automated setup script
   python setup_redis.py
   
   # Option 2: Manual Redis installation
   # macOS:
   brew install redis
   brew services start redis
   
   # Ubuntu/Debian:
   sudo apt-get update
   sudo apt-get install redis-server
   sudo systemctl start redis-server
   
   # Windows:
   # Download Redis from https://redis.io/download
   ```

5. **Configure GitLab access**
   ```bash
   export GITLAB_TOKEN="your-gitlab-personal-access-token"
   export GITLAB_URL="https://git.csez.zohocorpin.com"  # Your GitLab instance URL
   export PROJECT_ID="16895"  # Your GitLab project ID
   ```

6. **Run the application**
   ```bash
   python app.py
   ```

7. **Access the application**
   Open your browser and navigate to `http://localhost:5001`

## Redis Caching

The application uses Redis to cache frequently accessed data for improved performance. The following endpoints are cached for 24 hours:

- **`/api/labels`** - GitLab project labels
- **`/api/reviewers`** - Available reviewers from MRs
- **`/api/authors`** - MR authors

### Cache Management

The application provides several endpoints for cache management:

- **`GET /api/cache/status`** - Check cache status and TTL for each cached endpoint
- **`POST /api/cache/clear`** - Clear all cache data
- **`POST /api/cache/clear/<type>`** - Clear specific cache type (labels/reviewers/authors)

### Redis Configuration

You can configure Redis connection settings using environment variables:

```bash
export REDIS_HOST='localhost'      # Redis server host (default: localhost)
export REDIS_PORT='6379'           # Redis server port (default: 6379)
export REDIS_DB='0'                # Redis database number (default: 0)
export REDIS_PASSWORD=''           # Redis password (default: none)
```

### Cache Benefits

- **Faster Page Loads**: Cached data loads instantly instead of making API calls
- **Reduced API Calls**: Fewer requests to GitLab API, reducing rate limiting
- **Better User Experience**: Smoother filtering and dropdown population
- **Reduced Server Load**: Less processing required for frequently accessed data

## Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `GITLAB_TOKEN` | GitLab Personal Access Token | Yes | (empty) |
| `GITLAB_URL` | URL of your GitLab instance | Yes | `https://git.csez.zohocorpin.com` |
| `PROJECT_ID` | GitLab project ID | Yes | `16895` |

### GitLab Personal Access Token

To use the GitLab API features, you'll need to create a personal access token:

1. Go to your GitLab instance
2. Navigate to **User Settings** → **Access Tokens**
3. Create a new token with the following scopes:
   - `read_api`
   - `write_repository`
   - `read_repository`
   - `api`

## Usage

### Dashboard
The dashboard provides an overview of all MR statuses with real-time badge counts:
- **All Open MRs**: Total count of open merge requests
- **To Be Reviewed**: MRs with all 3 review labels
- **Reviewed MRs**: MRs with all 4 review labels
- **Good to Merge**: MRs with all 5 review labels
- **Merged MRs**: Total count of merged MRs

### Managing All Open MRs
1. Navigate to **All Open MRs** from the sidebar
2. Use filters to find specific MRs:
   - **Author**: Filter by MR author
   - **Reviewer**: Filter by assigned reviewer
   - **Labels**: Filter by GitLab labels
3. Click **+ New MR** to create a new merge request
4. View source and destination branches for each MR
5. See labels with their actual GitLab colors

### To Be Reviewed MRs
1. Navigate to **To Be Reviewed** to see MRs ready for review
2. MRs listed have ALL 3 required labels: "Self Reviewed", "Peer reviewed", "Ready to be Reviewed"
3. Click **Mark as Reviewed** to add the "Reviewed" label
4. Use filters to find specific MRs

### Reviewed MRs
1. Go to **Reviewed MRs** to see approved MRs
2. MRs listed have ALL 4 required labels (including "Reviewed")
3. Click **Mark as GTM** to add the "Good To Merge" label
4. Use filters to find specific MRs

### Good to Merge MRs
1. Visit **Good to Merge** to see MRs ready for merging
2. MRs listed have ALL 5 required labels (including "Good To Merge")
3. Click **Merge MR** to merge individual MRs
4. Use filters to find specific MRs

### Merged MRs
1. Check **Merged MRs** to see recently merged changes
2. View source and destination branches for each MR
3. Use filters to find specific MRs
4. No export or refresh buttons (simplified interface)

## API Endpoints

The application provides several REST API endpoints:

### MR Management
- `GET /api/mrs/<mr_id>/status` - Get MR status
- `POST /api/mrs/<mr_id>/mark-reviewed` - Add "Reviewed" label to MR
- `POST /api/mrs/<mr_id>/mark-gtm` - Add "Good To Merge" label to MR
- `POST /api/mrs/<mr_id>/merge` - Merge an MR

### Data Retrieval
- `GET /api/labels` - Get all available labels with colors
- `GET /api/authors` - Get all MR authors
- `GET /api/reviewers` - Get all MR reviewers
- `GET /api/stats` - Get MR statistics for badges
- `GET /api/debug/mr/<mr_id>` - Get raw GitLab data for debugging

### Filtering
- All pages support URL-based filtering with query parameters
- Filters work with AND logic for precise results
- Filter state is preserved in URL for sharing

## Development

### Project Structure
```
gitlab-mr-manager/
├── app.py                 # Main Flask application with GitLab API integration
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── debug_labels.py       # Debug script for badge counting logic
├── test_token.py         # Script to test GitLab token
├── static/               # Static assets
│   ├── css/
│   │   └── style.css     # Main stylesheet with responsive design
│   ├── js/
│   │   └── app.js        # JavaScript functionality
│   └── images/           # Image assets
└── templates/            # HTML templates
    ├── base.html         # Base template with mobile menu
    ├── home.html         # Dashboard
    ├── open_mrs.html     # All Open MRs page
    ├── to_be_reviewed_mrs.html # To Be Reviewed MRs page
    ├── reviewed_mrs.html # Reviewed MRs page
    ├── good_to_merge_mrs.html # Good to Merge MRs page
    └── merged_mrs.html   # Merged MRs page
```

### Key Features Implemented

#### Badge Counting Logic
- **To Be Reviewed**: `all(['self reviewed', 'peer reviewed', 'ready to be reviewed'])`
- **Reviewed MRs**: `all(['self reviewed', 'peer reviewed', 'ready to be reviewed', 'reviewed'])`
- **Good to Merge**: `all(['self reviewed', 'peer reviewed', 'ready to be reviewed', 'reviewed', 'good to merge'])`

#### Mobile Responsiveness
- Collapsible sidebar with hamburger menu
- Mobile backdrop for menu interaction
- Responsive grid layouts
- Touch-friendly interface

#### Filtering System
- Author filter with dropdown
- Reviewer filter with dropdown
- Label filter with color coding
- Clear filters functionality
- URL-based state management

### Testing
```bash
# Run the application in development mode
python app.py

# Test GitLab token
python test_token.py

# Debug badge counting logic
python debug_labels.py

# The application will be available at http://localhost:5001
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

If you encounter any issues or have questions:

1. Check the [Issues](https://github.com/yourusername/gitlab-mr-manager/issues) page
2. Create a new issue with detailed information
3. Contact the maintainers

## Roadmap

### Completed Features ✅
- [x] GitLab API integration with python-gitlab
- [x] Real-time badge counting with accurate logic
- [x] Advanced filtering system with AND logic
- [x] Mobile responsive design with collapsible menu
- [x] Label management (add/remove labels)
- [x] MR actions (mark as reviewed, mark as GTM, merge)
- [x] Color-coded labels with GitLab colors
- [x] Source and destination branch display
- [x] URL-based filter state management
- [x] Clear filters functionality
- [x] Pagination for large MR lists

### Upcoming Features
- [ ] Real-time notifications
- [ ] Advanced search with full-text search
- [ ] MR templates and automation
- [ ] Integration with CI/CD pipelines
- [ ] Multi-repository support
- [ ] Advanced analytics and reporting
- [ ] Slack/Discord integration
- [ ] Email notifications
- [ ] Custom workflows and approval processes
- [ ] Bulk actions for multiple MRs

## Acknowledgments

- Built with [Flask](https://flask.palletsprojects.com/)
- GitLab API integration with [python-gitlab](https://python-gitlab.readthedocs.io/)
- UI components inspired by modern design systems
- Icons from [Font Awesome](https://fontawesome.com/)
- Fonts from [Google Fonts](https://fonts.google.com/)
- Responsive design with CSS Grid and Flexbox
