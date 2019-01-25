#! ./venv/bin/python

import json
import os

from mysql.connector import Error, MySQLConnection

from util.db_connector_config import read_db_config

cwd = os.getcwd()


def update_db():
    tables = os.listdir('{0}/save-on-data'.format(cwd))

    for table in tables:
        update_table(table)


def update_table(table_name):
    db_config = read_db_config()
    data_dir = '{0}/save-on-data'.format(cwd)

    valid_name = table_name.replace(',', '')
    files = os.listdir('{0}/{1}/'.format(data_dir, table_name))

    if not files:
        print('{0} directory is empty...'.format(table_name))
        return

    query = """
                DROP TABLE IF EXISTS `{0}`;

                CREATE TABLE {0} (brand VARCHAR(40), name VARCHAR(50),
                                  category VARCHAR (200),
                                  current_price VARCHAR(20),
                                  regular_price VARCHAR(20), size VARCHAR(20),
                                  current_unit_price VARCHAR(20),
                                  description VARCHAR(200), sku VARCHAR(20));

                INSERT INTO {0} VALUES
            """.format(valid_name)

    for file in files:

        file_name = '{0}/{1}/{2}'.format(data_dir, table_name, file)

        with open(file_name) as r:
            table_data = json.load(r)

        for pe in table_data:
            query += '("{0}", "{1}", "{2}", "{3}", "{4}", "{5}", "{6}", "{7}", "{8}"),'.format(
                pe['brand'].replace('\'', '').replace('\"', ''),
                pe['name'].replace('\'', '').replace('\"', ''),
                pe['category'].replace('\'', '').replace('\"', ''),
                pe['current_price'].replace('\'', '').replace('\"', ''),
                pe['regular_price'].replace('\'', '').replace('\"', ''),
                pe['size'].replace('\'', '').replace('\"', ''),
                pe['current_unit_price'].replace('\'', '').replace('\"', ''),
                pe['description'].replace('\'', '').replace('\"', ''),
                pe['sku'].replace('\'', '').replace('\"', ''))

    try:
        query = query[:-1]

        conn = MySQLConnection(**db_config)

        cursor = conn.cursor()
        results = cursor.execute(query, multi=True)

        i = 1

        for result in results:
            if i % 3 == 0:
                print('Inserting into saveon_db.`{0}`'.format(valid_name))
            i += 1

        conn.commit()

    except Error as error:
        print(error)

    finally:
        cursor.close()
        conn.close()


if __name__ == '__main__':
    update_db()
