import os
import re
from flask import jsonify, render_template
from flask.ext.restful import abort, Api, Resource, reqparse
from tracker import app, db, q
from tracker.models import Package, FedoraPackage, FedoraPatch
from git import Repo


api = Api(app)


@app.route('/')
def index():
    return render_template('layout.html')


class PackageAPI(Resource):
    def get(self, id):
        package = Package.query.get(id)
        if package is None:
            abort(404)

        package_dict = {'id': package.id, 'name': package.name,
                        'summary': package.summary,
                        'fedora_task_id': package.fedora_task_id,
                        'queue_status': package.queue_status}

        if package.queue_status == "DONE":
            fpackage = {}

            for fedora_package in package.fedora_packages:
                patches = fedora_package.patches
                fpackage[fedora_package.release] = {}
                for patch in patches:
                    fpackage[fedora_package.release][patch.name] = patch.content

            package_dict['fedora_packages'] = fpackage

        return jsonify(package=package_dict)


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
        if Package.query.filter_by(name=args['name']).first():
            data = {'id': None,
                    'msg': 'Package with that name already exists'}
            return jsonify(data=data), 400

        package = Package(args['name'], args['summary'])

        db.session.add(package)
        db.session.commit()

        package_id = package.id

        job = q.enqueue_call(func=self.parse_fedora_patches,
                             args=(package_id, args['name']),
                             result_ttl=600000)

        data = {'id': package.id, 'msg': 'Package Added'}
        return jsonify(data=data)

    def parse_fedora_patches(self, package_id, package_name):

        package = Package.query.get(package_id)
        repo_url = 'git://pkgs.fedoraproject.org/%s.git' % package_name

        # Create fedora_git dir if it doesn't exist
        fedora_git = os.path.join(app.config['BASEDIR'], 'tracker',
                                  'fedora_git')

        if not os.path.exists(fedora_git):
            os.makedirs(fedora_git)

        try:
            repo = Repo.clone_from(repo_url, os.path.join(fedora_git,
                                                          package_name))
        except:
            package.queue_status = "ERROR: Couldn't clone git repository"
            db.session.add(package)
            db.session.commit()
            return "Couldn't clone git repository"

        branches = []
        for ref in repo.remotes.origin.refs:
            match = re.match(r'origin\/(f[0-9]{2})', str(ref))

            if match:
                branches.append(ref)

        for branch in branches:
            # Checkout to this branch
            repo.head.reference = branch

            # save branch details in db
            # TODO: Parse version from spec
            fedora_package = FedoraPackage(package_id,
                                           os.path.basename(str(branch)), '')

            try:
                db.session.add(fedora_package)
                db.session.commit()
                fedora_package_id = fedora_package.id
            except:
                return "Error adding FedoraPackage record"

            tree = repo.head.commit.tree

            for blob in tree.blobs:
                if blob.name.endswith('.patch'):
                    # read the patch
                    fpatch = FedoraPatch(fedora_package_id,
                                         blob.name, blob.data_stream.read())

                    try:
                        db.session.add(fpatch)
                        db.session.commit()
                    except Exception:
                        return "Error adding FedoraPatch record"

        package.queue_status = "DONE"
        db.session.add(package)
        db.session.commit()
        return "done"

api.add_resource(PackageAPI, '/api/packages/<int:id>')
api.add_resource(PackageListAPI, '/api/packages')
