from flask import Blueprint, request, jsonify
from .schema import schema

graphql_bp = Blueprint('graphql_bp', __name__)

@graphql_bp.route('/graphql', methods=['GET', 'POST'])
def graphql_server():
    if request.method == 'GET':
        return render_template('graphiql.html')
    elif request.method == 'POST':
        data = request.get_json()
        result = schema.execute(
            data.get("query"), 
            variables=data.get("variables"),
            context_value=request
        )
        response = jsonify(result.data)
        response.status_code = (
            400 if result.errors else 200
        )
        return response