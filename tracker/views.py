import os
import re
import subprocess
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
                        'queue_status': package.queue_status}

        if package.queue_status == "DONE":
            fpatches = []

            for patch in package.fedora_patches:
                fpatches.append({'name': patch.name,
                                 'hexsha': patch.hexsha,
                                 'open': False})

            package_dict['fedora_patches'] = fpatches

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
            resp = jsonify(data=data)
            resp.status_code = 400
            return resp

        package = Package(args['name'], args['summary'])

        db.session.add(package)
        db.session.commit()

        package_id = package.id

        q.enqueue_call(func=self.parse_fedora_patches,
                       args=(package_id, args['name']),
                       result_ttl=600000,
                       timeout=600000)

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
                branches.append(match.group(0))

        for branch in branches:
            # Checkout to this branch
            repo.git.checkout(branch)

            # save branch details in db
            # TODO: Parse version from spec
            release = str(branch)[7:]

            tree = repo.head.commit.tree

            for blob in tree.blobs:
                if blob.name.endswith('.patch'):
                    hexsha = blob.hexsha[:10]

                    fpatch = FedoraPatch.query.filter_by(hexsha=hexsha,
                                                         package_id=package_id).first()

                    if fpatch is None:
                        # diffstat = repo.git.apply('--stat', blob.name)
                        command = ['diffstat', os.path.join(fedora_git,
                                                            package_name,
                                                            blob.name)]

                        try:
                            diffstat = subprocess.check_output(command)
                        except Exception:
                            diffstat = ""

                        content = blob.data_stream.read().decode('utf-8', 'replace')
                        if "\n---\n" in content:
                            comments = content[:content.find("---\n")]
                        elif "diff --git" in content:
                            comments = content[:content.find("diff --git")]
                        else:
                            comments = ""

                        fpatch = FedoraPatch(package_id, blob.name, hexsha,
                                             diffstat, comments)

                        try:
                            db.session.add(fpatch)
                            db.session.commit()
                        except Exception:
                            package.queue_status = "ERROR: Couldn't add FedoraPatch"
                            db.session.add(package)
                            db.session.commit()
                            return "Error adding FedoraPatch record"

                    # Add FedoraPackage
                    fpackage = FedoraPackage(fpatch.id, release, "")

                    try:
                        db.session.add(fpackage)
                        db.session.commit()
                    except Exception:
                        package.queue_status = "ERROR: Couldn't add FedoraPackage"
                        db.session.add(package)
                        db.session.commit()
                        return "Error adding FedoraPackage record"

        package.queue_status = "DONE"
        db.session.add(package)
        db.session.commit()
        return "done"


class FedoraPatchAPI(Resource):
    def get(self, hexsha):
        fpatch = FedoraPatch.query.filter_by(hexsha=hexsha).first()

        if fpatch is None:
            abort(404)

        patch_dict = {'hexsha': hexsha, 'name': fpatch.name,
                      'diffstat': fpatch.diffstat,
                      'comments': fpatch.comments}

        fpackages = FedoraPackage.query.filter_by(patch_id=fpatch.id)
        releases = set()
        for fpackage in fpackages:
            releases.add(fpackage.release)

        patch_dict['releases'] = list(releases)

        return jsonify(patch=patch_dict)

api.add_resource(PackageAPI, '/api/packages/<int:id>')
api.add_resource(PackageListAPI, '/api/packages')
api.add_resource(FedoraPatchAPI, '/api/fedora_patches/<string:hexsha>')
