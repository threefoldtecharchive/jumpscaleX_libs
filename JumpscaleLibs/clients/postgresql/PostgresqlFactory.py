from Jumpscale import j

try:
    import psycopg2
except:
    j.builders.system.package.install(["libpq-dev", "python3-dev"])
    j.builders.runtimes.python3.pip_package_install("psycopg2", reset=True)
    import psycopg2

from .PostgresqlClient import PostgresClient

JSConfigs = j.baseclasses.object_config_collection


class PostgresqlFactory(JSConfigs):
    """
    """

    __jslocation__ = "j.clients.postgres"
    _CHILDCLASS = PostgresClient

    def install(self):
        """
        kosmos 'j.clients.postgres.install()'
        :return:
        """
        j.builders.db.psql.install()

    def start(self):
        j.builders.db.psql.start()

    def stop(self):
        j.builders.db.psql.stop()

    def db_client_get(self, name="test", dbname="main"):
        """
        returns database client

        cl = j.clients.postgres.db_client_get()

        login: root
        passwd: rooter
        dbname: main if not specified
        :return:
        """
        try:
            cl = self.get(name=name, ipaddr="localhost", port=5432, login="root", passwd_="admin", dbname=dbname)
            r = cl.execute("SELECT version();")
            return cl
        except BaseException as e:
            pass

        # means could not return, lets now create the db
        try:

            j.sal.process.execute(
                """psql -h localhost -U postgres \
                --command='DROP ROLE IF EXISTS root; CREATE ROLE root superuser; ALTER ROLE root WITH LOGIN;' """
            )

            j.sal.process.execute(
                """psql -h localhost -U postgres \
                --command='DROP ROLE IF EXISTS odoouser; CREATE ROLE odoouser superuser ; ALTER ROLE odoouser WITH LOGIN; ALTER USER odoouser WITH SUPERUSER;' """
            )
            j.sal.process.execute("createdb -O odoouser %s" % dbname)
            j.sal.process.execute(
                """psql -h localhost -U postgres \
                --command='CREATE TABLE initialize_table (available BOOLEAN NOT NULL );' """
            )
        except:
            pass

        cl = self.get(name=name, ipaddr="localhost", port=5432, login="root", passwd_="rooter", dbname=dbname)
        cl.save()
        return cl

    def test(self):
        """
        kosmos 'j.clients.postgres.test()'
        """
        self.install()
        self.start()

        cl = self.db_client_get()

        base, session = cl.sqlalchemy_client_get()
        j.shell()
        session.add(base.classes.address(email_address="foo@bar.com", user=(base.classes.user(name="foo"))))
        session.commit()

        # self.stop()
        print("TEST OK")
