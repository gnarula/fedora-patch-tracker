from flask import jsonify
from flask.ext.restful import abort, Api, Resource, reqparse
from tracker import app, db
from tracker.models import Package

api = Api(app)


class PackageAPI(Resource):
    def get(self, id):
        package = Package.query.get(id)
        if package is None:
            abort(404)

        package = {'id': package.id, 'name': package.name,
                   'summary': package.summary,
                   'fedora_task_id': package.fedora_task_id}

        return jsonify(package=package)


class PackageListAPI(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('name', type=str, required=True,
                                   help='No package name provided',
                                   location='json')
        self.reqparse.add_argument('summary', type=str, default='',
                                   location='json')
        super(PackageListAPI, self).__init__()

    def get(self):
        packages = Package.query.all()

        output = []
        for package in packages:
            row = {}

            for field in Package.__table__.c:
                row[field.name] = getattr(package, field.name, None)

            output.append(row)

        return jsonify(packages=output)

    def post(self):
        args = self.reqparse.parse_args()
        package = Package(args['name'], args['summary'])

        db.session.add(package)
        db.session.commit()

        return package.id


api.add_resource(PackageAPI, '/api/packages/<int:id>')
api.add_resource(PackageListAPI, '/api/packages')
