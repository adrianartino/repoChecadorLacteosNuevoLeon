try:
    import pymysql

    pymysql.install_as_MySQLdb()
except ImportError:
    # Si PyMySQL no esta instalado, el proyecto puede seguir usando mysqlclient.
    pass
