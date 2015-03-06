from tracker import db


class Package(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(40))
    summary = db.Column(db.Text)
    fedora_task_id = db.Column(db.Integer)
    fedora_packages = db.relationship('FedoraPackage', backref='package',
                                      lazy='dynamic')

    def __init__(self, name, summary):
        self.name = name
        self.summary = summary

    def __repr__(self):
        return '<Package %r>' % self.name


class FedoraPackage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    package_id = db.Column(db.Integer, db.ForeignKey('package.id'))
    release = db.Column(db.String(5))
    version = db.Column(db.String(10))
    patches = db.relationship('FedoraPatch', backref='fedora_package',
                              lazy='dynamic')

    def __init__(self, package_id, release, version):
        self.package_id = package_id
        self.release = release
        self.version = version

    def __repr__(self):
        return '<FedoraPackage %r %r:%r>' % (self.package.name, self.release,
                                             self.version)


class FedoraPatch(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fedora_package_id = db.Column(db.Integer,
                                  db.ForeignKey('fedora_package.id'))
    name = db.Column(db.String(50))
    content = db.Column(db.Text)

    def __init__(self, fedora_package_id, name, content):
        self.fedora_package_id = fedora_package_id
        self.name = name
        self.content = content

    def __repr__(self):
        return '<Fedora Patch %r>' % self.name
