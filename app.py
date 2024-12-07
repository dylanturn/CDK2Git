from flask import Flask, request, Response
import os
import logging
from git_handler import GitHandler

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

app = Flask(__name__)
git_handler = GitHandler()

@app.errorhandler(Exception)
def handle_error(error):
    logger.error(f"An error occurred: {str(error)}", exc_info=True)
    return f"Internal server error: {str(error)}", 500

@app.route('/<project>/info/refs')
def info_refs(project):
    """Handle Git info/refs request"""
    service = request.args.get('service')
    if service != 'git-upload-pack':
        return 'Service not available', 400

    logger.info(f"Received info/refs request for service: {service} and project: {project}")
    
    # Set the project path in the git handler
    git_handler.set_project_path(project)
    
    # Get Git references
    refs_data = git_handler.get_refs()
    
    return Response(
        refs_data,
        mimetype=f'application/x-{service}-advertisement'
    )

@app.route('/<project>/git-upload-pack', methods=['POST'])
def git_upload_pack(project):
    """Handle Git upload-pack request"""
    if request.content_type != 'application/x-git-upload-pack-request':
        return 'Invalid content type', 400

    logger.info(f"Received git-upload-pack request for project: {project} with Content-Type: {request.content_type}")
    
    try:
        # Set the project path in the git handler
        git_handler.set_project_path(project)
        
        # Generate pack data
        pack_data = git_handler.generate_pack(request.data)
        if not pack_data:
            return 'Failed to generate pack data', 500
        
        return Response(
            pack_data,
            mimetype='application/x-git-upload-pack-result'
        )
        
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}", exc_info=True)
        return 'Internal server error', 500

if __name__ == '__main__':
    logger.info("Starting CDK2Git server...")
    app.run(debug=True, port=5005)
