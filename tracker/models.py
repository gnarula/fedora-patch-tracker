from tracker import db


class Package(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(40))
    summary = db.Column(db.Text)
    fedora_task_id = db.Column(db.Integer)
    fedora_patches = db.relationship('FedoraPatch', backref='package',
                                     lazy='dynamic')
    queue_status = db.Column(db.String(50))  # DONE, QUEUED, ERROR

    def __init__(self, name, summary):
        self.name = name
        self.summary = summary
        self.queue_status = "QUEUED"

    def __repr__(self):
        return '<Package %r>' % self.name


class FedoraPackage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    release = db.Column(db.String(5))
    version = db.Column(db.String(10))
    patch_id = db.Column(db.Integer, db.ForeignKey('fedora_patch.id'))

    def __init__(self, patch_id, release, version):
        self.patch_id = patch_id
        self.release = release
        self.version = version

    def __repr__(self):
        return '<FedoraPackage %r:%r>' % (self.release, self.version)


class FedoraPatch(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    package_id = db.Column(db.Integer, db.ForeignKey('package.id'))
    name = db.Column(db.String(50))
    hexsha = db.Column(db.String(10), index=True)
    diffstat = db.Column(db.Text)
    comments = db.Column(db.Text)
    fedora_packages = db.relationship('FedoraPackage',
                                      backref='fedora_patch',
                                      lazy='dynamic')

    def __init__(self, package_id, name, hexsha, diffstat, comments):
        self.package_id = package_id
        self.name = name
        self.hexsha = hexsha
        self.diffstat = diffstat
        self.comments = comments

    def __repr__(self):
        return '<Fedora Patch %r-%r>' % (self.name, self.hexsha)
