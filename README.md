# P(ost)G(res) Migrate

## Installation

`pip install git+git://github.com/wenrixai/pgmigrate.git` from a private repository

## Migration Files

The migration files are used to determine the schema of the DB
The `verify` and `undo` section are optional.

```yaml
version: 1
name: Add filter column
description: DEV-193223
migration:
  - ALTER TABLE bookings ADD COLUMN gds TEXT DEFAULT 'sabre';
verify:
  - SELECT * FROM bookings WHERE gds <> 'sabre';
undo:
  - ALTER TABLE bookings DROP COLUMN gds;

```

## Usage

| command 	  | description 	                                                                                                                                                                                               |
|------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `migrate`	 | Migrate the current DB to the defined schema           	                                                                                                                                                    |
| `clean` 	  | Clean is a great help in development and test. It will effectively give you a fresh start, by wiping your configured schemas completely clean. All objects (tables, views, procedures, …) will be dropped.	 |
| `info`	    | Get the current version of the Database and compare to the file path	                                                                                                                                       |
| `undo`     | Undo to a specific version or until a sepecific version	                                                                                                                                                                                    |


### Flags and Parameters

* `--connection-string` - The connection string 
* `--path` - The path for the migration files
* `--dry-run` - Dry run mode, do not run the migrations (run them without commit)
* `--verbose` - More logging

## How does it work?

The uses a table called `schema_history`. If the table does not exists it will create it upon the first migration.
The table contains all migrations that were executed.

