#!/usr/bin/env python3

import hashlib
import sqlite3
import os # Only for Testing - Used to check and delete output DB during testing.
import re


def consistent_hash(s: str) -> str:
    m = hashlib.md5()
    m.update(s.encode('utf-8'))
    return m.hexdigest()[:8]


def consistent_transform(s: str, ignores: list = [], prefix: str = '') -> str:
    if not s:
        return s

    # Convert all ignore words to lowercase for case-insensitive comparison
    ignores = [ignore.lower() for ignore in ignores]

    words = re.split(r'(\W+)', s)
    transformed_words = []
    transformed_flag = False  # Indicates whether any part of the string was transformed

    for word in words:
        # Convert the word to lowercase for a case-insensitive comparison
        if word.lower() in ignores or word.isdigit() or not word.isalnum():
            transformed_words.append(word)
        else:
            hash_value = consistent_hash(word)
            transformed_word = hash_value
            transformed_words.append(transformed_word)
            transformed_flag = True  # At least one word has been transformed

    if transformed_flag and prefix:
        return prefix + ''.join(transformed_words)
    else:
        return ''.join(transformed_words)


def copy_table_structure(source_cursor, dest_cursor, table_name):
    source_cursor.execute(f"PRAGMA table_info({table_name});")
    columns = source_cursor.fetchall()
    columns_str = ", ".join([f'"{col[1]}" {col[2]}' for col in columns])
    create_table_query = f"CREATE TABLE {table_name} ({columns_str});"
    print(f"Executing: {create_table_query}")  # Debugging line
    try:
        dest_cursor.execute(create_table_query)
    except sqlite3.OperationalError as e:
        print(f"Failed to create table: {e}")



def obfuscate_db_data(source_db_path: str, dest_db_path: str):
    source_conn = sqlite3.connect(source_db_path)
    dest_conn = sqlite3.connect(dest_db_path)

    source_cursor = source_conn.cursor()
    dest_cursor = dest_conn.cursor()

    columns_to_rename = {
        'device': {'ignores': ['switch', 'sw', 'rtr', 'router', 'fw', 'firewall'], 'prefix': 'dev-'},
        'Vlan': {'ignores': ['routed', 'trunk'], 'prefix': 'Vlan-'},
        'vlan': {'ignores': ['routed', 'trunk'], 'prefix': 'vlan-'},
        'nameif': {
            'ignores': ['management', 'inside', 'outside', 'link', 'dmz', 'pci', 'ext', 'mgt', 'mgmt', 'int', 'vpn'],
            'prefix': 'iface-'},
        'description': {'ignores': ['sw', 'switch', 'rtr', 'router'], 'prefix': 'desc-'},
        'notes': {'ignores': ['sw', 'switch', 'rtr', 'router'], 'prefix': 'note-'},
        'desc': {'ignores': ['sw', 'switch', 'rtr', 'router'], 'prefix': 'dsc-'},
        'partition': {'ignores': [], 'prefix': 'part-'},
        'node': {'ignores': [], 'prefix': 'node-'},
        'name': {'ignores': [], 'prefix': 'name-'},
        'pool': {'ignores': ['Server', 'srvr', 'svr'], 'prefix': 'pool-'},
        'pool_name': {'ignores': [], 'prefix': 'pname-'},
        'pool_member': {'ignores': [], 'prefix': 'pmem-'},
        'vip': {'ignores': [], 'prefix': 'vip-'},
        'peer_group': {'ignores': [], 'prefix': 'AS'},  # Keeping "AS" prefix for bgp
        'vrf': {'ignores': ['internet', 'dr', 'mgmt', 'management', 'mgt', 'default', 'wan'], 'prefix': 'vrf-'},
        'serial': {'ignores': [], 'prefix': 'srl-'},
        'serialnum': {'ignores': [], 'prefix': 'snum-'},
        'networkId': {'ignores': [], 'prefix': 'netId-'},
        'address': {'ignores': [], 'prefix': 'addr-'},
        'url': {'ignores': [], 'prefix': 'url-'},
        'tags': {'ignores': [], 'prefix': 'tag-'},
        'orgId': {'ignores': [], 'prefix': 'org-'},
        'id': {'ignores': [], 'prefix': 'id-'},
    }

    source_cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = source_cursor.fetchall()

    for table in tables:
        table_name = table[0]
        if table_name == 'sqlite_sequence':
            continue

        copy_table_structure(source_cursor, dest_cursor, table_name)

        source_cursor.execute(f"SELECT * FROM {table_name};")
        rows = source_cursor.fetchall()

        for row in rows:
            source_cursor.execute(f"PRAGMA table_info({table_name});")
            columns = [col[1] for col in source_cursor.fetchall()]

            new_values = []
            for col, original_value in zip(columns, row):
                rules = columns_to_rename.get(col, {})
                if col in columns_to_rename:
                    new_value = consistent_transform(original_value, rules.get("ignores", []),
                                                     prefix=rules.get("prefix", ""))
                else:
                    new_value = original_value
                new_values.append(new_value)

            placeholders = ", ".join(["?" for _ in new_values])
            dest_cursor.execute(f"INSERT INTO {table_name} VALUES ({placeholders})", tuple(new_values))

        dest_conn.commit()

    source_conn.close()
    dest_conn.close()


if __name__ == "__main__":
    source_db_path = "/home/cory/python-projects/Net-Manage/import_data.db"  # Replace with your original SQLite db path
    dest_db_path = "/home/cory/python-projects/Net-Manage/output_data.db"  # Replace with your new SQLite db path

    if os.path.exists(dest_db_path): os.remove(dest_db_path)  # Only for testing - One-liner to delete the output db if it exists

    obfuscate_db_data(source_db_path, dest_db_path)
