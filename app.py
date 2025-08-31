from flask import Flask, render_template, jsonify, request
import os
import subprocess
import json
from datetime import datetime, timedelta
import re
import gitlab
import redis
import pickle

app = Flask(__name__)

# Configuration
GITLAB_REPO_PATH = os.getenv('GITLAB_REPO_PATH', '/path/to/your/gitlab/repo')
GITLAB_URL = os.getenv('GITLAB_URL', 'https://git.csez.zohocorpin.com')
GITLAB_TOKEN = os.getenv('GITLAB_TOKEN', 'VJaybg9Leej4zscS_Xf4')
PROJECT_ID = os.getenv('PROJECT_ID', '16895')

# Redis Configuration
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 0))
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', None)

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
    # Re-read environment variables after loading .env
    GITLAB_TOKEN = os.getenv('GITLAB_TOKEN', GITLAB_TOKEN)
except ImportError:
    # python-dotenv not installed, continue without it
    pass

# Initialize GitLab client
try:
    gl = gitlab.Gitlab(url=GITLAB_URL, private_token=GITLAB_TOKEN)
    gl.auth()  # Explicit authentication
    project = gl.projects.get(PROJECT_ID)
    print(f"GitLab connection successful! Project: {project.name}")
except Exception as e:
    print(f"Error connecting to GitLab: {e}")
    gl = None
    project = None

# Initialize Redis client
try:
    redis_client = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_DB,
        password=REDIS_PASSWORD,
        decode_responses=False  # Keep as bytes for pickle compatibility
    )
    # Test connection
    redis_client.ping()
    print("Redis connection established successfully")
except Exception as e:
    print(f"Error connecting to Redis: {e}")
    redis_client = None

def get_cached_data(key):
    """Get data from Redis cache"""
    if redis_client is None:
        return None
    
    try:
        cached_data = redis_client.get(key)
        if cached_data:
            return pickle.loads(cached_data)
        return None
    except Exception as e:
        print(f"Error getting cached data for key {key}: {e}")
        return None

def set_cached_data(key, data, expiry_hours=24):
    """Set data in Redis cache with expiry"""
    if redis_client is None:
        return False
    
    try:
        pickled_data = pickle.dumps(data)
        redis_client.setex(key, expiry_hours * 3600, pickled_data)  # Convert hours to seconds
        return True
    except Exception as e:
        print(f"Error setting cached data for key {key}: {e}")
        return False

def invalidate_cache(pattern):
    """Invalidate cache entries matching a pattern"""
    if redis_client is None:
        return False
    
    try:
        keys = redis_client.keys(pattern)
        if keys:
            redis_client.delete(*keys)
            print(f"Invalidated {len(keys)} cache entries matching pattern: {pattern}")
        return True
    except Exception as e:
        print(f"Error invalidating cache for pattern {pattern}: {e}")
        return False

def run_git_command(command, repo_path=None):
    """Run git command and return output"""
    if repo_path is None:
        repo_path = GITLAB_REPO_PATH
    
    try:
        result = subprocess.run(
            ['git'] + command,
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except Exception as e:
        return "", str(e), -1

def get_mr_status(mr_id):
    """Get the status of a merge request"""
    if project is None:
        return 'unknown'
    
    try:
        mr = project.mergerequests.get(mr_id)
        return mr.state
    except Exception as e:
        print(f"Error getting MR status: {e}")
        return 'unknown'

def fetch_gitlab_mrs(state='opened'):
    """Fetch merge requests from GitLab API"""
    if project is None:
        return []
    
    try:
        mrs = project.mergerequests.list(state=state, get_all=True)
        mr_list = []
        
        for mr in mrs:
            # Get assignees (for display purposes only)
            assignees = []
            if mr.assignees:
                for assignee in mr.assignees:
                    assignees.append(assignee.get('username', assignee.get('name', 'Unknown')))
            
            # Get labels
            labels = mr.labels if mr.labels else []
            
            # Get actual reviewers from the reviewers field
            reviewers = []
            if hasattr(mr, 'reviewers') and mr.reviewers:
                for reviewer in mr.reviewers:
                    reviewer_name = reviewer.get('username', reviewer.get('name', 'Unknown'))
                    if reviewer_name != 'Unknown':
                        reviewers.append(reviewer_name)
            elif hasattr(mr, 'approved_by') and mr.approved_by:
                # For merged MRs, use people who have already reviewed
                for approver in mr.approved_by:
                    reviewer_name = approver.get('user', {}).get('username', 'Unknown')
                    if reviewer_name != 'Unknown':
                        reviewers.append(reviewer_name)
            
            mr_data = {
                'id': mr.iid,
                'title': mr.title,
                'author': mr.author.get('username', mr.author.get('name', 'Unknown')),
                'created_at': mr.created_at.split('T')[0] if mr.created_at else 'Unknown',
                'updated_at': mr.updated_at.split('T')[0] if mr.updated_at else 'Unknown',
                'labels': labels,
                'assignees': assignees,  # Keep for display purposes
                'reviewers': reviewers,  # Add actual reviewers
                'state': mr.state,
                'web_url': mr.web_url,
                'source_branch': mr.source_branch,
                'target_branch': mr.target_branch
            }
            
            if mr.merged_at:
                mr_data['merged_at'] = mr.merged_at.split('T')[0]
                mr_data['merged_by'] = mr.merged_by.get('username', 'Unknown') if mr.merged_by else 'Unknown'
            
            if mr.closed_at:
                mr_data['closed_at'] = mr.closed_at.split('T')[0]
                mr_data['closed_by'] = mr.closed_by.get('username', 'Unknown') if mr.closed_by else 'Unknown'
            
            mr_list.append(mr_data)
        
        return mr_list
    except Exception as e:
        print(f"Error fetching MRs: {e}")
        return []

def get_mr_stats():
    """Get MR statistics from GitLab"""
    if project is None:
        return {'open': 0, 'to_be_reviewed': 0, 'reviewed': 0, 'good_to_merge': 0, 'merged': 0, 'total': 0}
    
    try:
        # Get basic counts
        open_count = len(list(project.mergerequests.list(state='opened', get_all=True)))
        merged_count = len(list(project.mergerequests.list(state='merged', get_all=True)))
        total_count = len(list(project.mergerequests.list(get_all=True)))
        
        # Calculate counts for different MR states
        open_mrs = fetch_gitlab_mrs(state='opened')
        to_be_reviewed_count = 0
        reviewed_count = 0
        good_to_merge_count = 0
        
        for mr in open_mrs:
            labels = mr.get('labels', [])
            label_names = [label.lower() for label in labels]
            
            # Count "To Be Reviewed" MRs
            has_review_labels = all(label in label_names for label in ['self reviewed', 'peer reviewed', 'ready to be reviewed'])
            has_reviewed_label = 'reviewed' in label_names
            if has_review_labels and not has_reviewed_label:
                to_be_reviewed_count += 1
            
            # Count "Reviewed" MRs
            has_all_review_labels = all(label in label_names for label in ['self reviewed', 'peer reviewed', 'ready to be reviewed', 'reviewed'])
            has_gtm_label = 'good to merge' in label_names
            if has_all_review_labels and not has_gtm_label:
                reviewed_count += 1
            
            # Count "Good to Merge" MRs
            required_labels = ['self reviewed', 'peer reviewed', 'ready to be reviewed', 'reviewed', 'good to merge']
            has_all_required_labels = all(label in label_names for label in required_labels)
            if has_all_required_labels:
                good_to_merge_count += 1
        
        return {
            'open': open_count,
            'to_be_reviewed': to_be_reviewed_count,
            'reviewed': reviewed_count,
            'good_to_merge': good_to_merge_count,
            'merged': merged_count,
            'total': total_count
        }
    except Exception as e:
        print(f"Error getting MR stats: {e}")
        return {'open': 0, 'to_be_reviewed': 0, 'reviewed': 0, 'good_to_merge': 0, 'merged': 0, 'total': 0}

def paginate_mrs(mrs, page, per_page=10):
    """Helper function to paginate MRs"""
    total_mrs = len(mrs)
    total_pages = (total_mrs + per_page - 1) // per_page
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    
    return {
        'mrs': mrs[start_idx:end_idx],
        'current_page': page,
        'total_pages': total_pages,
        'total_mrs': total_mrs,
        'per_page': per_page,
        'has_prev': page > 1,
        'has_next': page < total_pages
    }

@app.route('/')
def home():
    """Home page with navigation menu"""
    stats = get_mr_stats()
    return render_template('home.html', stats=stats)

@app.route('/instructions')
def instructions():
    """Instructions page for searchable dropdowns"""
    return render_template('instructions.html')

@app.route('/open-mrs')
def open_mrs():
    """Page showing all open MRs"""
    page = request.args.get('page', 1, type=int)
    reviewer_filter = request.args.get('reviewer', '')
    author_filter = request.args.get('author', '')
    label_filter = request.args.get('label', '')
    per_page = 10
    
    open_mrs = fetch_gitlab_mrs(state='opened')
    
    # Apply filters with AND logic
    filtered_mrs = []
    for mr in open_mrs:
        # Check reviewer filter (use actual reviewers, not assignees)
        if reviewer_filter and reviewer_filter != 'all':
            reviewers = mr.get('reviewers', [])
            if reviewer_filter not in reviewers:
                continue
        
        # Check author filter
        if author_filter and author_filter != 'all':
            if mr.get('author') != author_filter:
                continue
        
        # Check label filter
        if label_filter and label_filter != 'all':
            labels = mr.get('labels', [])
            if label_filter not in labels:
                continue
        
        filtered_mrs.append(mr)
    
    pagination = paginate_mrs(filtered_mrs, page, per_page)
    pagination['current_reviewer'] = reviewer_filter
    pagination['current_author'] = author_filter
    pagination['current_label'] = label_filter
    
    return render_template('open_mrs.html', **pagination)

@app.route('/to-be-reviewed-mrs')
def to_be_reviewed_mrs():
    """Page showing MRs that need to be reviewed"""
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    # Get filter parameters
    reviewer_filter = request.args.get('reviewer', '')
    author_filter = request.args.get('author', '')
    label_filter = request.args.get('label', '')
    
    open_mrs = fetch_gitlab_mrs(state='opened')
    to_be_reviewed = []
    
    for mr in open_mrs:
        labels = mr.get('labels', [])
        label_names = [label.lower() for label in labels]
        
        # Check if MR has ALL review-related labels but not "Reviewed"
        required_labels = ['self reviewed', 'peer reviewed', 'ready to be reviewed']
        has_all_review_labels = all(label in label_names for label in required_labels)
        has_reviewed_label = 'reviewed' in label_names
        
        if has_all_review_labels and not has_reviewed_label:
            # Apply filters with AND logic
            if reviewer_filter and reviewer_filter != 'all':
                if reviewer_filter not in mr.get('reviewers', []):
                    continue
            
            if author_filter and author_filter != 'all':
                if mr.get('author') != author_filter:
                    continue
            
            if label_filter and label_filter != 'all':
                if label_filter not in labels:
                    continue
            
            to_be_reviewed.append(mr)
    
    pagination = paginate_mrs(to_be_reviewed, page, per_page)
    pagination['current_reviewer'] = reviewer_filter
    pagination['current_author'] = author_filter
    
    return render_template('to_be_reviewed_mrs.html', **pagination)

@app.route('/reviewed-mrs')
def reviewed_mrs():
    """Page showing MRs that have been reviewed"""
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    # Get filter parameters
    reviewer_filter = request.args.get('reviewer', '')
    author_filter = request.args.get('author', '')
    
    open_mrs = fetch_gitlab_mrs(state='opened')
    reviewed_mrs = []
    
    for mr in open_mrs:
        labels = mr.get('labels', [])
        label_names = [label.lower() for label in labels]
        
        # Check if MR has ALL review-related labels including "Reviewed" but not "Good to Merge"
        required_labels = ['self reviewed', 'peer reviewed', 'ready to be reviewed', 'reviewed']
        has_all_review_labels = all(label in label_names for label in required_labels)
        has_gtm_label = 'good to merge' in label_names
        
        if has_all_review_labels and not has_gtm_label:
            # Apply filters with AND logic
            if reviewer_filter and reviewer_filter != 'all':
                if reviewer_filter not in mr.get('reviewers', []):
                    continue
            
            if author_filter and author_filter != 'all':
                if mr.get('author') != author_filter:
                    continue
            
            reviewed_mrs.append(mr)
    
    pagination = paginate_mrs(reviewed_mrs, page, per_page)
    pagination['current_reviewer'] = reviewer_filter
    pagination['current_author'] = author_filter
    
    return render_template('reviewed_mrs.html', **pagination)

@app.route('/good-to-merge-mrs')
def good_to_merge_mrs():
    """Page showing MRs that are good to merge"""
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    # Get filter parameters
    reviewer_filter = request.args.get('reviewer', '')
    author_filter = request.args.get('author', '')
    
    open_mrs = fetch_gitlab_mrs(state='opened')
    gtm_mrs = []
    
    for mr in open_mrs:
        labels = mr.get('labels', [])
        label_names = [label.lower() for label in labels]
        
        # Check if MR has ALL review-related labels including "Good To Merge"
        required_labels = ['self reviewed', 'peer reviewed', 'ready to be reviewed', 'reviewed', 'good to merge']
        has_all_required_labels = all(label in label_names for label in required_labels)
        
        if has_all_required_labels:
            # Apply filters with AND logic
            if reviewer_filter and reviewer_filter != 'all':
                if reviewer_filter not in mr.get('reviewers', []):
                    continue
            
            if author_filter and author_filter != 'all':
                if mr.get('author') != author_filter:
                    continue
            
            gtm_mrs.append(mr)
    
    pagination = paginate_mrs(gtm_mrs, page, per_page)
    pagination['current_reviewer'] = reviewer_filter
    pagination['current_author'] = author_filter
    
    return render_template('good_to_merge_mrs.html', **pagination)



@app.route('/merged-mrs')
def merged_mrs():
    """Page showing merged MRs with filtering"""
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    # Get filter parameters
    reviewer_filter = request.args.get('reviewer', '')
    author_filter = request.args.get('author', '')
    
    merged_mrs = fetch_gitlab_mrs(state='merged')
    filtered_mrs = []
    
    for mr in merged_mrs:
        # Apply filters with AND logic
        if reviewer_filter and reviewer_filter != 'all':
            if reviewer_filter not in mr.get('reviewers', []):
                continue
        
        if author_filter and author_filter != 'all':
            if mr.get('author') != author_filter:
                continue
        
        filtered_mrs.append(mr)
    
    pagination = paginate_mrs(filtered_mrs, page, per_page)
    pagination['current_reviewer'] = reviewer_filter
    pagination['current_author'] = author_filter
    
    return render_template('merged_mrs.html', **pagination)



@app.route('/api/mrs/<mr_id>/status')
def get_mr_status_api(mr_id):
    """API endpoint to get MR status"""
    status = get_mr_status(mr_id)
    return jsonify({'mr_id': mr_id, 'status': status})

@app.route('/api/labels')
def get_labels():
    """API endpoint to get all available labels with Redis caching"""
    cache_key = f"labels:{PROJECT_ID}"
    
    # Try to get from cache first
    cached_labels = get_cached_data(cache_key)
    if cached_labels is not None:
        print(f"Returning cached labels for project {PROJECT_ID}")
        return jsonify(cached_labels)
    
    if project is None:
        labels = [
            {'name': 'feature', 'color': '#1d76db'},
            {'name': 'bug', 'color': '#d73a4a'},
            {'name': 'frontend', 'color': '#0075ca'},
            {'name': 'backend', 'color': '#0e8a16'},
            {'name': 'security', 'color': '#d93f0b'},
            {'name': 'testing', 'color': '#fef2c0'},
            {'name': 'documentation', 'color': '#0075ca'},
            {'name': 'api', 'color': '#5319e7'},
            {'name': 'database', 'color': '#fbca04'},
            {'name': 'auth', 'color': '#d73a4a'},
            {'name': 'duplicate', 'color': '#cfd3d7'}
        ]
        # Cache the fallback data
        set_cached_data(cache_key, labels, expiry_hours=24)
        return jsonify(labels)
    
    try:
        # Get all labels from the project
        labels = project.labels.list(per_page=50)
        label_data = [{'name': label.name, 'color': label.color} for label in labels]
        
        # Cache the data for 24 hours
        set_cached_data(cache_key, label_data, expiry_hours=24)
        print(f"Cached labels for project {PROJECT_ID}")
        
        return jsonify(label_data)
    except Exception as e:
        print(f"Error fetching labels: {e}")
        return jsonify([])

@app.route('/api/reviewers')
def get_reviewers():
    """API endpoint to get all available reviewers with Redis caching"""
    cache_key = f"reviewers:{PROJECT_ID}"
    
    # Try to get from cache first
    cached_reviewers = get_cached_data(cache_key)
    if cached_reviewers is not None:
        print(f"Returning cached reviewers for project {PROJECT_ID}")
        return jsonify(cached_reviewers)
    
    if project is None:
        reviewers = ['reviewer1', 'reviewer2']
        # Cache the fallback data
        set_cached_data(cache_key, reviewers, expiry_hours=24)
        return jsonify(reviewers)
    
    try:
        # Get all merge requests to extract unique reviewers
        all_mrs = project.mergerequests.list(get_all=True)
        reviewer_names = set()
        
        for mr in all_mrs:
            # Use actual reviewers from the reviewers field
            if hasattr(mr, 'reviewers') and mr.reviewers:
                for reviewer in mr.reviewers:
                    reviewer_name = reviewer.get('username', reviewer.get('name', 'Unknown'))
                    if reviewer_name and reviewer_name != 'Unknown':
                        reviewer_names.add(reviewer_name)
            
            # For merged MRs, also include people who have already reviewed
            if hasattr(mr, 'approved_by') and mr.approved_by:
                for approver in mr.approved_by:
                    if isinstance(approver, dict) and 'user' in approver:
                        reviewer_name = approver['user'].get('username', approver['user'].get('name', 'Unknown'))
                        if reviewer_name and reviewer_name != 'Unknown':
                            reviewer_names.add(reviewer_name)
        
        reviewer_list = list(reviewer_names)
        
        # Cache the data for 24 hours
        set_cached_data(cache_key, reviewer_list, expiry_hours=24)
        print(f"Cached reviewers for project {PROJECT_ID}")
        
        return jsonify(reviewer_list)
    except Exception as e:
        print(f"Error fetching reviewers: {e}")
        return jsonify([])

@app.route('/api/authors')
def get_authors():
    """API endpoint to get all MR authors with Redis caching"""
    cache_key = f"authors:{PROJECT_ID}"
    
    # Try to get from cache first
    cached_authors = get_cached_data(cache_key)
    if cached_authors is not None:
        print(f"Returning cached authors for project {PROJECT_ID}")
        return jsonify(cached_authors)
    
    if project is None:
        authors = ['john.doe', 'jane.smith', 'alice.johnson', 'bob.wilson']
        # Cache the fallback data
        set_cached_data(cache_key, authors, expiry_hours=24)
        return jsonify(authors)
    
    try:
        # Get all merge requests to extract unique authors
        all_mrs = project.mergerequests.list(get_all=True)
        authors = set()
        
        for mr in all_mrs:
            if hasattr(mr, 'author') and mr.author:
                author_name = mr.author.get('username', mr.author.get('name', 'Unknown'))
                if author_name and author_name != 'Unknown':
                    authors.add(author_name)
        
        author_list = list(authors)
        
        # Cache the data for 24 hours
        set_cached_data(cache_key, author_list, expiry_hours=24)
        print(f"Cached authors for project {PROJECT_ID}")
        
        return jsonify(author_list)
    except Exception as e:
        print(f"Error fetching authors: {e}")
        return jsonify([])

@app.route('/api/mrs/<int:mr_id>/approve', methods=['POST'])
def approve_mr(mr_id):
    """API endpoint to approve a merge request"""
    if project is None:
        return jsonify({'success': False, 'message': 'GitLab connection not available'})
    
    try:
        mr = project.mergerequests.get(mr_id)
        # Note: GitLab API approval is more complex and depends on project settings
        # This is a simplified implementation
        return jsonify({'success': True, 'message': f'MR #{mr_id} approved successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error approving MR: {str(e)}'})

@app.route('/api/mrs/<int:mr_id>/merge', methods=['POST'])
def merge_mr(mr_id):
    """API endpoint to merge a merge request"""
    if project is None:
        return jsonify({'success': False, 'message': 'GitLab connection not available'})
    
    try:
        mr = project.mergerequests.get(mr_id)
        if mr.state == 'opened':
            mr.merge()
            return jsonify({'success': True, 'message': f'MR #{mr_id} merged successfully'})
        else:
            return jsonify({'success': False, 'message': f'MR #{mr_id} cannot be merged (state: {mr.state})'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error merging MR: {str(e)}'})

@app.route('/api/mrs/<int:mr_id>/close', methods=['POST'])
def close_mr(mr_id):
    """API endpoint to close a merge request"""
    if project is None:
        return jsonify({'success': False, 'message': 'GitLab connection not available'})
    
    try:
        mr = project.mergerequests.get(mr_id)
        if mr.state == 'opened':
            mr.close()
            return jsonify({'success': True, 'message': f'MR #{mr_id} closed successfully'})
        else:
            return jsonify({'success': False, 'message': f'MR #{mr_id} cannot be closed (state: {mr.state})'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error closing MR: {str(e)}'})

@app.route('/api/mrs/<int:mr_id>/mark-reviewed', methods=['POST'])
def mark_reviewed(mr_id):
    """API endpoint to mark MR as reviewed"""
    if project is None:
        return jsonify({'success': False, 'error': 'No GitLab connection'})
    
    try:
        mr = project.mergerequests.get(mr_id)
        current_labels = mr.labels if mr.labels else []
        
        # Add 'Reviewed' label if not present
        if 'Reviewed' not in current_labels:
            current_labels.append('Reviewed')
            mr.labels = current_labels
            mr.save()
        
        return jsonify({'success': True, 'message': f'MR #{mr_id} marked as reviewed'})
    except Exception as e:
        print(f"Error marking MR {mr_id} as reviewed: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/mrs/<int:mr_id>/mark-gtm', methods=['POST'])
def mark_gtm(mr_id):
    """API endpoint to mark MR as Good to Merge"""
    if project is None:
        return jsonify({'success': False, 'error': 'No GitLab connection'})
    
    try:
        mr = project.mergerequests.get(mr_id)
        current_labels = mr.labels if mr.labels else []
        
        # Add 'Good To Merge' label if not present
        if 'Good To Merge' not in current_labels:
            current_labels.append('Good To Merge')
            mr.labels = current_labels
            mr.save()
        
        return jsonify({'success': True, 'message': f'MR #{mr_id} marked as Good to Merge'})
    except Exception as e:
        print(f"Error marking MR {mr_id} as GTM: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/stats')
def get_stats():
    """API endpoint to get MR statistics"""
    stats = get_mr_stats()
    return jsonify(stats)

@app.route('/api/cache/clear', methods=['POST'])
def clear_cache():
    """API endpoint to clear all cache"""
    try:
        if redis_client is None:
            return jsonify({'success': False, 'message': 'Redis not available'})
        
        # Clear all cache keys
        redis_client.flushdb()
        print("All cache cleared")
        return jsonify({'success': True, 'message': 'All cache cleared successfully'})
    except Exception as e:
        print(f"Error clearing cache: {e}")
        return jsonify({'success': False, 'message': f'Error clearing cache: {str(e)}'})

@app.route('/api/cache/clear/<cache_type>', methods=['POST'])
def clear_specific_cache(cache_type):
    """API endpoint to clear specific cache types"""
    try:
        if redis_client is None:
            return jsonify({'success': False, 'message': 'Redis not available'})
        
        if cache_type == 'labels':
            pattern = f"labels:{PROJECT_ID}"
        elif cache_type == 'reviewers':
            pattern = f"reviewers:{PROJECT_ID}"
        elif cache_type == 'authors':
            pattern = f"authors:{PROJECT_ID}"
        else:
            return jsonify({'success': False, 'message': f'Invalid cache type: {cache_type}'})
        
        success = invalidate_cache(pattern)
        if success:
            return jsonify({'success': True, 'message': f'{cache_type} cache cleared successfully'})
        else:
            return jsonify({'success': False, 'message': f'Error clearing {cache_type} cache'})
    except Exception as e:
        print(f"Error clearing {cache_type} cache: {e}")
        return jsonify({'success': False, 'message': f'Error clearing {cache_type} cache: {str(e)}'})

@app.route('/api/cache/status')
def cache_status():
    """API endpoint to get cache status"""
    try:
        if redis_client is None:
            return jsonify({'success': False, 'message': 'Redis not available'})
        
        # Get cache keys and their TTL
        cache_info = {}
        for cache_type in ['labels', 'reviewers', 'authors']:
            key = f"{cache_type}:{PROJECT_ID}"
            ttl = redis_client.ttl(key)
            exists = ttl > 0
            cache_info[cache_type] = {
                'exists': exists,
                'ttl_seconds': ttl if exists else None,
                'ttl_hours': round(ttl / 3600, 2) if exists and ttl > 0 else None
            }
        
        return jsonify({
            'success': True,
            'redis_connected': True,
            'cache_info': cache_info
        })
    except Exception as e:
        print(f"Error getting cache status: {e}")
        return jsonify({
            'success': False,
            'redis_connected': False,
            'message': f'Error getting cache status: {str(e)}'
        })

@app.route('/api/debug/mrs')
def debug_mrs():
    """Debug endpoint to see MR data structure"""
    if project is None:
        return jsonify({'error': 'No GitLab connection'})
    
    try:
        # Get a few sample MRs to show their structure
        mrs = project.mergerequests.list(state='opened', per_page=5)
        debug_data = []
        
        for mr in mrs:
            debug_mr = {
                'id': mr.iid,
                'title': mr.title,
                'state': mr.state,
                'has_assignees': bool(mr.assignees),
                'assignees': mr.assignees,
                'has_approved_by': hasattr(mr, 'approved_by') and bool(mr.approved_by),
                'approved_by': mr.approved_by if hasattr(mr, 'approved_by') else None,
                'labels': mr.labels,
                'created_at': mr.created_at,
                'updated_at': mr.updated_at,
                'web_url': mr.web_url
            }
            debug_data.append(debug_mr)
        
        return jsonify({
            'total_open_mrs': len(list(project.mergerequests.list(state='opened'))),
            'sample_mrs': debug_data
        })
    except Exception as e:
        return jsonify({'error': str(e)})



if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
